from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from app.core.db.database import get_db
from app.modules.auth import service
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.auth.schemas import LoginData, UserLogin, UserRegistrationSuccessResponse, LoginResponse
from app.modules.auth.schemas import UserRegister
from app.modules.users.schemas import UserResponse

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])
@auth_router.post("/register", response_model=UserRegistrationSuccessResponse)
async def register(data: UserRegister,db: AsyncSession=Depends(get_db),) -> UserRegistrationSuccessResponse:
    final_result: UserResponse= await service.register_user(db=db, user_data=data) 
    return UserRegistrationSuccessResponse(data=final_result)

@auth_router.post("/login", response_model=LoginResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    try:
        access, refresh, user = await service.login_user(
            db,
            data.phone_number,
            data.password,
        )

        return LoginResponse(
            data=LoginData(access_token=access, refresh_token=refresh, user=user)
        )

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Internal server error" + e.__str__()
        )
