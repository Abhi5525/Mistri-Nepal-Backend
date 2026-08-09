"""Seed authorization rules for the application."""
# pyright: reportUnusedImport=false

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.common.enum.role_enum import RoleEnum
from app.core.db.database import AsyncSessionLocal
from app.core.utils.string_utils import StringUtils

# import models to ensure they're registered with SQLAlchemy
from app.modules.auth.models import Authorization, Role  # noqa: F401
from app.modules.booking.models import Booking  # noqa: F401
from app.modules.file.models import File  # noqa: F401
from app.modules.payments.models import Payment  # noqa: F401
from app.modules.professional_applications.models import (  # noqa: F401
    ProfessionalApplication,
)
from app.modules.professionals.models import (  # noqa: F401
    ProfessionalProfile,
    professional_skills,
)
from app.modules.reviews.models import Review  # noqa: F401
from app.modules.skills.models import Skill  # noqa: F401
from app.modules.users.models import User  # noqa: F401

# Define HTTP methods
readOnlyMethods = ["GET"]
postMethod = ["POST"]
writeMethods = ["DELETE", "PUT", "PATCH"]


def setAuthorizationPermissions(
    role: Role, path: str, methods: list[str]
) -> Authorization:
    auth = Authorization()
    auth.id = StringUtils.randomAlphaNumeric(8)
    auth.role = role
    auth.path = path
    auth.methods = methods
    return auth


def getAdminPermissions(role: Role) -> list[Authorization]:
    return [
        setAuthorizationPermissions(role, "/api/v1/adminDashboard", readOnlyMethods),
        setAuthorizationPermissions(role, "/api/v1/users", readOnlyMethods),
        setAuthorizationPermissions(role, "/api/v1/skills", postMethod),
        setAuthorizationPermissions(role, "/api/v1/skills/{skill_id}", writeMethods),
        setAuthorizationPermissions(
            role, "/api/v1/professionalApplication", readOnlyMethods
        ),
        setAuthorizationPermissions(
            role,
            "/api/v1/professionalApplication/{application_id}/status",
            writeMethods,
        ),
    ]


def getCustomerPermissions(role: Role) -> list[Authorization]:
    return [
        setAuthorizationPermissions(role, "/api/v1/loggedInUser", readOnlyMethods),
        setAuthorizationPermissions(
            role, "/api/v1/professionalApplication", postMethod
        ),
        setAuthorizationPermissions(
            role, "/api/v1/professionalApplication/me", readOnlyMethods
        ),
        setAuthorizationPermissions(role, "/api/v1/booking", postMethod),
        setAuthorizationPermissions(role, "/api/v1/booking/me", readOnlyMethods),
    ]


def getProfessionalPermissions(role: Role) -> list[Authorization]:
    return [
        setAuthorizationPermissions(role, "/api/v1/loggedInUser", readOnlyMethods),
        setAuthorizationPermissions(
            role, "/api/v1/professionalProfile", readOnlyMethods
        ),
        setAuthorizationPermissions(
            role, "/api/v1/professionalProfile/update/me", writeMethods
        ),
        setAuthorizationPermissions(
            role, "/api/v1/professionalApplication/me", readOnlyMethods
        ),
        setAuthorizationPermissions(role, "/api/v1/booking/professional/me", readOnlyMethods),
        setAuthorizationPermissions(
            role, "/api/v1/booking/{booking_id}/status", writeMethods
        ),
        setAuthorizationPermissions(
            role, "/api/v1/booking/{booking_id}/payment", writeMethods
        ),
    ]


async def create_authorizations():
    async with AsyncSessionLocal() as session:
        try:
            # Fetch all roles from database
            result = await session.execute(select(Role))
            roles = list(result.scalars().all())

            # Helper to match role flexibly by name or value (e.g. 'CUSTOMER' vs 'Customer')
            def find_role(role_enum: RoleEnum) -> Role:
                for r in roles:
                    role_str = str(r.role).upper()
                    if role_str == role_enum.name or role_str == role_enum.value.upper():
                        return r
                raise Exception(
                    f"Role {role_enum.name}/{role_enum.value} not found in database. Please run create_role.py first."
                )

            admin = find_role(RoleEnum.ADMIN)
            customer = find_role(RoleEnum.CUSTOMER)
            professional = find_role(RoleEnum.PROFESSIONAL)

            print("[SUCCESS] All roles verified successfully")

            authorizations_lists = [
                await _create_permissions(session, getAdminPermissions, admin),
                await _create_permissions(session, getCustomerPermissions, customer),
                await _create_permissions(session, getProfessionalPermissions, professional),
            ]

            # Flatten the lists
            all_authorizations = [
                auth for sublist in authorizations_lists for auth in sublist
            ]

            await session.commit()
            print("[SUCCESS] Authorizations created successfully")
            return all_authorizations

        except Exception as e:
            await session.rollback()
            print(f"[ERROR] Error while creating authorizations: {e}")
            raise


async def _create_permissions(
    session: AsyncSession, permission_fn, role: Role
) -> list[Authorization]:
    desired_auths = permission_fn(role)
    created_or_updated = []
    for auth in desired_auths:
        result = await session.execute(
            select(Authorization).where(
                Authorization.role_id == role.id,
                Authorization.path == auth.path,
            )
        )
        existing_records = list(result.scalars().all())
        if existing_records:
            primary = existing_records[0]
            primary.methods = auth.methods
            # Remove any duplicate authorization records for the same role and path
            for duplicate in existing_records[1:]:
                await session.delete(duplicate)
            created_or_updated.append(primary)
        else:
            session.add(auth)
            created_or_updated.append(auth)
    return created_or_updated


# Main execution
if __name__ == "__main__":
    import asyncio

    asyncio.run(create_authorizations())

