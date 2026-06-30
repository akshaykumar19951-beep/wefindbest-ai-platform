from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.db.models.user import User
from app.db.models.chat_message import ChatMessage
from app.core.api_security import get_current_user

router = APIRouter()


@router.get("/history")
def get_chat_history(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    db_user = db.query(User).filter(User.id == user.id).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    history = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == db_user.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(50)
        .all()
    )

    return {
        "user": db_user.email,
        "history": [
            {
                "role": h.role,
                "content": h.content,
                "created_at": h.created_at
            }
            for h in history
        ]
    }
