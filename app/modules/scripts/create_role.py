# app/scripts/insert_roles.py
from app.core.db.database import Base, sync_engine, SyncSessionLocal
from app.modules.auth.models import Role
from app.modules.users.models import User  # noqa: F401
from app.core.utils.string_utils import StringUtils
from app.common.enum.role_enum import RoleEnum
# Import all models to ensure they're registered with SQLAlchemy


# ✅ Ensure the table exists
Base.metadata.create_all(bind=sync_engine)


def create_roles_if_not_exist():
    session = SyncSessionLocal()
    try:
        roles = [
            RoleEnum.CUSTOMER,
            RoleEnum.PROFESSIONAL,
            RoleEnum.ADMIN
        ]
        roles_descriptions = [
            "Customer role with access to customer-specific features",
            "Professional role with access to professional-specific features",
            "Admin role with access to all features and management capabilities"
        ]

        for role_name, role_description in zip(roles, roles_descriptions):
            existing_role = (
                session.query(Role).filter(Role.role == role_name.value).first()
            )

            if not existing_role:
                new_role = Role(
                    id=StringUtils.randomAlphaNumeric(8),
                    role=role_name.value,
                    description=role_description,
                )
                session.add(new_role)
                print(f"✅ Created role: {role_name}")
            else:
                print(f"⚠️ Role already exists: {role_name}")

        session.commit()
    except Exception as e:
        session.rollback()
        print(f"❌ Error while inserting roles: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    create_roles_if_not_exist()
