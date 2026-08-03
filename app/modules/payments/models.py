from datetime import datetime
from sqlalchemy import Float, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING
from app.core.db.database import Base
from app.common.models.timestamp_mixin import TimestampMixin
from sqlalchemy import Enum as SQLEnum

from app.common.enum.payment_method_enum import PaymentMethodEnum
from app.common.enum.payment_transaction_status_enum import PaymentTransactionStatusEnum
from app.common.enum.payment_type_enum import PaymentTypeEnum

if TYPE_CHECKING:
    from app.modules.users.models import User
    from app.modules.booking.models import Booking


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    payment_id: Mapped[str] = mapped_column(String(20), primary_key=True, index=True)

    booking_id: Mapped[str] = mapped_column(
        String(13), ForeignKey("bookings.booking_id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(13), ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True
    )

    amount: Mapped[float] = mapped_column(Float, nullable=False)
    
    payment_method: Mapped[PaymentMethodEnum] = mapped_column(
        SQLEnum(PaymentMethodEnum, name="payment_method_enum", values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    
    payment_type: Mapped[PaymentTypeEnum] = mapped_column(
        SQLEnum(PaymentTypeEnum, name="payment_type_enum", values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    
    gateway_reference_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True) # pidx for khalti, ref_id for esewa
    
    status: Mapped[PaymentTransactionStatusEnum] = mapped_column(
        SQLEnum(PaymentTransactionStatusEnum, name="payment_transaction_status_enum", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=PaymentTransactionStatusEnum.PENDING
    )

    # Relationships
    user: Mapped["User"] = relationship()
    booking: Mapped["Booking"] = relationship()
