from fastapi import APIRouter
from fastapi.params import Depends
from app.core.db.database import get_db
from app.modules.auth import service
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.auth.schemas import UserRegistrationSuccessResponse
from app.modules.auth.schemas import UserRegister
from app.modules.users.schemas import UserResponse

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])
@auth_router.post("/register", response_model=UserRegistrationSuccessResponse)
async def register(data: UserRegister,db: AsyncSession=Depends(get_db),) -> UserRegistrationSuccessResponse:
    final_result: UserResponse= await service.register_user(db=db, user_data=data) 
    return UserRegistrationSuccessResponse(data=final_result)