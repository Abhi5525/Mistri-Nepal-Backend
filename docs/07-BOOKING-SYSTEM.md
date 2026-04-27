# 07-BOOKING-SYSTEM.md

# Booking System - Time Slots & Conflict Detection

## 📋 Overview

Complete booking management system with intelligent time slot generation, conflict detection, and automated scheduling.

---

## 🗄️ Database Models (Already Created)

See `02-DATABASE-SCHEMA.md` for complete booking table structure.

---

## ⏰ Time Slot Management Service

### `app/services/booking_service.py`

```python
from datetime import datetime, timedelta, date, time
from typing import List, Dict, Optional, Tuple
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from app.models.booking import Booking
from app.models.professional import ProfessionalProfile
from app.models.payment import Payment
from fastapi import HTTPException, status

class BookingService:
    """Booking management with time slot logic"""
    
    # Configuration
    BOOKING_START_HOUR = 6  # 6 AM
    BOOKING_END_HOUR = 20   # 8 PM
    MIN_DURATION_HOURS = 0.5
    MAX_DURATION_HOURS = 24
    BOOKING_GAP_MINUTES = 30  # Gap between bookings
    MIN_ADVANCE_MINUTES = 30  # Minimum advance booking time
    
    @staticmethod
    async def get_available_slots(
        db: AsyncSession,
        professional_id: int,
        selected_date: date,
        duration_hours: float
    ) -> List[Dict]:
        """
        Generate available time slots for a professional on a specific date
        Returns list of available start times
        """
        
        # Validate duration
        if duration_hours < BookingService.MIN_DURATION_HOURS or \
           duration_hours > BookingService.MAX_DURATION_HOURS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Duration must be between {BookingService.MIN_DURATION_HOURS} and {BookingService.MAX_DURATION_HOURS} hours"
            )
        
        # Get professional's existing bookings for the day
        day_start = datetime.combine(selected_date, time.min)
        day_end = datetime.combine(selected_date, time.max)
        
        result = await db.execute(
            select(Booking).where(
                and_(
                    Booking.professional_id == professional_id,
                    Booking.booking_time >= day_start,
                    Booking.booking_time <= day_end,
                    Booking.status.in_(['upcoming', 'ongoing'])
                )
            ).order_by(Booking.booking_time)
        )
        existing_bookings = result.scalars().all()
        
        # Generate all possible slots (every 30 minutes)
        available_slots = []
        current_time = datetime.combine(selected_date, time(BookingService.BOOKING_START_HOUR, 0))
        day_cutoff = datetime.combine(selected_date, time(BookingService.BOOKING_END_HOUR, 0))
        
        while current_time + timedelta(hours=duration_hours) <= day_cutoff:
            slot_end = current_time + timedelta(hours=duration_hours)
            
            # Check if slot conflicts with existing bookings (including gap)
            is_available = True
            
            for booking in existing_bookings:
                booking_end_with_gap = booking.end_time + timedelta(minutes=BookingService.BOOKING_GAP_MINUTES)
                
                # Check overlap
                if current_time < booking_end_with_gap and slot_end > booking.booking_time:
                    is_available = False
                    break
            
            # Check minimum advance time for today
            if selected_date == date.today():
                min_booking_time = datetime.now() + timedelta(minutes=BookingService.MIN_ADVANCE_MINUTES)
                if current_time < min_booking_time:
                    is_available = False
            
            if is_available:
                available_slots.append({
                    "start_time": current_time.strftime("%H:%M"),
                    "end_time": slot_end.strftime("%H:%M"),
                    "display": f"{current_time.strftime('%I:%M %p')} - {slot_end.strftime('%I:%M %p')}"
                })
            
            # Move to next 30-minute slot
            current_time += timedelta(minutes=30)
        
        return available_slots
    
    @staticmethod
    async def check_availability(
        db: AsyncSession,
        professional_id: int,
        booking_time: datetime,
        duration_hours: float
    ) -> bool:
        """
        Check if professional is available at specific time
        Returns True if available, False if booked
        """
        
        end_time = booking_time + timedelta(hours=duration_hours)
        
        # Check for overlapping bookings (with gap)
        result = await db.execute(
            select(func.count()).select_from(Booking).where(
                and_(
                    Booking.professional_id == professional_id,
                    Booking.status.in_(['upcoming', 'ongoing']),
                    or_(
                        # New booking starts during existing booking
                        and_(
                            Booking.booking_time <= booking_time,
                            Booking.end_time > booking_time
                        ),
                        # New booking ends during existing booking
                        and_(
                            Booking.booking_time < end_time,
                            Booking.end_time >= end_time
                        ),
                        # New booking completely contains existing booking
                        and_(
                            Booking.booking_time >= booking_time,
                            Booking.end_time <= end_time
                        )
                    )
                )
            )
        )
        
        conflict_count = result.scalar()
        return conflict_count == 0
    
    @staticmethod
    async def create_booking(
        db: AsyncSession,
        client_id: int,
        professional_id: int,
        booking_time: datetime,
        duration_hours: float,
        client_name: str,
        client_phone: str,
        user_latitude: float,
        user_longitude: float
    ) -> Dict:
        """Create a new booking with validation"""
        
        # Validate professional exists and is approved
        prof_result = await db.execute(
            select(ProfessionalProfile).where(ProfessionalProfile.id == professional_id)
        )
        professional = prof_result.scalar_one_or_none()
        
        if not professional:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Professional not found"
            )
        
        if professional.verification_status != 'APPROVED':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Professional is not approved for bookings"
            )
        
        if not professional.is_available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Professional is currently unavailable"
            )
        
        # Check availability
        is_available = await BookingService.check_availability(
            db, professional_id, booking_time, duration_hours
        )
        
        if not is_available:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Time slot is already booked"
            )
        
        # Validate booking time
        if booking_time.hour < BookingService.BOOKING_START_HOUR or \
           booking_time.hour >= BookingService.BOOKING_END_HOUR:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bookings allowed only between {BookingService.BOOKING_START_HOUR}:00 AM and {BookingService.BOOKING_END_HOUR}:00 PM"
            )
        
        # Calculate end time
        end_time = booking_time + timedelta(hours=duration_hours)
        
        # Calculate fees
        total_fee = Decimal(str(professional.rate)) * Decimal(str(duration_hours))
        deposit_amount = total_fee * Decimal('0.10')  # 10% deposit
        
        total_fee = total_fee.quantize(Decimal('0.01'))
        deposit_amount = deposit_amount.quantize(Decimal('0.01'))
        
        # Create booking
        booking = Booking(
            client_id=client_id,
            client_name=client_name,
            client_phone=client_phone,
            professional_id=professional_id,
            booking_time=booking_time,
            end_time=end_time,
            duration_hours=duration_hours,
            total_fee=total_fee,
            deposit_amount=deposit_amount,
            user_latitude=user_latitude,
            user_longitude=user_longitude,
            professional_latitude=professional.latitude,
            professional_longitude=professional.longitude,
            status='upcoming',
            is_confirmed=False
        )
        
        db.add(booking)
        await db.flush()
        await db.refresh(booking)
        
        # Create payment record
        payment = Payment(
            booking_id=booking.id,
            amount=deposit_amount,
            is_paid=False
        )
        
        db.add(payment)
        await db.flush()
        
        return {
            "booking": booking,
            "payment": payment,
            "total_fee": float(total_fee),
            "deposit_amount": float(deposit_amount),
            "remaining_payment": float(total_fee - deposit_amount)
        }
    
    @staticmethod
    async def confirm_booking(db: AsyncSession, booking_id: int) -> dict:
        """Confirm booking after successful payment"""
        
        result = await db.execute(
            select(Booking).where(Booking.id == booking_id)
        )
        booking = result.scalar_one_or_none()
        
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )
        
        booking.is_confirmed = True
        await db.flush()
        
        return {"message": "Booking confirmed", "booking_id": booking_id}
    
    @staticmethod
    async def cancel_booking(db: AsyncSession, booking_id: int, user_id: int) -> dict:
        """Cancel booking (with refund logic)"""
        
        result = await db.execute(
            select(Booking).where(Booking.id == booking_id)
        )
        booking = result.scalar_one_or_none()
        
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )
        
        # Only client or admin can cancel
        if booking.client_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to cancel this booking"
            )
        
        if booking.status == 'completed':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel completed booking"
            )
        
        booking.status = 'cancelled'
        await db.flush()
        
        # Process refund if payment was made
        if booking.is_confirmed:
            # Refund logic here
            pass
        
        return {"message": "Booking cancelled", "booking_id": booking_id}
    
    @staticmethod
    async def mark_booking_completed(db: AsyncSession, booking_id: int, professional_user_id: int) -> dict:
        """Mark booking as completed (by professional)"""
        
        result = await db.execute(
            select(Booking).where(Booking.id == booking_id)
        )
        booking = result.scalar_one_or_none()
        
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )
        
        # Verify professional owns this booking
        prof_result = await db.execute(
            select(ProfessionalProfile).where(ProfessionalProfile.user_id == professional_user_id)
        )
        profile = prof_result.scalar_one_or_none()
        
        if not profile or profile.id != booking.professional_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized"
            )
        
        now = datetime.utcnow()
        
        # Can only complete current or past bookings
        if booking.booking_time > now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot complete future booking"
            )
        
        booking.end_time = now
        booking.status = 'completed'
        await db.flush()
        
        return {"message": "Booking completed", "booking_id": booking_id}
    
    @staticmethod
    async def get_user_bookings(
        db: AsyncSession,
        user_id: int,
        is_client: bool = True,
        status_filter: Optional[str] = None
    ) -> List[Dict]:
        """Get bookings for user (client or professional)"""
        
        query = select(Booking)
        
        if is_client:
            query = query.where(Booking.client_id == user_id)
        else:
            # Get professional ID
            prof_result = await db.execute(
                select(ProfessionalProfile).where(ProfessionalProfile.user_id == user_id)
            )
            profile = prof_result.scalar_one_or_none()
            
            if not profile:
                return []
            
            query = query.where(Booking.professional_id == profile.id)
        
        # Apply status filter
        if status_filter:
            query = query.where(Booking.status == status_filter)
        
        query = query.order_by(Booking.booking_time.desc())
        
        result = await db.execute(query)
        bookings = result.scalars().all()
        
        # Format response
        booking_list = []
        for booking in bookings:
            booking_list.append({
                "id": booking.id,
                "booking_time": booking.booking_time.isoformat(),
                "end_time": booking.end_time.isoformat(),
                "duration_hours": booking.duration_hours,
                "total_fee": float(booking.total_fee),
                "deposit_amount": float(booking.deposit_amount),
                "status": booking.status,
                "is_confirmed": booking.is_confirmed,
                "client_name": booking.client_name,
                "client_phone": booking.client_phone
            })
        
        return booking_list
```

