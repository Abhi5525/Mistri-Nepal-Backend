from sqlalchemy import Integer, String, Text, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING
from app.core.db.database import Base
from app.common.models.timestamp_mixin import TimestampMixin

if TYPE_CHECKING:
    from app.modules.users.models import User
    from app.modules.professionals.models import ProfessionalProfile
    from app.modules.booking.models import Booking


class Review(Base, TimestampMixin):
    __tablename__ = "reviews"

    review_id: Mapped[str] = mapped_column(String(13), primary_key=True, index=True)

    # Relationships / FKs
    booking_id: Mapped[str] = mapped_column(
        String(13), ForeignKey("bookings.booking_id", ondelete="CASCADE"), unique=True, nullable=False
    )
    reviewer_id: Mapped[str] = mapped_column(
        String(13), ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True
    )
    professional_profile_id: Mapped[str] = mapped_column(
        String(13),
        ForeignKey("professional_profiles.professional_profile_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Rating & Text are both nullable because user can submit rating now, text later.
    # Check constraint ensures rating is between 1 and 5 if it exists.
    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, CheckConstraint = "(rating >= 1 AND rating <= 5)")
    review_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="check_rating_range"),
    )

    # ORM relationships
    reviewer: Mapped["User"] = relationship()
    professional_profile: Mapped["ProfessionalProfile"] = relationship(back_populates="reviews")
    booking: Mapped["Booking"] = relationship()
