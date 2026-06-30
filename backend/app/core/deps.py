from fastapi import Header, HTTPException, Depends, status
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.models import User


# -------------------------
# DATABASE SESSION
# -------------------------
def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# -------------------------
# API KEY AUTH
# -------------------------
def get_user_by_api_key(
    x_api_key: str = Header(None),
    db: Session = Depends(get_db)
):

    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key"
        )

    user = (
        db.query(User)
        .filter(User.api_key == x_api_key)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )

    return user