---

## 🌐 API Endpoints

### `app/api/bookings.py`

```python
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, datetime
from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.booking_service import BookingService
from pydantic import BaseModel

router = APIRouter(prefix="/api/bookings", tags=["Bookings"])

class CreateBookingRequest(BaseModel):
    professional_id: int
    booking_time: datetime
    duration_hours: float
    client_name: str
    client_phone: str
    latitude: float
    longitude: float

@router.get("/available-slots/{professional_id}")
async def get_available_slots(
    professional_id: int,
    date_str: str = Query(..., description="Date in YYYY-MM-DD format"),
    duration_hours: float = Query(1.0, ge=0.5, le=24),
    db: AsyncSession = Depends(get_db)
):
    """Get available time slots for a professional"""
    try:
        selected_date = date.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    
    slots = await BookingService.get_available_slots(
        db, professional_id, selected_date, duration_hours
    )
    
    return {
        "date": date_str,
        "duration_hours": duration_hours,
        "available_slots": slots
    }

@router.post("/create", status_code=201)
async def create_booking(
    booking_data: CreateBookingRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new booking"""
    result = await BookingService.create_booking(
        db,
        current_user.id,
        booking_data.professional_id,
        booking_data.booking_time,
        booking_data.duration_hours,
        booking_data.client_name,
        booking_data.client_phone,
        booking_data.latitude,
        booking_data.longitude
    )
    
    return result

@router.post("/{booking_id}/confirm")
async def confirm_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Confirm booking after payment"""
    return await BookingService.confirm_booking(db, booking_id)

@router.post("/{booking_id}/cancel")
async def cancel_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel a booking"""
    return await BookingService.cancel_booking(db, booking_id, current_user.id)

@router.post("/{booking_id}/complete")
async def complete_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark booking as completed (professional only)"""
    return await BookingService.mark_booking_completed(
        db, booking_id, current_user.id
    )

@router.get("/my-bookings")
async def get_my_bookings(
    status: str = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's bookings"""
    bookings = await BookingService.get_user_bookings(
        db, current_user.id, 
        is_client=current_user.is_client,
        status_filter=status
    )
    
    return {"bookings": bookings}
```

