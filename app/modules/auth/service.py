from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.auth.schemas import UserRegister
from app.modules.users.schemas import UserResponse
from app.modules.users.service import create_user


async def register_user(db: AsyncSession, user_data: UserRegister) -> UserResponse:
    print("Registering user with data:", user_data.model_dump())
    user_registration_result = await create_user(db, **user_data.model_dump())
    print("User registration successful:", user_registration_result)
    return UserResponse.model_validate(user_registration_result)
