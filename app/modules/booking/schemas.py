from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.common.enum.booking_payment_status_enum import PaymentStatusEnum
from app.common.enum.booking_status_enum import BookingStatusEnum
from app.common.schema.location import Location


class BookingCreateRequest(BaseModel):
    """Schema for creating a new booking."""

    professional_profile_id: str = Field(
        ..., description="ID of the professional being booked"
    )
    booking_start_time: datetime = Field(..., description="Start time of the booking")
    booking_end_time: datetime = Field(..., description="End time of the booking")
    notes: str | None = Field(
        None, description="Any specific notes or requirements for the job"
    )
    customer_location: Location = Field(
        ..., description="Location where the service is required"
    )


class BookingStatusUpdate(BaseModel):
    """Schema for updating the status of a booking."""

    status: BookingStatusEnum = Field(..., description="New status of the booking")


class BookingPaymentUpdate(BaseModel):
    """Schema for updating the payment details of a booking."""

    paid_amount: float = Field(..., ge=0, description="Amount paid by the customer")
    payment_status: PaymentStatusEnum = Field(..., description="Current payment status")


class BookingResponse(BaseModel):
    """Schema for returning booking details."""

    model_config = ConfigDict(from_attributes=True)

    booking_id: str
    user_id: str
    professional_profile_id: str

    booking_start_time: datetime
    booking_end_time: datetime
    booked_at: datetime

    total_fee: float
    advance_fee: float
    paid_amount: float
    due_amount: float

    payment_status: PaymentStatusEnum
    status: BookingStatusEnum

    notes: str | None = None
    has_reminded: bool

    customer_location: Location | None = None
    professional_location: Location | None = None


class BookingListResponse(BaseModel):
    """Schema for listing bookings in paginated format."""

    data: list[BookingResponse]
    total_count: int
