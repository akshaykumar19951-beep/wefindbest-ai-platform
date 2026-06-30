from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import json

from app.core.deps import get_db
from app.db.models.user import User
from app.db.models.chat_message import ChatMessage
from app.db.models.usage import Usage
from app.core.api_security import get_current_user
from app.services.ai_service import ai_service
from app.services.billing_service import enforce_billing_limits, record_usage
from app.schemas.ai import ChatStreamRequest
from app.services.observability_service import record_provider_metric, record_user_activity
import time

router = APIRouter()


@router.post("/chat/stream")
def stream_chat(
    request: ChatStreamRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    db_user = db.query(User).filter(User.id == user.id).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    enforce_billing_limits(db, db_user)

    if request.input:
        user_input = request.input
    elif request.messages:
        user_input = request.messages[-1].content
    else:
        user_input = ""

    if not user_input:
        raise HTTPException(status_code=400, detail="Input is required")

    try:
        db.add(ChatMessage(
            user_id=db_user.id,
            role="user",
            content=user_input
        ))
        db.commit()
    except Exception:
        db.rollback()
        raise

    # load memory
    history_records = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == db_user.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(10)
        .all()
    )

    history = [
        {"role": m.role, "content": m.content}
        for m in reversed(history_records)
    ]

    # -------------------------
    # STREAM GENERATOR
    # -------------------------
    def generate():

        full_response = ""
        start_time = time.time()

        final_meta = {}
        for chunk in ai_service.stream(
            user_input,
            history,
            model=request.model,
            provider=request.provider,
            temperature=request.temperature,
            fallback_models=request.fallback_models,
        ):
            if isinstance(chunk, dict):
                final_meta = chunk
                continue

            full_response += chunk

            yield f"data: {json.dumps({'token': chunk})}\n\n"

        latency_ms = int((time.time() - start_time) * 1000)
        tokens = final_meta.get("total_tokens", len(full_response.split()))
        cost = final_meta.get("estimated_cost_usd", 0.0)

        try:
            db.add(ChatMessage(
                user_id=db_user.id,
                role="assistant",
                content=full_response
            ))

            db.add(
                Usage(
                    user_id=db_user.id,
                    endpoint="/v1/chat/stream",
                    model=final_meta.get("model", request.model or "mock"),
                    prompt=user_input,
                    response=full_response,
                    latency_ms=latency_ms,
                    tokens=tokens,
                    estimated_cost_usd=cost,
                )
            )
            record_provider_metric(
                db,
                user_id=db_user.id,
                provider=final_meta.get("provider", request.provider or "mock"),
                model=final_meta.get("model", request.model or "mock"),
                latency_ms=final_meta.get("provider_latency_ms", latency_ms),
                prompt_tokens=final_meta.get("prompt_tokens", 0),
                completion_tokens=final_meta.get("completion_tokens", 0),
                total_tokens=tokens,
                cost_usd=cost,
                success=True,
            )
            record_user_activity(
                db,
                user_id=db_user.id,
                action="chat.stream.completed",
                resource_type="model",
                resource_id=final_meta.get("model", request.model or "mock"),
                details=f"{final_meta.get('provider', request.provider or 'mock')}:{tokens} tokens",
            )
            db_user.used += 1
            record_usage(db, db_user, tokens, cost)
            db.commit()
        except Exception:
            db.rollback()
            raise

        yield f"data: {json.dumps({'done': True, **final_meta})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )
