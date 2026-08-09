from app.common.enum.role_enum import RoleEnum
from app.core.db.database import Base, SyncSessionLocal, sync_engine
from app.core.utils.string_utils import StringUtils

# Import all models to ensure they're registered with SQLAlchemy
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

# Ensure tables exist
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
                print(f"[SUCCESS] Created role: {role_name}")
            else:
                print(f"[INFO] Role already exists: {role_name}")

        session.commit()
    except Exception as e:
        session.rollback()
        print(f"[ERROR] Error while inserting roles: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    create_roles_if_not_exist()
