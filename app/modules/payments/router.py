from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Union

from app.core.db.database import get_db
from app.core.security.security import get_current_user
from app.modules.auth.schemas import JwtPayload
from app.modules.payments import service
from app.modules.payments.schemas import (
    PaymentInitiateRequest,
    PaymentVerifyRequest,
    PaymentVerifyResponse,
    EsewaInitiateResponse,
    KhaltiInitiateResponse
)

payment_router = APIRouter(prefix="/payments", tags=["Payments"])


@payment_router.post("/initiate", response_model=Union[EsewaInitiateResponse, KhaltiInitiateResponse])
async def initiate_payment(
    data: PaymentInitiateRequest,
    current_user: JwtPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Initiates a payment for a specific booking.
    Returns the required payload/url for the mobile SDK to open the payment method.
    """
    return await service.initiate_payment(
        db=db,
        user_id=current_user.sub,
        booking_id=data.booking_id,
        payment_method=data.payment_method,
        payment_type=data.payment_type
    )


@payment_router.post("/verify", response_model=PaymentVerifyResponse)
async def verify_payment(
    data: PaymentVerifyRequest,
    current_user: JwtPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Verifies a payment after the mobile SDK returns success.
    - For Khalti, send the `pidx`
    - For eSewa, send the base64 encoded `esewa_data` returned by the SDK.
    """
    return await service.verify_payment(
        db=db,
        booking_id=data.booking_id,
        payment_method=data.payment_method,
        pidx=data.pidx,
        esewa_data=data.esewa_data
    )
