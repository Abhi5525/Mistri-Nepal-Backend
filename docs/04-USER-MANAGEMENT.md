# 04-USER-MANAGEMENT.md

# User Management - CRUD Operations

## 📋 Overview

Complete user profile management system with update, view, and account management features.

---

## 📝 Pydantic Schemas

### `app/schemas/user.py`

```python
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional

class UserProfileUpdate(BaseModel):
    """Schema for updating user profile"""
    full_name: Optional[str] = Field(None, min_length=3, max_length=100)
    phone_number: Optional[str] = Field(None, min_length=10, max_length=10)
    email: Optional[EmailStr] = None
    
    @validator('phone_number')
    def validate_phone(cls, v):
        if v:
            import re
            pattern = r'^98\d{8}$'
            if not re.match(pattern, v):
                raise ValueError('Phone number must be 10 digits starting with 98')
        return v

class UserProfileResponse(BaseModel):
    """Complete user profile response"""
    id: int
    phone_number: str
    full_name: str
    email: Optional[str] = None
    is_client: bool
    is_professional: bool
    is_active: bool
    created_at: Optional[str] = None
    
    class Config:
        from_attributes = True

class UserStatsResponse(BaseModel):
    """User statistics (for professionals)"""
    total_bookings: int = 0
    completed_bookings: int = 0
    upcoming_bookings: int = 0
    average_rating: float = 0.0
    total_reviews: int = 0
    total_earnings: float = 0.0
```

---

## 🔧 User Service

### `app/services/user_service.py`

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.user import User
from app.models.professional import ProfessionalProfile
from app.models.booking import Booking
from app.schemas.user import UserProfileUpdate
from fastapi import HTTPException, status

class UserService:
    """User management service"""
    
    @staticmethod
    async def get_user_profile(db: AsyncSession, user_id: int) -> dict:
        """Get complete user profile with stats"""
        
        # Fetch user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get professional stats if applicable
        stats = {}
        if user.is_professional:
            prof_result = await db.execute(
                select(ProfessionalProfile).where(ProfessionalProfile.user_id == user_id)
            )
            profile = prof_result.scalar_one_or_none()
            
            if profile:
                # Calculate booking stats
                total_bookings = await db.execute(
                    select(func.count()).select_from(Booking).where(
                        Booking.professional_id == profile.id
                    )
                )
                
                completed = await db.execute(
                    select(func.count()).select_from(Booking).where(
                        (Booking.professional_id == profile.id) &
                        (Booking.status == 'completed')
                    )
                )
                
                upcoming = await db.execute(
                    select(func.count()).select_from(Booking).where(
                        (Booking.professional_id == profile.id) &
                        (Booking.status.in_(['upcoming', 'ongoing']))
                    )
                )
                
                # Calculate earnings
                earnings_result = await db.execute(
                    select(func.sum(Booking.total_fee)).where(
                        (Booking.professional_id == profile.id) &
                        (Booking.status == 'completed')
                    )
                )
                total_earnings = earnings_result.scalar() or 0
                
                stats = {
                    "total_bookings": total_bookings.scalar(),
                    "completed_bookings": completed.scalar(),
                    "upcoming_bookings": upcoming.scalar(),
                    "average_rating": profile.average_rating,
                    "total_reviews": profile.total_reviews,
                    "total_earnings": float(total_earnings)
                }
        
        return {
            "user": user,
            "stats": stats
        }
    
    @staticmethod
    async def update_user_profile(
        db: AsyncSession,
        user_id: int,
        update_data: UserProfileUpdate
    ) -> User:
        """Update user profile with validation"""
        
        # Fetch user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update fields if provided
        update_dict = update_data.dict(exclude_unset=True)
        
        # Check phone uniqueness if changing
        if 'phone_number' in update_dict:
            new_phone = update_dict['phone_number']
            if new_phone != user.phone_number:
                existing = await db.execute(
                    select(User).where(
                        (User.phone_number == new_phone) &
                        (User.id != user_id)
                    )
                )
                if existing.scalar_one_or_none():
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Phone number already registered"
                    )
        
        # Check email uniqueness if changing
        if 'email' in update_dict and update_dict['email']:
            new_email = update_dict['email']
            if new_email != user.email:
                existing = await db.execute(
                    select(User).where(
                        (User.email == new_email) &
                        (User.id != user_id)
                    )
                )
                if existing.scalar_one_or_none():
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Email already registered"
                    )
        
        # Apply updates
        for field, value in update_dict.items():
            setattr(user, field, value)
        
        await db.flush()
        await db.refresh(user)
        
        return user
    
    @staticmethod
    async def deactivate_account(db: AsyncSession, user_id: int) -> dict:
        """Deactivate user account (soft delete)"""
        
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.is_active = False
        await db.flush()
        
        return {"message": "Account deactivated successfully"}
    
    @staticmethod
    async def delete_account(db: AsyncSession, user_id: int) -> dict:
        """Permanently delete user account (hard delete)"""
        
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if user has active bookings
        active_bookings = await db.execute(
            select(func.count()).select_from(Booking).where(
                (Booking.client_id == user_id) &
                (Booking.status.in_(['upcoming', 'ongoing']))
            )
        )
        
        if active_bookings.scalar() > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete account with active bookings"
            )
        
        await db.delete(user)
        await db.flush()
        
        return {"message": "Account deleted permanently"}
