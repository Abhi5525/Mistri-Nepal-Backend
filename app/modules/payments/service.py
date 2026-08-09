import base64
import hashlib
import hmac
import json
import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Union

from app.core.config.config import settings
from app.core.utils.string_utils import StringUtils
from app.modules.booking.models import Booking
from app.common.enum.booking_payment_status_enum import PaymentStatusEnum
from app.common.enum.booking_status_enum import BookingStatusEnum
from app.common.enum.payment_method_enum import PaymentMethodEnum
from app.common.enum.payment_transaction_status_enum import PaymentTransactionStatusEnum
from app.common.enum.payment_type_enum import PaymentTypeEnum
from app.modules.payments.models import Payment
from app.modules.payments.schemas import EsewaInitiateResponse, KhaltiInitiateResponse


def generate_esewa_signature(secret_key: str, message: str) -> str:
    """Generate HMAC SHA256 signature for eSewa v2."""
    key = secret_key.encode("utf-8")
    msg = message.encode("utf-8")
    hmac_obj = hmac.new(key, msg, hashlib.sha256)
    return base64.b64encode(hmac_obj.digest()).decode("utf-8")


async def initiate_payment(
    db: AsyncSession, user_id: str, booking_id: str, payment_method: PaymentMethodEnum, payment_type: PaymentTypeEnum
) -> Union[EsewaInitiateResponse, KhaltiInitiateResponse]:
    """Initiate payment for a booking with the chosen payment method."""
    
    # Verify booking
    result = await db.execute(select(Booking).where(Booking.booking_id == booking_id))
    booking = result.scalars().first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")
    
    if booking.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized.")
        
    if booking.payment_status == PaymentStatusEnum.PAID:
        raise HTTPException(status_code=400, detail="Booking is already paid.")

    # Depending on payment_type, we decide how much to charge.
    # Currently assuming due_amount
    amount_to_pay = booking.due_amount
    if payment_type == PaymentTypeEnum.BOOKING_ADVANCE:
        # e.g., 10% advance
        amount_to_pay = booking.total_fee * 0.10
    
    if amount_to_pay <= 0:
        raise HTTPException(status_code=400, detail="No due amount to pay.")

    # Create Payment Record
    txn_id = "PAY_" + StringUtils.randomAlphaNumeric(10)
    payment_record = Payment(
        payment_id=txn_id,
        booking_id=booking_id,
        user_id=user_id,
        amount=amount_to_pay,
        payment_method=payment_method,
        payment_type=payment_type,
        status=PaymentTransactionStatusEnum.PENDING
    )
    db.add(payment_record)
    await db.commit()

    if payment_method == PaymentMethodEnum.ESEWA:
        # eSewa v2 requirements
        total_amount = amount_to_pay
        transaction_uuid = txn_id
        product_code = settings.ESEWA_MERCHANT_CODE
        signed_field_names = "total_amount,transaction_uuid,product_code"
        message = f"total_amount={total_amount},transaction_uuid={transaction_uuid},product_code={product_code}"
        
        signature = generate_esewa_signature(settings.ESEWA_SECRET_KEY, message)
        
        return EsewaInitiateResponse(
            amount=amount_to_pay,
            tax_amount=0.0,
            total_amount=total_amount,
            transaction_uuid=transaction_uuid,
            product_code=product_code,
            product_service_charge=0.0,
            product_delivery_charge=0.0,
            success_url="https://yourdomain.com/success", # Dummy, mobile SDK handles this usually
            failure_url="https://yourdomain.com/failure",
            signed_field_names=signed_field_names,
            signature=signature
        )

    elif payment_method == PaymentMethodEnum.KHALTI:
        # Khalti API Call
        url = f"{settings.KHALTI_BASE_URL}/epayment/initiate/"
        payload = {
            "return_url": "https://yourdomain.com/success",
            "website_url": "https://yourdomain.com",
            "amount": int(amount_to_pay * 100), # Khalti takes paisa
            "purchase_order_id": txn_id,
            "purchase_order_name": f"Booking {booking_id}",
            "customer_info": {
                "name": "Customer",
                "email": "customer@example.com",
                "phone": "9800000000"
            }
        }
        headers = {
            "Authorization": f"key {settings.KHALTI_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to initiate Khalti payment.")
            
        data = response.json()
        
        # Save pidx to txn
        payment_record.gateway_reference_id = data.get("pidx")
        await db.commit()
        
        return KhaltiInitiateResponse(
            pidx=data.get("pidx"),
            payment_url=data.get("payment_url"),
            expires_at=data.get("expires_at"),
            expires_in=data.get("expires_in")
        )


async def verify_payment(
    db: AsyncSession, booking_id: str, payment_method: PaymentMethodEnum, pidx: str = None, esewa_data: str = None
) -> dict:
    """Verify payment status with the gateway after frontend SDK returns success."""
    
    # 1. Fetch pending transaction for this booking
    result = await db.execute(
        select(Payment).where(
            Payment.booking_id == booking_id,
            Payment.payment_method == payment_method,
            Payment.status == PaymentTransactionStatusEnum.PENDING
        ).order_by(Payment.created_at.desc())
    )
    payment_record = result.scalars().first()
    if not payment_record:
        raise HTTPException(status_code=404, detail="No pending transaction found.")

    is_verified = False

    if payment_method == PaymentMethodEnum.KHALTI:
        if not pidx:
            raise HTTPException(status_code=400, detail="pidx is required for Khalti verification.")
            
        url = f"{settings.KHALTI_BASE_URL}/epayment/lookup/"
        payload = {"pidx": pidx}
        headers = {
            "Authorization": f"key {settings.KHALTI_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "Completed":
                is_verified = True

    elif payment_method == PaymentMethodEnum.ESEWA:
        if not esewa_data:
            raise HTTPException(status_code=400, detail="esewa_data (base64) is required.")
        
        # Decode base64 payload from eSewa
        try:
            decoded_bytes = base64.b64decode(esewa_data)
            payload_str = decoded_bytes.decode("utf-8")
            esewa_payload = json.loads(payload_str)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid eSewa data format.")
            
        # Verify transaction_uuid matches
        if esewa_payload.get("transaction_uuid") == payment_record.payment_id and esewa_payload.get("status") == "COMPLETE":
            is_verified = True

    if is_verified:
        # Mark txn as success
        payment_record.status = PaymentTransactionStatusEnum.SUCCESS
        
        # Update Booking
        booking_result = await db.execute(select(Booking).where(Booking.booking_id == booking_id))
        booking = booking_result.scalars().first()
        
        if payment_record.payment_type == PaymentTypeEnum.BOOKING_ADVANCE:
            booking.advance_fee += payment_record.amount
            
        booking.paid_amount += payment_record.amount
        booking.due_amount = booking.total_fee - booking.paid_amount
        if booking.due_amount <= 0:
            booking.payment_status = PaymentStatusEnum.PAID
            booking.due_amount = 0.0
        else:
            booking.payment_status = PaymentStatusEnum.PARTIAL
            
        booking.status = BookingStatusEnum.CONFIRMED # Usually payment confirms the booking
        
        await db.commit()
        return {"status": "success", "message": "Payment verified successfully."}
    else:
        payment_record.status = PaymentTransactionStatusEnum.FAILED
        await db.commit()
        raise HTTPException(status_code=400, detail="Payment verification failed.")
