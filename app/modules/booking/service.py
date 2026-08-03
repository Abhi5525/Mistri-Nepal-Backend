from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.core.utils.string_utils import StringUtils
from app.modules.booking.models import Booking
from app.modules.booking.schemas import (
    BookingCreateRequest,
    BookingPaymentUpdate,
    BookingStatusUpdate,
)
from app.modules.professionals.models import ProfessionalProfile
from app.common.enum.booking_status_enum import BookingStatusEnum
from app.common.enum.booking_payment_status_enum import PaymentStatusEnum


async def create_booking(
    db: AsyncSession, user_id: str, data: BookingCreateRequest
) -> Booking:
    """Create a new booking."""
    
    # Check if professional exists and fetch their details
    result = await db.execute(
        select(ProfessionalProfile).where(
            ProfessionalProfile.professional_profile_id == data.professional_profile_id
        )
    )
    professional = result.scalars().first()
    if not professional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professional profile not found",
        )
        
    if not professional.is_available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This professional is currently not available for bookings.",
        )

    # Validate timing
    if data.booking_start_time >= data.booking_end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking end time must be after start time",
        )

    # Calculate duration in hours
    duration_delta = data.booking_end_time - data.booking_start_time
    duration_hours = duration_delta.total_seconds() / 3600.0

    # Backend Fee Calculation (base_rate/hourly_rate)
    # The ProfessionalProfile schema uses base_rate or hourly_rate depending on the exact model. 
    # Based on the models, it seems `base_rate` might be the field name on the model.
    rate = getattr(professional, 'base_rate', getattr(professional, 'hourly_rate', 0.0))
    total_fee = rate * duration_hours
    
    booking_id = "BK_" + StringUtils.randomAlphaNumeric(10)

    # Professional's location snapshot (optional depending on if it exists)
    prof_location = None
    if professional.latitude and professional.longitude:
        prof_location = {
            "latitude": professional.latitude,
            "longitude": professional.longitude
        }

    new_booking = Booking(
        booking_id=booking_id,
        user_id=user_id,
        professional_profile_id=data.professional_profile_id,
        booking_start_time=data.booking_start_time,
        booking_end_time=data.booking_end_time,
        total_fee=total_fee,
        advance_fee=0.0,
        paid_amount=0.0,
        due_amount=total_fee,
        payment_status=PaymentStatusEnum.UNPAID,
        status=BookingStatusEnum.PENDING_PAYMENT,
        notes=data.notes,
        customer_location=data.customer_location.model_dump(),
        professional_location=prof_location,
    )

    db.add(new_booking)
    await db.commit()
    await db.refresh(new_booking)
    return new_booking


async def get_booking_by_id(db: AsyncSession, booking_id: str) -> Optional[Booking]:
    """Get a single booking by ID."""
    result = await db.execute(
        select(Booking).where(Booking.booking_id == booking_id)
    )
    return result.scalars().first()


async def get_user_bookings(
    db: AsyncSession, user_id: str, skip: int = 0, limit: int = 10
) -> tuple[List[Booking], int]:
    """Get all bookings for a user."""
    # Count total
    count_query = select(Booking).where(Booking.user_id == user_id)
    count_result = await db.execute(count_query)
    total_count = len(count_result.scalars().all())

    # Get paginated data
    query = (
        select(Booking)
        .where(Booking.user_id == user_id)
        .order_by(Booking.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    bookings = result.scalars().all()
    
    return list(bookings), total_count


async def get_professional_bookings(
    db: AsyncSession, professional_profile_id: str, skip: int = 0, limit: int = 10
) -> tuple[List[Booking], int]:
    """Get all bookings for a professional."""
    # Count total
    count_query = select(Booking).where(Booking.professional_profile_id == professional_profile_id)
    count_result = await db.execute(count_query)
    total_count = len(count_result.scalars().all())

    # Get paginated data
    query = (
        select(Booking)
        .where(Booking.professional_profile_id == professional_profile_id)
        .order_by(Booking.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    bookings = result.scalars().all()
    
    return list(bookings), total_count


async def update_booking_status(
    db: AsyncSession, booking_id: str, status_data: BookingStatusUpdate
) -> Booking:
    """Update booking status."""
    booking = await get_booking_by_id(db, booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )
        
    booking.status = status_data.status
    
    await db.commit()
    await db.refresh(booking)
    return booking


async def update_booking_payment(
    db: AsyncSession, booking_id: str, payment_data: BookingPaymentUpdate
) -> Booking:
    """Update booking payment information."""
    booking = await get_booking_by_id(db, booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )
        
    booking.paid_amount = payment_data.paid_amount
    booking.payment_status = payment_data.payment_status
    
    # Calculate due amount safely, avoiding negative dues
    due = booking.total_fee - booking.paid_amount
    booking.due_amount = due if due > 0 else 0.0
    
    await db.commit()
    await db.refresh(booking)
    return booking
