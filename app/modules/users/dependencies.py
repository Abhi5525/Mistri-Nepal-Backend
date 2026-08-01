from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.database import get_db
from app.modules.users.service import UserService


# Centralize dependency injection here
def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)
