from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import time

from app.core.deps import get_db
from app.db.models.user import User
from app.db.models.chat_message import ChatMessage
from app.db.models.usage import Usage
from app.schemas.ai import ChatRequest, ChatResponse
from app.services.ai_service import ai_service
from app.services.billing_service import enforce_billing_limits, record_usage
from app.core.api_security import get_current_user
from app.services.observability_service import (
    create_alert,
    record_error_event,
    record_provider_metric,
    record_user_activity,
)

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # -------------------------
    # Validate user
    # -------------------------
    db_user = db.query(User).filter(User.id == user.id).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    enforce_billing_limits(db, db_user)

    user_input = request.input

    try:
        db.add(
            ChatMessage(
                user_id=db_user.id,
                role="user",
                content=user_input,
            )
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

    # -------------------------
    # Load memory (optional)
    # -------------------------
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
    # AI CALL
    # -------------------------
    start_time = time.time()

    try:
        gateway_response = ai_service.ask(
            user_input,
            history=history,
            model=request.model,
            provider=request.provider,
            temperature=request.temperature,
            fallback_models=request.fallback_models,
        )
    except Exception as e:
        record_error_event(
            db,
            user_id=db_user.id,
            method="POST",
            path="/v1/chat",
            status_code=500,
            error_type=type(e).__name__,
            message=str(e),
        )
        create_alert(
            db,
            severity="warning",
            title="AI provider request failed",
            message=str(e),
            source="ai-gateway",
        )
        db.commit()
        raise HTTPException(
            status_code=500,
            detail=f"AI service failed: {str(e)}"
        )

    latency_ms = int((time.time() - start_time) * 1000)

    response_text = gateway_response.text
    tokens = gateway_response.total_tokens
    cost = gateway_response.estimated_cost_usd

    try:
        db.add(
            ChatMessage(
                user_id=db_user.id,
                role="assistant",
                content=response_text,
            )
        )

        db.add(
            Usage(
                user_id=db_user.id,
                endpoint="/v1/chat",
                model=gateway_response.model,
                prompt=user_input,
                response=response_text,
                latency_ms=latency_ms,
                tokens=tokens,
                estimated_cost_usd=cost,
            )
        )
        record_provider_metric(
            db,
            user_id=db_user.id,
            provider=gateway_response.provider,
            model=gateway_response.model,
            latency_ms=gateway_response.provider_latency_ms,
            prompt_tokens=gateway_response.prompt_tokens,
            completion_tokens=gateway_response.completion_tokens,
            total_tokens=tokens,
            cost_usd=cost,
            success=True,
        )
        record_user_activity(
            db,
            user_id=db_user.id,
            action="chat.completed",
            resource_type="model",
            resource_id=gateway_response.model,
            details=f"{gateway_response.provider}:{tokens} tokens",
        )
        db_user.used += 1
        record_usage(db, db_user, tokens, cost)
        db.commit()
    except Exception:
        db.rollback()
        raise

    # -------------------------
    # FINAL RESPONSE (DASHBOARD FORMAT)
    # -------------------------
    return {
        "input": user_input,
        "provider": gateway_response.provider,
        "model": gateway_response.model,
        "response": response_text,
        "latency_ms": latency_ms,
        "tokens": tokens,
        "prompt_tokens": gateway_response.prompt_tokens,
        "completion_tokens": gateway_response.completion_tokens,
        "estimated_cost_usd": cost,
        "attempts": gateway_response.attempts,
        "provider_latency_ms": gateway_response.provider_latency_ms,
        "fallback_used": gateway_response.fallback_used,
    }
