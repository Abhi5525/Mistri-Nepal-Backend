from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enum.booking_payment_status_enum import (
    PaymentStatusEnum as BookingPaymentStatusEnum,
)
from app.common.enum.booking_status_enum import BookingStatusEnum
from app.common.models.timestamp_mixin import TimestampMixin
from app.common.schema.location import Location
from app.core.db.database import Base
from app.core.pydantic_middleware.custom_typedecorator import PydanticType

if TYPE_CHECKING:
    from app.modules.professionals.models import ProfessionalProfile
    from app.modules.users.models import User


class Booking(Base, TimestampMixin):
    __tablename__ = "bookings"

    booking_id: Mapped[str] = mapped_column(String(13), primary_key=True, index=True)

    # --- Foreign Keys & Relations ---
    user_id: Mapped[str] = mapped_column(
        String(13), ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True
    )
    professional_profile_id: Mapped[str] = mapped_column(
        String(13),
        ForeignKey("professional_profiles.professional_profile_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # --- Time & Schedule Fields ---
    booking_start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    booking_end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    booked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # --- Financial Fields ---
    total_fee: Mapped[float] = mapped_column(Float, nullable=False)
    advance_fee: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    paid_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    due_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # --- Enums ---
    payment_status: Mapped[BookingPaymentStatusEnum] = mapped_column(
        SQLEnum(
            BookingPaymentStatusEnum,
            name="booking_payment_status_enum",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=BookingPaymentStatusEnum.UNPAID,
        server_default=BookingPaymentStatusEnum.UNPAID.value,
    )
    status: Mapped[BookingStatusEnum] = mapped_column(
        SQLEnum(
            BookingStatusEnum,
            name="booking_status_enum",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=BookingStatusEnum.PENDING_PAYMENT,
        server_default=BookingStatusEnum.PENDING_PAYMENT.value,
    )

    # --- Additional Notes & Flags ---
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    has_reminded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # --- Location Fields (Pydantic JSONB TypeDecorator) ---
    customer_location: Mapped[Optional[Location]] = mapped_column(
        PydanticType(Location), nullable=True
    )
    professional_location: Mapped[Optional[Location]] = mapped_column(
        PydanticType(Location), nullable=True
    )

    # --- Relationships ---
    user: Mapped["User"] = relationship(back_populates="bookings")
    professional_profile: Mapped["ProfessionalProfile"] = relationship(
        back_populates="bookings"
    )
