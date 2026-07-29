from datetime import datetime
from enum import Enum
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Float, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.common.models.timestamp_mixin import TimestampMixin
from app.core.db.database import Base

if TYPE_CHECKING:
    from app.modules.users.models import User
    from app.modules.file.models import File


class ApplicationStatusEnum(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ProfessionalApplication(Base, TimestampMixin):
    __tablename__ = "professional_applications"

    professional_application_id: Mapped[str] = mapped_column(
        String(13), primary_key=True, index=True
    )

    # 🔥 CRITICAL: Matches User.id type (String 13)
    user_id: Mapped[str] = mapped_column(
        String(13),
        ForeignKey("user.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # --- Contact & Location ---
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    province: Mapped[str] = mapped_column(String(100), nullable=False)
    district: Mapped[str] = mapped_column(String(100), nullable=False)
    municipality: Mapped[str] = mapped_column(String(100), nullable=False)
    ward: Mapped[int] = mapped_column(Integer, nullable=False)

    # --- Professional Details ---
    experience: Mapped[str] = mapped_column(String(100), nullable=False)
    about_yourself: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    base_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # --- File Relationships (Required) ---
    # 🔥 Relates directly to the File entity instead of storing strings
    profile_image_id: Mapped[str] = mapped_column(
        String(13), ForeignKey("file.file_id", ondelete="RESTRICT"), nullable=False
    )
    citizenship_front_id: Mapped[str] = mapped_column(
        String(13), ForeignKey("file.file_id", ondelete="RESTRICT"), nullable=False
    )
    citizenship_back_id: Mapped[str] = mapped_column(
        String(13), ForeignKey("file.file_id", ondelete="RESTRICT"), nullable=False
    )

    # --- Workflow State ---
    status: Mapped[ApplicationStatusEnum] = mapped_column(
        SQLEnum(ApplicationStatusEnum, name="application_status_enum"),
        default=ApplicationStatusEnum.PENDING,
        nullable=False,
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # --- Admin Audit Trail ---
    reviewed_by: Mapped[Optional[str]] = mapped_column(
        String(13), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # --- Relationships ---
    user: Mapped["User"] = relationship(
        "User",
        back_populates="professional_application",
        foreign_keys="[ProfessionalApplication.user_id]",
    )
    profile_image: Mapped["File"] = relationship(foreign_keys=[profile_image_id])
    citizenship_front: Mapped["File"] = relationship(
        foreign_keys=[citizenship_front_id]
    )
    citizenship_back: Mapped["File"] = relationship(foreign_keys=[citizenship_back_id])
