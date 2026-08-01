from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.common.enum.role_enum import RoleEnum
from app.core.security.security import get_password_hash, verify_password
from app.core.utils.string_utils import StringUtils
from app.modules.auth.models import Role
from app.modules.users.models import User


class UserService:
    def __init__(self, db: AsyncSession):
        """Inject the database session when the service is instantiated."""
        self.db = db

    async def create_user(
        self,
        full_name: str,
        phone_number: str,
        password: str,
        confirm_password: str,
        role: RoleEnum = RoleEnum.CUSTOMER,
    ) -> User:
        try:
            result = await self.db.execute(
                select(User).where(User.phone_number == phone_number)
            )
            user = result.scalar_one_or_none()

            if user:
                raise HTTPException(
                    status_code=400, detail="Phone number already registered"
                )

            relatedRole = await self.db.execute(select(Role).where(Role.role == role))
            hashed_password = get_password_hash(password=password)
            id = "US_" + StringUtils.randomAlphaNumeric(10)

            new_user = User(
                id=id,
                full_name=full_name,
                email=None,
                phone_number=phone_number,
                role=relatedRole.scalar_one(),
                password=hashed_password,
            )
            self.db.add(new_user)
            await self.db.commit()
            await self.db.refresh(new_user)
            return new_user

        except HTTPException as http_exc:
            await self.db.rollback()
            print("HTTPException in create_user:", str(http_exc.detail))
            raise http_exc
        except Exception as e:
            await self.db.rollback()
            print("Error in create_user:", str(e))
            raise HTTPException(500, "Internal Server Error - Failed to create user")

    async def get_user_by_phone_number(self, phone_number: str):
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.role))
            .where(User.phone_number == phone_number)
        )
        return result.scalar_one_or_none()

    async def get_authenticated_user(self, user_id: str, role: RoleEnum):
        query = select(User).where(User.id == user_id).options(selectinload(User.role))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_user_profile(
        self,
        user_id: str,
        full_name: str = None,
        email: str = None,
    ) -> User:
        """Update user profile information"""
        try:
            result = await self.db.execute(
                select(User).options(selectinload(User.role)).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()

            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            if email and email != user.email:
                email_check = await self.db.execute(
                    select(User).where((User.email == email) & (User.id != user_id))
                )
                if email_check.scalar_one_or_none():
                    raise HTTPException(status_code=400, detail="Email already in use")
                user.email = email

            if full_name:
                user.full_name = full_name

            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            return user

        except HTTPException as http_exc:
            await self.db.rollback()
            raise http_exc
        except Exception as e:
            await self.db.rollback()
            print("Error in update_user_profile:", str(e))
            raise HTTPException(status_code=500, detail="Failed to update profile")

    async def change_password(
        self,
        user_id: str,
        old_password: str,
        new_password: str,
    ) -> bool:
        """Change user password"""
        try:
            result = await self.db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()

            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            if not verify_password(old_password, user.password):
                raise HTTPException(status_code=400, detail="Incorrect old password")

            user.password = get_password_hash(new_password)

            self.db.add(user)
            await self.db.commit()
            return True

        except HTTPException as http_exc:
            await self.db.rollback()
            raise http_exc
        except Exception as e:
            await self.db.rollback()
            print("Error in change_password:", str(e))
            raise HTTPException(status_code=500, detail="Failed to change password")

    async def update_fcm_token(self, user_id: str, fcm_token: str) -> User:
        """Update Firebase Cloud Messaging token"""
        try:
            result = await self.db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()

            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            user.fcm_token = fcm_token

            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            return user

        except HTTPException as http_exc:
            await self.db.rollback()
            raise http_exc
        except Exception as e:
            await self.db.rollback()
            print("Error in update_fcm_token:", str(e))
            raise HTTPException(status_code=500, detail="Failed to update FCM token")

    async def get_user_with_details(self, user_id: str) -> User:
        """Get user with all details (role, professional profile if exists)"""
        try:
            result = await self.db.execute(
                select(User)
                .options(
                    selectinload(User.role),
                    selectinload(User.files),
                    selectinload(User.professional_profile),
                )
                .where(User.id == user_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            print("Error in get_user_with_details:", str(e))
            raise HTTPException(status_code=500, detail="Failed to fetch user details")

    async def delete_user_account(self, user_id: str) -> bool:
        """Delete user account (soft delete via is_active flag)"""
        try:
            result = await self.db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()

            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            user.is_active = False

            self.db.add(user)
            await self.db.commit()
            return True

        except HTTPException as http_exc:
            await self.db.rollback()
            raise http_exc
        except Exception as e:
            await self.db.rollback()
            print("Error in delete_user_account:", str(e))
            raise HTTPException(status_code=500, detail="Failed to delete account")

    async def search_users(
        self, query: str = None, skip: int = 0, limit: int = 10
    ) -> list[User]:
        """Search users by phone number or name (admin only)"""
        try:
            base_query = select(User).options(selectinload(User.role))

            if query:
                base_query = base_query.where(
                    (User.phone_number.ilike(f"%{query}%"))
                    | (User.full_name.ilike(f"%{query}%"))
                    | (User.email.ilike(f"%{query}%"))
                )

            result = await self.db.execute(
                base_query.order_by(User.created_at.desc()).offset(skip).limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            print("Error in search_users:", str(e))
            raise HTTPException(status_code=500, detail="Failed to search users")

    async def get_all_users(self, skip: int = 0, limit: int = 10) -> list[User]:
        """Get all users with pagination (admin only)"""
        try:
            result = await self.db.execute(
                select(User)
                .options(selectinload(User.role))
                .order_by(User.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            print("Error in get_all_users:", str(e))
            raise HTTPException(status_code=500, detail="Failed to fetch users")
