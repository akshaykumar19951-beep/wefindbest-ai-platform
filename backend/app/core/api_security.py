from datetime import datetime

from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.db.models import APIKey, User

api_key_scheme = APIKeyHeader(
    name="x-api-key",
    scheme_name="API Key",
    description="Enter your API key",
    auto_error=False,
)


def get_current_user(
    request: Request,
    api_key: str = Security(api_key_scheme),
    db: Session = Depends(get_db),
):
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key missing",
        )

    key_record = (
        db.query(APIKey)
        .filter(APIKey.key == api_key, APIKey.is_active == True)
        .first()
    )

    if key_record:
        key_record.last_used_at = datetime.utcnow()
        request.state.user_id = key_record.user_id
        request.state.api_key_prefix = api_key[:12]
        db.commit()
        return key_record.user

    user = db.query(User).filter(User.api_key == api_key).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
        )

    request.state.user_id = user.id
    request.state.api_key_prefix = api_key[:12]
    return user
