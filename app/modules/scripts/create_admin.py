"""Seed default admin user for the application."""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.common.enum.role_enum import RoleEnum
from app.core.db.database import AsyncSessionLocal
from app.core.security.security import get_password_hash
from app.core.utils.string_utils import StringUtils

# Import models to ensure they're registered with SQLAlchemy
from app.modules.auth.models import Authorization, Role  # noqa: F401
from app.modules.users.models import User
from app.modules.file.models import File  # noqa: F401
from app.modules.professional_applications.models import (  # noqa: F401
    ProfessionalApplication,
)
from app.modules.professionals.models import ProfessionalProfile  # noqa: F401
from app.modules.skills.models import Skill  # noqa: F401

# Default Admin Configuration
ADMIN_FULL_NAME = "System Admin"
ADMIN_PHONE = "9898989898"
ADMIN_EMAIL = "admin@mistrinepal.com"
ADMIN_PASSWORD = "AdminPassword@123"


async def create_admin():
    """Create default admin user if one does not already exist."""
    async with AsyncSessionLocal() as session:
        try:
            # Check if ADMIN role exists
            result = await session.execute(
                select(Role).where(Role.role == RoleEnum.ADMIN.value)
            )
            admin_role = result.scalar_one_or_none()

            if not admin_role:
                print(
                    "[ERROR] ADMIN role not found in database. "
                    "Please run create_role.py first."
                )
                raise Exception("ADMIN role not found")

            # Check if an admin user already exists
            existing_admin_result = await session.execute(
                select(User).where(
                    (User.role_id == admin_role.id)
                    | (User.phone_number == ADMIN_PHONE)
                    | (User.email == ADMIN_EMAIL)
                )
            )
            existing_admin = existing_admin_result.scalars().first()

            if existing_admin:
                print(
                    f"[ERROR] Admin user already exists! "
                    f"(ID: {existing_admin.id}, Phone: {existing_admin.phone_number}). "
                    f"Aborting admin creation."
                )
                raise Exception(
                    f"Admin user already exists with ID: {existing_admin.id}"
                )

            # Create new Admin User
            user_id = "US_" + StringUtils.randomAlphaNumeric(10)
            hashed_password = get_password_hash(ADMIN_PASSWORD)

            new_admin = User(
                id=user_id,
                full_name=ADMIN_FULL_NAME,
                phone_number=ADMIN_PHONE,
                email=ADMIN_EMAIL,
                password=hashed_password,
                is_active=True,
                role_id=admin_role.id,
            )

            session.add(new_admin)
            await session.commit()
            await session.refresh(new_admin)

            print("[SUCCESS] Admin user created successfully!")
            print(f"  - User ID: {new_admin.id}")
            print(f"  - Full Name: {new_admin.full_name}")
            print(f"  - Phone Number: {new_admin.phone_number}")
            print(f"  - Email: {new_admin.email}")
            return new_admin

        except Exception as e:
            await session.rollback()
            print(f"[ERROR] Error while creating admin: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(create_admin())
