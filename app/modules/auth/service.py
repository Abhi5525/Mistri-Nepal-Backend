from fastapi.security import OAuth2PasswordBearer
from app.core.db.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.core.exceptions import HttpException
from starlette import status

from app.modules.auth.models import User
from app.modules.auth.models import ProfessionalProfile

OAuth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

async def get_current_user(
        token: str = Depends(OAuth2_scheme), 
        db: AsyncSession = Depends(get_db)) -> User:
    """
    Get current authenticated user from JWT token
    Use this dependency to protect routes that require authentication
    """

    credentials_exception = HttpException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = OAuth2_scheme.decode_token(token)
        if payload.get_type() != "access":
            raise credentials_exception
        
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
    
    result = await db.execute(User.select().where(User.c.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HttpException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def get_current_active_professional(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)) -> User:
    
    """
    Get current user and verify they are an approved professional
    Use for professional-only endpoints
    """ 
    if not current_user.is_professional:
        raise HttpException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
            headers={"WWW-Authenticate": "Bearer"},
        )
    result = await db.execute(ProfessionalProfile.select().where(ProfessionalProfile.user_id == current_user.id))
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HttpException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Must have a professional profile to access this resource",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user

async def get_current_admin(
        current_user: User = Depends(get_current_user)) -> User:
    """
    Get current user and verify they are an admin
    Use for admin-only endpoints
    """ 
    if not current_user.is_admin or not current_user.is_staff:
        raise HttpException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user
