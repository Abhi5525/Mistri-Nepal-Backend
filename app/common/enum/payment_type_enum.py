from enum import StrEnum


class PaymentTypeEnum(StrEnum):
    BOOKING_ADVANCE = "Booking Advance"
    BOOKING_COMPLETE = "Booking Complete"
    BOOKING_CANCEL = "Booking Cancel"
