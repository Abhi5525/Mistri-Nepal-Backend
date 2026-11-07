from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.database import get_db
from app.core.security.authorization import authorize
from app.core.security.security import get_current_user
from app.modules.auth.schemas import JwtPayload
from app.modules.booking import service
from app.modules.booking.schemas import (
    BookingCreateRequest,
    BookingListResponse,
    BookingPaymentUpdate,
    BookingResponse,
    BookingStatusUpdate,
)
from app.modules.professionals.service import get_professional_by_user_id

booking_router = APIRouter(prefix="/booking", tags=["Bookings"])


@booking_router.post("", response_model=BookingResponse)
async def create_booking(
    data: BookingCreateRequest,
    current_user: JwtPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _=Depends(authorize)
):
    """Create a new booking."""
    return await service.create_booking(db, user_id=current_user.sub, data=data)


@booking_router.get("/me", response_model=BookingListResponse)
async def get_my_bookings(
    skip: int = 0,
    limit: int = 10,
    current_user: JwtPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _=Depends(authorize)
):
    """Get all bookings made by the current user."""
    bookings, total = await service.get_user_bookings(
        db, user_id=current_user.sub, skip=skip, limit=limit
    )
    return {"data": bookings, "total_count": total}


@booking_router.get("/professional/me", response_model=BookingListResponse)
async def get_my_professional_bookings(
    skip: int = 0,
    limit: int = 10,
    current_user: JwtPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _=Depends(authorize)
):
    """Get all bookings received by the current professional."""
    # First, get the professional profile of the logged in user
    professional = await get_professional_by_user_id(db, user_id=current_user.sub)
    if not professional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professional profile not found for the current user",
        )

    bookings, total = await service.get_professional_bookings(
        db, professional_profile_id=professional.professional_profile_id, skip=skip, limit=limit
    )
    return {"data": bookings, "total_count": total}


@booking_router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: str,
    current_user: JwtPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get details of a specific booking."""
    booking = await service.get_booking_by_id(db, booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )
        
    # Optional: We could add authorization here to ensure only the customer or the professional can see the booking
    if booking.user_id != current_user.sub:
        professional = await get_professional_by_user_id(db, user_id=current_user.sub)
        if not professional or professional.professional_profile_id != booking.professional_profile_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this booking",
            )
            
    return booking


@booking_router.patch("/{booking_id}/status", response_model=BookingResponse)
async def update_status(
    booking_id: str,
    data: BookingStatusUpdate,
    current_user: JwtPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _=Depends(authorize)
):
    """Update the status of a booking."""
    # Authorization checks should ideally go here to verify only the professional/admin can update status
    return await service.update_booking_status(db, booking_id, data)


@booking_router.patch("/{booking_id}/payment", response_model=BookingResponse)
async def update_payment(
    booking_id: str,
    data: BookingPaymentUpdate,
    current_user: JwtPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _=Depends(authorize)
):
    """Update the payment details of a booking."""
    return await service.update_booking_payment(db, booking_id, data)
