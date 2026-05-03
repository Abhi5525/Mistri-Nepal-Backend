from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security.security import create_access_token, create_refresh_token, verify_password
from app.modules.auth.schemas import JwtPayload, UserRegister
from app.modules.users.schemas import UserResponse
from app.modules.users.service import create_user, get_authenticated_user, get_user_by_phone_number


async def register_user(db: AsyncSession, user_data: UserRegister) -> UserResponse:
    print("Registering user with data:", user_data.model_dump())
    user_registration_result = await create_user(db, **user_data.model_dump())
    print("User registration successful:", user_registration_result)
    return UserResponse.model_validate(user_registration_result)

async def authenticate_user(db: AsyncSession, phone_number: str, password: str):
    user = await get_user_by_phone_number(db, phone_number)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid phone number")
    if not verify_password(password, user.password):
        raise HTTPException(status_code=401, detail="Invalid password")
    return user


async def login_user(
    db: AsyncSession,
    email: str,
    password: str,
    fcm_token: str | None = None,
):
    try:
        user = await authenticate_user(db, email, password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        if fcm_token and fcm_token != user.fcm_token:
            user.fcm_token = fcm_token
            await db.commit()
            await db.refresh(user)

        # Load user with role-specific profile details and files
        user_with_details = await get_authenticated_user(db, user.id, user.role.role)
        if not user_with_details:
            raise HTTPException(status_code=404, detail="User not found")

        payload = JwtPayload(
            sub=user_with_details.id,
            full_name=user_with_details.full_name,
            role=user_with_details.role.role,
        )
        # print(
        #     f"Creating JWT with payload: sub={user.id}, full_name={user.full_name}, role={user.role.role}"
        # )
        access = create_access_token(payload)
        refresh = create_refresh_token({"sub": user_with_details.id})

        return access, refresh, user_with_details
    except HTTPException as e:
        raise e