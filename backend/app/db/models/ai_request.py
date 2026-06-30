from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from datetime import datetime

from app.db.database import Base


class AIRequest(Base):
    __tablename__ = "ai_requests"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    prompt = Column(Text, nullable=False)

    response = Column(Text, nullable=True)

    model = Column(String, default="mock")

    created_at = Column(DateTime, default=datetime.utcnow)
