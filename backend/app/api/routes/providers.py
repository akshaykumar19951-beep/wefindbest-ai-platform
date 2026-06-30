from fastapi import APIRouter, Depends

from app.core.auth_deps import get_current_jwt_user
from app.schemas.ai import ProviderHealthResponse
from app.services.ai_service import ai_service

router = APIRouter()


@router.get("/providers/health", response_model=list[ProviderHealthResponse])
def provider_health(user=Depends(get_current_jwt_user)):
    return ai_service.health()
