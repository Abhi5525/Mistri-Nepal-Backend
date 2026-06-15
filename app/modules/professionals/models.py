from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Column, String, Boolean, DateTime, Integer, Float, Table, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.models.timestamp_mixin import TimestampMixin
from app.core.db.database import Base

if TYPE_CHECKING:
    from app.modules.auth.models import User
    from app.modules.skills.models import Skill
    from app.modules.booking.models import Booking
    from app.modules.models.models import Review

    professional_skills = Table(
    "professional_skills",
    Base.metadata,
    Column("professional_id", Integer, ForeignKey("professional_profiles.id", ondelete="CASCADE")),
    Column("skill_id", Integer, ForeignKey("skills.id", ondelete="CASCADE")),
)

class ProfessionalProfile(Base, TimestampMixin):
    __tablename__ = "professional_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    province: Mapped[str] = mapped_column(String(100), nullable=False)
    district: Mapped[str] = mapped_column(String(100), nullable=False)
    municipality: Mapped[str] = mapped_column(String(100), nullable=False)
    ward: Mapped[int] = mapped_column(Integer, nullable=False)

    experience: Mapped[int] = mapped_column(Integer, default=0)
    about_yourself: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rate: Mapped[float] = mapped_column(Float, default=0)

    average_rating: Mapped[float] = mapped_column(Float, default=0.0)
    total_reviews: Mapped[int] = mapped_column(Integer, default=0)

    profile_picture: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    citizenship_front: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    citizenship_back: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    is_available: Mapped[bool] = mapped_column(Boolean, default=True)

    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    verification_status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)

    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    verified_by: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"), nullable=True)

    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    skills: Mapped[list["Skill"]] = relationship(
        secondary="professional_skills",
        back_populates="professionals"
    )