```

---

## 🌐 API Endpoints

### `app/api/users.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import (
    UserProfileUpdate, UserProfileResponse, UserStatsResponse
)
from app.services.user_service import UserService

router = APIRouter(prefix="/api/users", tags=["Users"])

@router.get("/profile", response_model=dict)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's complete profile with statistics"""
    return await UserService.get_user_profile(db, current_user.id)

@router.put("/profile", response_model=UserProfileResponse)
async def update_my_profile(
    update_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user's profile"""
    updated_user = await UserService.update_user_profile(
        db, current_user.id, update_data
    )
    return updated_user

@router.post("/deactivate")
async def deactivate_my_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Deactivate current user's account (soft delete)"""
    return await UserService.deactivate_account(db, current_user.id)

@router.delete("/account")
async def delete_my_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Permanently delete current user's account"""
    return await UserService.delete_account(db, current_user.id)
```

---

## 📱 Flutter Integration Example

```dart
// lib/services/user_service.dart
import 'package:dio/dio.dart';

class UserService {
  final Dio _dio;
  
  UserService(this._dio);
  
  // Get user profile
  Future<Map<String, dynamic>> getProfile() async {
    try {
      final response = await _dio.get('/api/users/profile');
      return response.data;
    } catch (e) {
      throw Exception('Failed to load profile: $e');
    }
  }
  
  // Update profile
  Future<Map<String, dynamic>> updateProfile({
    String? fullName,
    String? phoneNumber,
    String? email,
  }) async {
    try {
      final data = <String, dynamic>{};
      if (fullName != null) data['full_name'] = fullName;
      if (phoneNumber != null) data['phone_number'] = phoneNumber;
      if (email != null) data['email'] = email;
      
      final response = await _dio.put('/api/users/profile', data: data);
      return response.data;
    } catch (e) {
      throw Exception('Failed to update profile: $e');
    }
  }
  
  // Deactivate account
  Future<void> deactivateAccount() async {
    try {
      await _dio.post('/api/users/deactivate');
    } catch (e) {
      throw Exception('Failed to deactivate account: $e');
    }
  }
}

// Usage in Flutter widget
class ProfileScreen extends StatefulWidget {
  @override
  _ProfileScreenState createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final UserService _userService = UserService(Dio());
  Map<String, dynamic>? _profile;
  
  @override
  void initState() {
    super.initState();
    _loadProfile();
  }
  
  Future<void> _loadProfile() async {
    try {
      final profile = await _userService.getProfile();
      setState(() {
        _profile = profile;
      });
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString())),
      );
    }
  }
  
  @override
  Widget build(BuildContext context) {
    if (_profile == null) {
      return Center(child: CircularProgressIndicator());
    }
    
    return Scaffold(
      appBar: AppBar(title: Text('My Profile')),
      body: ListView(
        padding: EdgeInsets.all(16),
        children: [
          Text('Name: ${_profile!['user']['full_name']}'),
          Text('Phone: ${_profile!['user']['phone_number']}'),
          if (_profile!['user']['is_professional'])
            Column(
              children: [
                Text('Rating: ${_profile!['stats']['average_rating']}'),
                Text('Total Bookings: ${_profile!['stats']['total_bookings']}'),
                Text('Earnings: Rs ${_profile!['stats']['total_earnings']}'),
              ],
            ),
        ],
      ),
    );
  }
}
```

---

## ✅ Testing

### Test Cases

```python
# tests/test_users.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_profile(client: AsyncClient, auth_token: str):
    """Test getting user profile"""
    response = await client.get(
        "/api/users/profile",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "user" in data
    assert "stats" in data

@pytest.mark.asyncio
async def test_update_profile(client: AsyncClient, auth_token: str):
    """Test updating user profile"""
    response = await client.put(
        "/api/users/profile",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"full_name": "Updated Name"}
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Name"

@pytest.mark.asyncio
async def test_update_duplicate_phone(client: AsyncClient, auth_token: str):
    """Test updating to duplicate phone number fails"""
    response = await client.put(
        "/api/users/profile",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"phone_number": "9812345678"}  # Existing number
    )
    assert response.status_code == 409
```

---

## 🔐 Security Best Practices

1. **Always validate input** - Use Pydantic validators
2. **Check ownership** - Users can only modify their own data
3. **Prevent enumeration** - Don't reveal if phone/email exists during updates
4. **Rate limiting** - Limit profile update requests
5. **Audit logging** - Log all profile changes

---

## 📊 Performance Tips

1. **Cache user profiles** in Redis (TTL: 5 minutes)
2. **Use database indexes** on frequently queried fields
3. **Batch operations** when updating multiple users
4. **Lazy load statistics** - Only fetch when needed

---

**Next:** Professional registration and verification ➡️ See `05-PROFESSIONAL-REGISTRATION.md`
