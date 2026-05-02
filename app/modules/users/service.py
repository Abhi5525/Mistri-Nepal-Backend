from sqlalchemy import select
from app.common.enum.role_enum import RoleEnum
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.core.security.security import get_password_hash
from app.core.utils.string_utils import StringUtils
from app.modules.auth.models import Role
from app.modules.users.models import User

async def create_user(
    db: AsyncSession,
    full_name: str,
    phone_number: str,
    password: str,
    confirm_password: str,
    role: RoleEnum=RoleEnum.CUSTOMER,
)->User:
    try:
        result = await db.execute(select(User).where(User.phone_number == phone_number))
        user = result.scalar_one_or_none()

        if user:
            raise HTTPException(status_code=400, detail="Phone number already registered")

        relatedRole = await db.execute(select(Role).where(Role.role == role))
        hashed_password = get_password_hash(password=password)
        id ="US_"+StringUtils.randomAlphaNumeric(10)
        new_user = User(
            id=id,
            full_name=full_name,
            email=None,
            phone_number=phone_number,
            role=relatedRole.scalar_one(),
            password=hashed_password,
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
    except HTTPException as http_exc:
        db.rollback()
        print("HTTPException in create_user:", str(http_exc.detail))
        raise http_exc
    except Exception as e:
        db.rollback()        
        print("Error in create_user:", str(e))
        raise HTTPException(500, "Internal Server Error - Failed to create user")
    return new_user
