from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    api_key = Column(String, unique=True, nullable=False, index=True)
    role = Column(String, nullable=False, default="user")
    email_verified = Column(Boolean, nullable=False, default=False)
    quota = Column(Integer, nullable=False, default=1000)
    used = Column(Integer, nullable=False, default=0)
    plan = Column(String, nullable=False, default="free")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    requests = relationship("AIRequest", backref="user", lazy="dynamic")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    memberships = relationship("TeamMember", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", cascade="all, delete-orphan")
