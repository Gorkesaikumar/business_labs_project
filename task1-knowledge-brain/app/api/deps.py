from typing import Optional
from fastapi import Header, HTTPException, status
from app.core.config import settings


async def verify_admin_key(x_api_key: Optional[str] = Header(None, alias="X-API-Key")) -> bool:
    """Authentication and authorization dependency for administrative endpoints."""
    # Allow in development if configured, or check against TASK1_API_KEY
    if not x_api_key or x_api_key != settings.TASK1_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing administrative API Key (X-API-Key header required).",
        )
    return True
