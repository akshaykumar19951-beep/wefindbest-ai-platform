from fastapi import APIRouter, Depends

from app.core.api_security import get_current_user
from app.db.models.user import User
from app.schemas.auth import UserResponse

router = APIRouter()


@router.get("/me", response_model=UserResponse)
def get_current_account(user: User = Depends(get_current_user)):
    return user
