from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Float, Text, ForeignKey, Boolean, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.common.models.timestamp_mixin import TimestampMixin
from app.core.db.database import Base

from app.modules.skills.models import Skill

if TYPE_CHECKING:
    from app.modules.users.models import User
    from app.modules.file.models import File
    # from app.modules.bookings.models import Booking
    # from app.modules.reviews.models import Review

professional_skills = Table(
    "professional_skills",
    Base.metadata,
    Column("professional_profile_id", Integer, ForeignKey("professional_profiles.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", Integer, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)

class ProfessionalProfile(Base, TimestampMixin):
    __tablename__ = "professional_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    user_id: Mapped[str] = mapped_column(
        String(13),
        ForeignKey("user.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )

    # --- Promoted from Application ---
    profile_image_id: Mapped[Optional[str]] = mapped_column(
        String(13), ForeignKey("file.file_id", ondelete="SET NULL"), nullable=True
    )
    citizenship_front_id: Mapped[str] = mapped_column(
        String(13), ForeignKey("file.file_id", ondelete="RESTRICT"), nullable=False
    )
    citizenship_back_id: Mapped[str] = mapped_column(
        String(13), ForeignKey("file.file_id", ondelete="RESTRICT"), nullable=False
    )
    experience: Mapped[str] = mapped_column(String(100), nullable=False)
    about_yourself: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    other_skills: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    base_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True, index=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True, index=True)

    # --- Operational Metrics ---
    average_rating: Mapped[float] = mapped_column(Float, default=0.0)
    total_reviews: Mapped[int] = mapped_column(Integer, default=0)
    total_completed_jobs: Mapped[int] = mapped_column(Integer, default=0)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    # --- Relationships ---
    user: Mapped["User"] = relationship(back_populates="professional_profile")
    profile_image: Mapped[Optional["File"]] = relationship(foreign_keys=[profile_image_id])
    citizenship_front: Mapped["File"] = relationship(foreign_keys=[citizenship_front_id])
    citizenship_back: Mapped["File"] = relationship(foreign_keys=[citizenship_back_id])
    
    skills: Mapped[list["Skill"]] = relationship(
        secondary=professional_skills,
        back_populates="professionals"
    )
    # bookings: Mapped[list["Booking"]] = relationship(back_populates="professional")
    # reviews: Mapped[list["Review"]] = relationship(back_populates="professional")