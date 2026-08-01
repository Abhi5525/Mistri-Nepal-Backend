from fastapi import APIRouter, Depends, HTTPException

from app.modules.auth import service
from app.modules.auth.schemas import (
    LoginData,
    LoginResponse,
    UserLogin,
    UserRegister,
    UserRegistrationSuccessResponse,
)
from app.modules.users.dependencies import get_user_service
from app.modules.users.schemas import UserResponse
from app.modules.users.service import UserService

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post("/register", response_model=UserRegistrationSuccessResponse)
async def register(
    data: UserRegister,
    user_service: UserService = Depends(get_user_service),
) -> UserRegistrationSuccessResponse:
    final_result: UserResponse = await service.register_user(
        user_data=data,
        user_service=user_service,
    )
    return UserRegistrationSuccessResponse(data=final_result)


@auth_router.post("/login", response_model=LoginResponse)
async def login(
    data: UserLogin,
    user_service: UserService = Depends(get_user_service),
):
    try:
        access, refresh, user = await service.login_user(
            phone_number=data.phone_number,
            password=data.password,
            user_service=user_service,
        )

        return LoginResponse(
            data=LoginData(access_token=access, refresh_token=refresh, user=user)
        )

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Internal server error " + str(e)
        )

