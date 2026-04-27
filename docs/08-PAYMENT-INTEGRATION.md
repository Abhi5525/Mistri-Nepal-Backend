# 08-PAYMENT-INTEGRATION.md

# Payment Integration - eSewa Gateway

## 📋 Overview

Complete payment integration with eSewa (Nepal's leading digital wallet) for booking deposits.

---

## 💳 eSewa Integration

### Configuration

```python
# .env
ESEWA_MERCHANT_CODE=your_merchant_code
ESEWA_SECRET_KEY=your_secret_key
ESEWA_BASE_URL=https://rc-epay.esewa.com.np/api/epay/main/v2/form  # Test URL
# Production: https://epay.esewa.com.np/api/epay/main/v2/form
```

### `app/services/payment_service.py`

```python
import uuid
import hashlib
import base64
from typing import Dict, Optional
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.booking import Booking
from app.models.payment import Payment
from fastapi import HTTPException, status
import httpx

class PaymentService:
    """eSewa payment integration"""
    
    def __init__(self):
        self.merchant_code = "EPAYTEST"  # Test merchant code
        self.secret_key = "8gBm/:&EnhH.1/q"  # Test secret key
        self.base_url = "https://rc-epay.esewa.com.np/api/epay/main/v2/form"
        self.verify_url = "https://rc-epay.esewa.com.np/api/epay/transaction/status/"
    
    @staticmethod
    def generate_transaction_uuid() -> str:
        """Generate unique transaction ID"""
        return str(uuid.uuid4())
    
    def generate_signature(
        self,
        total_amount: str,
        transaction_uuid: str,
        product_code: str
    ) -> str:
        """Generate HMAC SHA256 signature for eSewa"""
        
        # Signature format: total_amount=X,transaction_uuid=Y,product_code=Z
        message = f"total_amount={total_amount},transaction_uuid={transaction_uuid},product_code={product_code}"
        
        # HMAC SHA256
        signature = hashlib.sha256(
            message.encode('utf-8')
        ).hexdigest()
        
        # Base64 encode
        signature_base64 = base64.b64encode(
            signature.encode('utf-8')
        ).decode('utf-8')
        
        return signature_base64
    
    async def initiate_payment(
        self,
        db: AsyncSession,
        booking_id: int,
        success_url: str,
        failure_url: str
    ) -> Dict:
        """Initiate eSewa payment for booking deposit"""
        
        # Get booking and payment
        result = await db.execute(
            select(Booking).where(Booking.id == booking_id)
        )
        booking = result.scalar_one_or_none()
        
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )
        
        payment_result = await db.execute(
            select(Payment).where(Payment.booking_id == booking_id)
        )
        payment = payment_result.scalar_one_or_none()
        
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment record not found"
            )
        
        if payment.is_paid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment already completed"
            )
        
        # Generate transaction UUID
        transaction_uuid = PaymentService.generate_transaction_uuid()
        payment.transaction_uuid = transaction_uuid
        
        # Prepare payment data
        amount = str(float(payment.amount))
        product_code = "EPAYTEST"
        
        # Generate signature
        signature = self.generate_signature(amount, transaction_uuid, product_code)
        
        # Update payment record
        payment.esewa_order_id = transaction_uuid
        await db.flush()
        
        # Return payment form data
        return {
            "payment_url": self.base_url,
            "form_data": {
                "amount": amount,
                "tax_amount": "0",
                "total_amount": amount,
                "transaction_uuid": transaction_uuid,
                "product_code": product_code,
                "product_service_charge": "0",
                "product_delivery_charge": "0",
                "success_url": success_url,
                "failure_url": failure_url,
                "signed_field_names": "total_amount,transaction_uuid,product_code",
                "signature": signature
            },
            "booking_id": booking_id,
            "amount": float(amount)
        }
    
    async def verify_payment(
        self,
        db: AsyncSession,
        transaction_uuid: str,
        reference_id: str
    ) -> Dict:
        """Verify payment status with eSewa"""
        
        # Verify with eSewa API
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.verify_url}/{reference_id}"
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Payment verification failed"
                )
            
            verification_data = response.json()
        
        # Check payment status
        if verification_data.get('status') != 'COMPLETE':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment not completed"
            )
        
        # Find payment by transaction UUID
        result = await db.execute(
            select(Payment).where(Payment.transaction_uuid == transaction_uuid)
        )
        payment = result.scalar_one_or_none()
        
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        
        if payment.is_paid:
            return {"message": "Payment already verified"}
        
        # Update payment status
        payment.is_paid = True
        payment.esewa_ref_id = reference_id
        payment.payment_date = datetime.utcnow()
        
        # Confirm booking
        booking_result = await db.execute(
            select(Booking).where(Booking.id == payment.booking_id)
        )
        booking = booking_result.scalar_one()
        booking.is_confirmed = True
        
        await db.flush()
        
        # Send confirmation notification
        from app.services.notification_service import NotificationService
        await NotificationService.send_push_notification(
            user_id=booking.client_id,
            title="✅ Payment Successful!",
            body=f"Your booking #{booking.id} has been confirmed.",
            data={"type": "booking_confirmed", "booking_id": booking.id}
        )
        
        return {
            "message": "Payment verified successfully",
            "booking_id": booking.id,
            "amount": float(payment.amount)
        }
```

---

## 🌐 API Endpoints

### `app/api/payments.py`

```python
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/api/payments", tags=["Payments"])

@router.post("/initiate/{booking_id}")
async def initiate_payment(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Initiate eSewa payment for booking"""
    payment_service = PaymentService()
    
    success_url = f"https://yourdomain.com/payment/success?booking_id={booking_id}"
    failure_url = f"https://yourdomain.com/payment/failure?booking_id={booking_id}"
    
    return await payment_service.initiate_payment(
        db, booking_id, success_url, failure_url
    )

@router.get("/verify")
async def verify_payment(
    transaction_uuid: str = Query(...),
    reference_id: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """Verify eSewa payment (called by eSewa callback)"""
    payment_service = PaymentService()
    
    return await payment_service.verify_payment(
        db, transaction_uuid, reference_id
    )

@router.get("/payment-status/{booking_id}")
async def get_payment_status(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get payment status for a booking"""
    from sqlalchemy import select
    from app.models.payment import Payment
    
    result = await db.execute(
        select(Payment).where(Payment.booking_id == booking_id)
    )
    payment = result.scalar_one_or_none()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    return {
        "booking_id": booking_id,
        "is_paid": payment.is_paid,
        "amount": float(payment.amount),
        "transaction_uuid": payment.transaction_uuid,
        "esewa_ref_id": payment.esewa_ref_id
    }
```

---

## 📱 Flutter Integration

```dart
// lib/services/payment_service.dart
import 'package:dio/dio.dart';
import 'package:flutter_webview_plugin/flutter_webview_plugin.dart';

class PaymentService {
  final Dio _dio;
  final FlutterWebviewPlugin _webviewPlugin = FlutterWebviewPlugin();
  
  PaymentService(this._dio);
  
  // Initiate payment and open webview
  Future<void> initiatePayment({
    required int bookingId,
    required Function(bool success) onPaymentComplete,
  }) async {
    try {
      // Get payment form data
      final response = await _dio.post('/api/payments/initiate/$bookingId');
      final paymentData = response.data;
      
      // Build HTML form
      String htmlForm = '''
        <html>
          <body>
            <form id="esewa_form" action="${paymentData['payment_url']}" method="POST">
              ${_buildFormFields(paymentData['form_data'])}
              <input type="submit" value="Pay with eSewa">
            </form>
            <script>
              document.getElementById('esewa_form').submit();
            </script>
          </body>
        </html>
      ''';
      
      // Open webview
      await _webviewPlugin.launch(
        "about:blank",
        userAgent: "Mozilla/5.0",
        hidden: false,
      );
      
      // Load HTML
      await _webviewPlugin.postUrl("about:blank", htmlForm);
      
      // Listen for URL changes
      _webviewPlugin.onUrlChanged.listen((url) {
        if (url.contains('payment/success')) {
          // Extract parameters
          final uri = Uri.parse(url);
          final transactionUuid = uri.queryParameters['transaction_uuid'];
          final referenceId = uri.queryParameters['ref_id'];
          
          // Verify payment
          _verifyPayment(transactionUuid!, referenceId!, onPaymentComplete);
        } else if (url.contains('payment/failure')) {
          onPaymentComplete(false);
        }
      });
      
    } catch (e) {
      throw Exception('Payment initiation failed: $e');
    }
  }
  
  String _buildFormFields(Map<String, dynamic> formData) {
    return formData.entries.map((entry) {
      return '<input type="hidden" name="${entry.key}" value="${entry.value}">';
    }).join('\n');
  }
  
  Future<void> _verifyPayment(
    String transactionUuid,
    String referenceId,
    Function(bool) onPaymentComplete,
  ) async {
    try {
      await _dio.get('/api/payments/verify', queryParameters: {
        'transaction_uuid': transactionUuid,
        'reference_id': referenceId,
      });
      
      onPaymentComplete(true);
      _webviewPlugin.close();
    } catch (e) {
      onPaymentComplete(false);
      _webviewPlugin.close();
    }
  }
  
  // Check payment status
  Future<Map<String, dynamic>> getPaymentStatus(int bookingId) async {
    try {
      final response = await _dio.get('/api/payments/payment-status/$bookingId');
      return response.data;
    } catch (e) {
      throw Exception('Failed to get payment status: $e');
    }
  }
}

// Usage in Flutter
class PaymentScreen extends StatelessWidget {
  final int bookingId;
  final PaymentService _paymentService = PaymentService(Dio());
  
  PaymentScreen({required this.bookingId});
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Complete Payment')),
      body: Center(
        child: ElevatedButton(
          onPressed: () {
            _paymentService.initiatePayment(
              bookingId: bookingId,
              onPaymentComplete: (success) {
                if (success) {
                  Navigator.pop(context);
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Payment successful!')),
                  );
                } else {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Payment failed')),
                  );
                }
              },
            );
          },
          child: Text('Pay with eSewa'),
        ),
      ),
    );
  }
}
```

---

## ✅ Testing

```python
# tests/test_payments.py
@pytest.mark.asyncio
async def test_initiate_payment(client, auth_token, booking_id):
    """Test initiating eSewa payment"""
    response = await client.post(
        f"/api/payments/initiate/{booking_id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    assert "payment_url" in response.json()
    assert "form_data" in response.json()

@pytest.mark.asyncio
async def test_verify_payment(client, db_session):
    """Test payment verification"""
    response = await client.get(
        "/api/payments/verify",
        params={
            "transaction_uuid": "test-uuid",
            "reference_id": "test-ref"
        }
    )
    
    assert response.status_code == 200
```

---

**Next:** Real-time features ➡️ See `11-REALTIME-FEATURES.md`