---

## 📱 Flutter Integration

```dart
// lib/services/booking_service.dart
import 'package:dio/dio.dart';

class BookingService {
  final Dio _dio;
  
  BookingService(this._dio);
  
  // Get available time slots
  Future<List<dynamic>> getAvailableSlots({
    required int professionalId,
    required String date,
    double durationHours = 1.0,
  }) async {
    try {
      final response = await _dio.get(
        '/api/bookings/available-slots/$professionalId',
        queryParameters: {
          'date_str': date,
          'duration_hours': durationHours,
        },
      );
      
      return response.data['available_slots'];
    } catch (e) {
      throw Exception('Failed to load slots: $e');
    }
  }
  
  // Create booking
  Future<Map<String, dynamic>> createBooking({
    required int professionalId,
    required DateTime bookingTime,
    required double durationHours,
    required String clientName,
    required String clientPhone,
    required double latitude,
    required double longitude,
  }) async {
    try {
      final response = await _dio.post('/api/bookings/create', data: {
        'professional_id': professionalId,
        'booking_time': bookingTime.toIso8601String(),
        'duration_hours': durationHours,
        'client_name': clientName,
        'client_phone': clientPhone,
        'latitude': latitude,
        'longitude': longitude,
      });
      
      return response.data;
    } catch (e) {
      throw Exception('Booking failed: $e');
    }
  }
  
  // Get my bookings
  Future<List<dynamic>> getMyBookings({String? status}) async {
    try {
      final response = await _dio.get(
        '/api/bookings/my-bookings',
        queryParameters: if (status != null) {'status': status},
      );
      
      return response.data['bookings'];
    } catch (e) {
      throw Exception('Failed to load bookings: $e');
    }
  }
  
  // Cancel booking
  Future<void> cancelBooking(int bookingId) async {
    try {
      await _dio.post('/api/bookings/$bookingId/cancel');
    } catch (e) {
      throw Exception('Cancellation failed: $e');
    }
  }
}

// Usage: Booking screen
class BookingScreen extends StatefulWidget {
  final int professionalId;
  
  BookingScreen({required this.professionalId});
  
  @override
  _BookingScreenState createState() => _BookingScreenState();
}

class _BookingScreenState extends State<BookingScreen> {
  final BookingService _bookingService = BookingService(Dio());
  List<dynamic> _availableSlots = [];
  DateTime? _selectedDate;
  
  @override
  void initState() {
    super.initState();
    _selectedDate = DateTime.now();
    _loadSlots();
  }
  
  Future<void> _loadSlots() async {
    if (_selectedDate == null) return;
    
    try {
      final slots = await _bookingService.getAvailableSlots(
        professionalId: widget.professionalId,
        date: _selectedDate!.toIso8601String().split('T')[0],
        durationHours: 1.0,
      );
      
      setState(() {
        _availableSlots = slots;
      });
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString())),
      );
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Book Service')),
      body: Column(
        children: [
          // Date picker
          CalendarDatePicker(
            initialDate: _selectedDate!,
            firstDate: DateTime.now(),
            lastDate: DateTime.now().add(Duration(days: 30)),
            onDateChanged: (date) {
              setState(() {
                _selectedDate = date;
              });
              _loadSlots();
            },
          ),
          
          // Available slots
          Expanded(
            child: ListView.builder(
              itemCount: _availableSlots.length,
              itemBuilder: (context, index) {
                final slot = _availableSlots[index];
                return ListTile(
                  title: Text(slot['display']),
                  onTap: () {
                    // Book this slot
                    _bookSlot(slot);
                  },
                );
              },
            ),
          ),
        ],
      ),
    );
  }
  
  Future<void> _bookSlot(Map<String, dynamic> slot) async {
    // Show confirmation dialog and proceed with booking
  }
}
```

