from pydantic import BaseModel
from typing import Optional
from app.common.enum.payment_method_enum import PaymentMethodEnum
from app.common.enum.payment_type_enum import PaymentTypeEnum

class PaymentInitiateRequest(BaseModel):
    booking_id: str
    payment_method: PaymentMethodEnum
    payment_type: PaymentTypeEnum

class EsewaInitiateResponse(BaseModel):
    amount: float
    tax_amount: float
    total_amount: float
    transaction_uuid: str
    product_code: str
    product_service_charge: float
    product_delivery_charge: float
    success_url: str
    failure_url: str
    signed_field_names: str
    signature: str

class KhaltiInitiateResponse(BaseModel):
    pidx: str
    payment_url: str
    expires_at: str
    expires_in: int

class PaymentVerifyRequest(BaseModel):
    """Generic verification payload sent from frontend after SDK returns success."""
    payment_method: PaymentMethodEnum
    booking_id: str
    # Khalti sends pidx
    pidx: Optional[str] = None
    # eSewa sends encoded data
    esewa_data: Optional[str] = None

class PaymentVerifyResponse(BaseModel):
    status: str
    message: str
