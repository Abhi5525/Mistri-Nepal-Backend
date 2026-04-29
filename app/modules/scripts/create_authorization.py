"""Seed authorization rules for the application."""
# pyright: reportUnusedImport=false

from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.common.enum.role_enum import RoleEnum
from app.core.utils.string_utils import StringUtils
from app.core.db.database import AsyncSessionLocal
# import models to ensure they're registered with SQLAlchemy
from app.modules.auth.models import Authorization, Role
from app.modules.users.models import User  # noqa: F401

# Define HTTP methods
readOnlyMethods = ["GET"]
postMethod = ["POST"]
updateMethods = [ "PUT", "PATCH"]
deleteMethod = ["DELETE"]


def setAuthorizationPermissions(
    role: Role, path: str, methods: List[str]
) -> Authorization:
    auth = Authorization()
    auth.id = StringUtils.randomAlphaNumeric(8)
    auth.role = role
    auth.path = path
    auth.methods = methods
    return auth


def getAdminPermissions(role: Role) -> List[Authorization]:
    return [
        setAuthorizationPermissions(
            role, "/api/v1/adminDashboard", readOnlyMethods 
        ),
        setAuthorizationPermissions(
            role, "/api/v1/users", readOnlyMethods
        ),
    ]


def getCustomerPermissions(role: Role) -> List[Authorization]:
    return [
       setAuthorizationPermissions(
            role, "/api/v1/loggedInUser", readOnlyMethods
        ),
        setAuthorizationPermissions(
            role, "/api/v1/professionalApplication/submit", postMethod
        ),
    ]


def getProfessionalPermissions(role: Role) -> List[Authorization]:
    return [
       setAuthorizationPermissions(
            role, "/api/v1/loggedInUser", readOnlyMethods
        ),
       setAuthorizationPermissions(
            role, "/api/v1/professionalProfile", readOnlyMethods
        ),
       setAuthorizationPermissions(
            role, "/api/v1/professionalProfile/update/me", updateMethods
        ),
    ]

# ✅ Async version (recommended for FastAPI)
async def create_authorizations():
    async with AsyncSessionLocal() as session:
        try:
            # ✅ Check if all required roles exist
            required_roles = list(RoleEnum.__members__.keys())
            result = await session.execute(
                select(Role).filter(Role.role.in_(required_roles))
            )
            roles = list(result.scalars().all())

            if len(roles) != len(required_roles):
                missing_roles = set(required_roles) - {r.role for r in roles}
                raise Exception(
                    f"❌ One or more roles not found: {', '.join(missing_roles)}"
                )

            print("✅ All roles verified successfully")

            # Find each role
            admin = next(r for r in roles if r.role == RoleEnum.ADMIN)
            customer = next(r for r in roles if r.role == RoleEnum.CUSTOMER)
            professional = next(r for r in roles if r.role == RoleEnum.PROFESSIONAL)

            # ✅ Parallel permission creation (like Promise.all)
            from asyncio import gather

            authorizations_lists = await gather(
                *[
                    _create_permissions(session, getAdminPermissions, admin),
                    _create_permissions(
                        session, getCustomerPermissions, customer
                    ),
                    _create_permissions(session, getProfessionalPermissions, professional),
                ]
            )

            # Flatten the lists
            all_authorizations = [
                auth for sublist in authorizations_lists for auth in sublist
            ]

            await session.commit()
            print("✅ Authorizations created successfully")
            return all_authorizations

        except Exception as e:
            await session.rollback()
            print(f"❌ Error while creating authorizations: {e}")
            raise


# helper for async gather
async def _create_permissions(
    session: AsyncSession, permission_fn, role: Role
) -> List[Authorization]:
    authorizations = permission_fn(role)
    session.add_all(authorizations)
    return authorizations


# Main execution
if __name__ == "__main__":
    import asyncio

    asyncio.run(create_authorizations())
