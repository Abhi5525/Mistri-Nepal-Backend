from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Column, String, Boolean, DateTime, Integer, Float, Table, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.models.timestamp_mixin import TimestampMixin
from app.core.db.database import Base

if TYPE_CHECKING:
    from app.modules.users.models import User
    from app.modules.skills.models import Skill
    from app.modules.professionals.documents_model import ProfessionalDocument

professional_skills = Table(
    "professional_skills",
    Base.metadata,
    Column("professional_id", String(13), ForeignKey("professional_profiles.id", ondelete="CASCADE")),
    Column("skill_id", Integer, ForeignKey("skills.id", ondelete="CASCADE")),
)

class ProfessionalProfile(Base, TimestampMixin):
    __tablename__ = "professional_profiles"

    id: Mapped[str] = mapped_column(String(13), primary_key=True, index=True)

    user_id: Mapped[str] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )

    province: Mapped[str] = mapped_column(String(100), nullable=False)
    district: Mapped[str] = mapped_column(String(100), nullable=False)
    municipality: Mapped[str] = mapped_column(String(100), nullable=False)
    ward: Mapped[int] = mapped_column(Integer, nullable=False)

    experience: Mapped[int] = mapped_column(Integer, default=0)
    about_yourself: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hourly_rate: Mapped[float] = mapped_column(Float, default=0)

    average_rating: Mapped[float] = mapped_column(Float, default=0.0)
    total_reviews: Mapped[int] = mapped_column(Integer, default=0)

    is_available: Mapped[bool] = mapped_column(Boolean, default=False)

    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    verification_status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)
    
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_by: Mapped[Optional[str]] = mapped_column(ForeignKey("user.id"), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="professional_profile")
    skills: Mapped[list["Skill"]] = relationship(
        secondary="professional_skills",
        back_populates="professionals"
    )
    documents: Mapped[list["ProfessionalDocument"]] = relationship(
        back_populates="professional",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return (
            f"<ProfessionalProfile(id={self.id}, user_id={self.user_id}, "
            f"district='{self.district}', verification_status='{self.verification_status}')>"
        )