---

## ✅ Testing

```python
# tests/test_bookings.py
@pytest.mark.asyncio
async def test_get_available_slots(client):
    """Test getting available time slots"""
    response = await client.get(
        "/api/bookings/available-slots/1",
        params={
            "date_str": "2024-01-15",
            "duration_hours": 1.0
        }
    )
    
    assert response.status_code == 200
    assert "available_slots" in response.json()

@pytest.mark.asyncio
async def test_create_booking(client, auth_token):
    """Test creating a booking"""
    booking_data = {
        "professional_id": 1,
        "booking_time": "2024-01-15T10:00:00",
        "duration_hours": 1.0,
        "client_name": "Test User",
        "client_phone": "9812345678",
        "latitude": 27.7172,
        "longitude": 85.3240
    }
    
    response = await client.post(
        "/api/bookings/create",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=booking_data
    )
    
    assert response.status_code == 201
    assert "booking" in response.json()
    assert "payment" in response.json()

@pytest.mark.asyncio
async def test_booking_conflict(client, auth_token):
    """Test that conflicting bookings are rejected"""
    # First booking
    await client.post(
        "/api/bookings/create",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "professional_id": 1,
            "booking_time": "2024-01-15T10:00:00",
            "duration_hours": 1.0,
            "client_name": "User 1",
            "client_phone": "9812345678",
            "latitude": 27.7172,
            "longitude": 85.3240
        }
    )
    
    # Second booking (should fail - conflict)
    response = await client.post(
        "/api/bookings/create",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "professional_id": 1,
            "booking_time": "2024-01-15T10:30:00",  # Overlaps
            "duration_hours": 1.0,
            "client_name": "User 2",
            "client_phone": "9812345679",
            "latitude": 27.7172,
            "longitude": 85.3240
        }
    )
    
    assert response.status_code == 409  # Conflict
```

---

## 🔧 Advanced Features

### Smart Scheduling Suggestions

```python
async def suggest_best_slots(
    db: AsyncSession,
    professional_id: int,
    preferred_date: date,
    duration_hours: float
) -> List[Dict]:
    """
    AI-powered slot suggestions based on:
    - Historical booking patterns
    - Professional preferences
    - Client convenience
    """
    
    available = await BookingService.get_available_slots(
        db, professional_id, preferred_date, duration_hours
    )
    
    # Score each slot
    scored_slots = []
    for slot in available:
        score = 100
        
        # Prefer mid-day slots (10 AM - 4 PM)
        hour = int(slot['start_time'].split(':')[0])
        if 10 <= hour <= 16:
            score += 10
        
        # Avoid early morning and late evening
        if hour < 8 or hour > 18:
            score -= 15
        
        scored_slots.append({**slot, 'score': score})
    
    # Sort by score and return top 5
    scored_slots.sort(key=lambda x: x['score'], reverse=True)
    return scored_slots[:5]
```

---

**Next:** Payment integration ➡️ See `08-PAYMENT-INTEGRATION.md`
