# 05-PROFESSIONAL-REGISTRATION.md

# Professional Registration & Verification System

## 📋 Overview

Complete professional registration workflow with KYC document upload, verification states (PENDING/APPROVED/REJECTED), and admin approval system.

---

## 🗄️ Database Models

### `app/models/professional.py`

```python
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class ProfessionalProfile(Base):
    __tablename__ = "professional_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    
    # Location
    province = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False)
    municipality = Column(String(100), nullable=False)
    ward = Column(Integer, nullable=False)
    
    # Professional details
    experience = Column(Integer, default=0)
    about_yourself = Column(Text, nullable=True)
    rate = Column(Float, nullable=False, default=0)
    
    # Ratings
    average_rating = Column(Float, default=0.0)
    total_reviews = Column(Integer, default=0)
    
    # Documents
    profile_picture = Column(String(500), nullable=True)
    citizenship_front = Column(String(500), nullable=True)
    citizenship_back = Column(String(500), nullable=True)
    
    # Availability & Location
    is_available = Column(Boolean, default=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Verification
    verification_status = Column(
        String(20),
        default='PENDING',
        nullable=False
    )
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="professional_profile")
    skills = relationship("Skill", secondary="professional_skills", back_populates="professionals")
    bookings = relationship("Booking", back_populates="professional")
    reviews = relationship("Review", back_populates="professional")
    
    __table_args__ = (
        CheckConstraint('experience >= 0 AND experience <= 50', name='check_experience_range'),
        CheckConstraint('rate >= 0 AND rate <= 10000', name='check_rate_range'),
        CheckConstraint(
            "verification_status IN ('PENDING', 'APPROVED', 'REJECTED')",
            name='check_verification_status'
        ),
    )
```

### `app/models/skill.py`

```python
from sqlalchemy import Column, Integer, String, Text, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class Skill(Base):
    __tablename__ = "skills"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    category = Column(String(50), default='General')
    description = Column(Text, nullable=True)
    aliases = Column(JSON, default=list)  # For fuzzy search
    
    professionals = relationship("ProfessionalProfile", secondary="professional_skills", back_populates="skills")
```

### `app/models/professional_skill.py`

```python
from sqlalchemy import Column, Integer, ForeignKey, PrimaryKeyConstraint
from app.database import Base

class ProfessionalSkill(Base):
    __tablename__ = "professional_skills"
    
    professional_id = Column(Integer, ForeignKey("professional_profiles.id", ondelete="CASCADE"), primary_key=True)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)
```

---

## 📝 Pydantic Schemas

### `app/schemas/professional.py`

```python
from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, List
from datetime import datetime

class ProfessionalRegistration(BaseModel):
    """Schema for professional registration"""
    email: EmailStr
    skill_ids: List[int] = Field(..., min_items=1, max_items=3)
    province: str = Field(..., min_length=2)
    district: str = Field(..., min_length=2)
    municipality: str = Field(..., min_length=2)
    ward: int = Field(..., ge=1, le=50)
    experience: int = Field(..., ge=0, le=50)
    about_yourself: Optional[str] = Field(None, max_length=1000)
    rate: float = Field(..., gt=0, le=10000)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    @validator('rate')
    def validate_rate(cls, v, values):
        if 'experience' in values:
            exp = values['experience']
            if exp < 1 and v > 200:
                raise ValueError('Rate must be ≤ 200 for experience < 1 year')
            elif 1 <= exp < 3 and v > 300:
                raise ValueError('Rate must be ≤ 300 for experience 1-3 years')
            elif 3 <= exp < 5 and v > 400:
                raise ValueError('Rate must be ≤ 400 for experience 3-5 years')
            elif exp >= 5 and v > 600:
                raise ValueError('Rate must be ≤ 600 for experience ≥ 5 years')
        return v

class ProfessionalUpdate(BaseModel):
    """Schema for updating professional profile"""
    email: Optional[EmailStr] = None
    skill_ids: Optional[List[int]] = Field(None, min_items=1, max_items=3)
    province: Optional[str] = None
    district: Optional[str] = None
    municipality: Optional[str] = None
    ward: Optional[int] = Field(None, ge=1, le=50)
    experience: Optional[int] = Field(None, ge=0, le=50)
    about_yourself: Optional[str] = Field(None, max_length=1000)
    rate: Optional[float] = Field(None, gt=0, le=10000)
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class ProfessionalResponse(BaseModel):
    """Professional profile response"""
    id: int
    user_id: int
    email: str
    province: str
    district: str
    municipality: str
    ward: int
    experience: int
    about_yourself: Optional[str] = None
    rate: float
    average_rating: float
    total_reviews: int
    profile_picture: Optional[str] = None
    is_available: bool
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    verification_status: str
    skills: List[str] = []
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class DocumentUploadResponse(BaseModel):
    """Response after document upload"""
    message: str
    file_url: str
    field_name: str

class VerificationAction(BaseModel):
    """Admin verification action"""
    action: str = Field(..., pattern="^(approve|reject)$")
    rejection_reason: Optional[str] = Field(None, max_length=500)
```

---

## 📁 File Upload Service

### `app/services/file_service.py`

```python
import os
import uuid
from fastapi import UploadFile, HTTPException, status
from typing import Optional

class FileService:
    """Handle file uploads for KYC documents"""
    
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    
    UPLOAD_DIR = {
        'profile_pictures': 'uploads/profile_pictures',
        'citizenship_front': 'uploads/citizenship/front',
        'citizenship_back': 'uploads/citizenship/back',
    }
    
    @staticmethod
    def validate_image(file: UploadFile) -> None:
        """Validate uploaded image file"""
        
        # Check file size
        file.file.seek(0, 2)  # Seek to end
        size = file.file.tell()
        file.file.seek(0)  # Reset position
        
        if size > FileService.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size must not exceed 5MB"
            )
        
        # Check extension
        filename = file.filename or ""
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        
        if ext not in FileService.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed: {', '.join(FileService.ALLOWED_EXTENSIONS)}"
            )
        
        # Check content type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image"
            )
    
    @staticmethod
    async def save_upload(file: UploadFile, upload_type: str) -> str:
        """Save uploaded file and return URL path"""
        
        # Validate file
        FileService.validate_image(file)
        
        # Create directory if not exists
        upload_dir = FileService.UPLOAD_DIR.get(upload_type)
        if not upload_dir:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid upload type"
            )
        
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        ext = file.filename.rsplit('.', 1)[-1].lower() if file.filename else 'jpg'
        unique_filename = f"{uuid.uuid4().hex}.{ext}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Save file
        with open(file_path, 'wb') as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Return URL path
        return f"/{file_path}"
    
    @staticmethod
    def delete_file(file_url: str) -> bool:
        """Delete file from storage"""
        try:
            # Remove leading slash
            file_path = file_url.lstrip('/')
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
        except Exception:
            pass
        return False
```

---

## 🔧 Professional Service

### `app/services/professional_service.py`

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.user import User
from app.models.professional import ProfessionalProfile
from app.models.skill import Skill
from app.schemas.professional import ProfessionalRegistration, ProfessionalUpdate
from app.services.file_service import FileService
from fastapi import HTTPException, status, UploadFile
from typing import Optional
from datetime import datetime

class ProfessionalService:
    """Professional registration and management service"""
    
    @staticmethod
    async def register_professional(
        db: AsyncSession,
        user_id: int,
        registration_data: ProfessionalRegistration,
        profile_picture: UploadFile,
        citizenship_front: Optional[UploadFile] = None,
        citizenship_back: Optional[UploadFile] = None
    ) -> dict:
        """Register new professional with KYC documents"""
        
        # Check if user already has professional profile
        result = await db.execute(
            select(ProfessionalProfile).where(ProfessionalProfile.user_id == user_id)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            if existing.verification_status == 'APPROVED':
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Already an approved professional"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Professional application is {existing.verification_status}"
                )
        
        # Verify skills exist
        skills_result = await db.execute(
            select(Skill).where(Skill.id.in_(registration_data.skill_ids))
        )
        skills = skills_result.scalars().all()
        
        if len(skills) != len(registration_data.skill_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more skills not found"
            )
        
        # Upload profile picture (required)
        profile_pic_url = await FileService.save_upload(
            profile_picture, 'profile_pictures'
        )
        
        # Upload citizenship documents (optional but recommended)
        citizenship_front_url = None
        citizenship_back_url = None
        
        if citizenship_front:
            citizenship_front_url = await FileService.save_upload(
                citizenship_front, 'citizenship_front'
            )
        
        if citizenship_back:
            citizenship_back_url = await FileService.save_upload(
                citizenship_back, 'citizenship_back'
            )
        
        # Create professional profile
        profile = ProfessionalProfile(
            user_id=user_id,
            email=registration_data.email,
            province=registration_data.province,
            district=registration_data.district,
            municipality=registration_data.municipality,
            ward=registration_data.ward,
            experience=registration_data.experience,
            about_yourself=registration_data.about_yourself,
            rate=registration_data.rate,
            profile_picture=profile_pic_url,
            citizenship_front=citizenship_front_url,
            citizenship_back=citizenship_back_url,
            latitude=registration_data.latitude,
            longitude=registration_data.longitude,
            verification_status='PENDING',
            is_available=False  # Not available until approved
        )
        
        db.add(profile)
        await db.flush()
        await db.refresh(profile)
        
        # Associate skills
        for skill in skills:
            profile.skills.append(skill)
        
        # Update user as professional
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one()
        user.is_professional = True
        user.is_client = False
        
        await db.flush()
        
        return {
            "message": "Professional registration submitted for verification",
            "profile": profile,
            "status": "PENDING"
        }
    
    @staticmethod
    async def update_professional(
        db: AsyncSession,
        user_id: int,
        update_data: ProfessionalUpdate,
        profile_picture: Optional[UploadFile] = None,
        citizenship_front: Optional[UploadFile] = None,
        citizenship_back: Optional[UploadFile] = None
    ) -> ProfessionalProfile:
        """Update professional profile"""
        
        # Get profile
        result = await db.execute(
            select(ProfessionalProfile).where(ProfessionalProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Professional profile not found"
            )
        
        # Check if rejected - allow updates for re-application
        if profile.verification_status == 'REJECTED':
            # Reset to pending on update
            profile.verification_status = 'PENDING'
            profile.rejection_reason = None
            profile.verified_at = None
            profile.verified_by = None
        
        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        
        for field, value in update_dict.items():
            if field == 'skill_ids':
                # Update skills
                skills_result = await db.execute(
                    select(Skill).where(Skill.id.in_(value))
                )
                new_skills = skills_result.scalars().all()
                profile.skills.clear()
                for skill in new_skills:
                    profile.skills.append(skill)
            else:
                setattr(profile, field, value)
        
        # Handle file uploads
        if profile_picture:
            # Delete old file
            if profile.profile_picture:
                FileService.delete_file(profile.profile_picture)
            profile.profile_picture = await FileService.save_upload(
                profile_picture, 'profile_pictures'
            )
        
        if citizenship_front:
            if profile.citizenship_front:
                FileService.delete_file(profile.citizenship_front)
            profile.citizenship_front = await FileService.save_upload(
                citizenship_front, 'citizenship_front'
            )
        
        if citizenship_back:
            if profile.citizenship_back:
                FileService.delete_file(profile.citizenship_back)
            profile.citizenship_back = await FileService.save_upload(
                citizenship_back, 'citizenship_back'
            )
        
        await db.flush()
        await db.refresh(profile)
        
        return profile
    
    @staticmethod
    async def toggle_availability(db: AsyncSession, user_id: int) -> dict:
        """Toggle professional availability status"""
        
        result = await db.execute(
            select(ProfessionalProfile).where(ProfessionalProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Professional profile not found"
            )
        
        # Only approved professionals can toggle availability
        if profile.verification_status != 'APPROVED':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Cannot toggle availability. Status: {profile.verification_status}"
            )
        
        profile.is_available = not profile.is_available
        await db.flush()
        
        return {
            "is_available": profile.is_available,
            "message": f"You are now {'available' if profile.is_available else 'unavailable'}"
        }
    
    @staticmethod
    async def approve_professional(
        db: AsyncSession,
        profile_id: int,
        admin_id: int
    ) -> dict:
        """Admin approves professional (with validation)"""
        
        result = await db.execute(
            select(ProfessionalProfile).where(ProfessionalProfile.id == profile_id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Professional profile not found"
            )
        
        if profile.verification_status != 'PENDING':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Can only approve PENDING profiles. Current: {profile.verification_status}"
            )
        
        # Validate rate based on experience
        exp = profile.experience
        rate = profile.rate
        
        if exp < 1 and rate > 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rate too high for experience level (< 1 year)"
            )
        elif 1 <= exp < 3 and rate > 300:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rate too high for experience level (1-3 years)"
            )
        elif 3 <= exp < 5 and rate > 400:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rate too high for experience level (3-5 years)"
            )
        elif exp >= 5 and rate > 600:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rate too high for experience level (≥ 5 years)"
            )
        
        # Approve
        profile.verification_status = 'APPROVED'
        profile.verified_at = datetime.utcnow()
        profile.verified_by = admin_id
        profile.rejection_reason = None
        profile.is_available = True  # Auto-enable on approval
        
        await db.flush()
        
        # Send push notification to professional
        from app.services.notification_service import NotificationService
        await NotificationService.send_push_notification(
            user_id=profile.user_id,
            title="✅ Professional Account Approved!",
            body="Your account has been approved. You can now accept bookings.",
            data={"type": "approval"}
        )
        
        return {
            "message": "Professional approved successfully",
            "profile": profile
        }
    
    @staticmethod
    async def reject_professional(
        db: AsyncSession,
        profile_id: int,
        admin_id: int,
        rejection_reason: str
    ) -> dict:
        """Admin rejects professional with reason"""
        
        result = await db.execute(
            select(ProfessionalProfile).where(ProfessionalProfile.id == profile_id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Professional profile not found"
            )
        
        # Reject
        profile.verification_status = 'REJECTED'
        profile.verified_at = datetime.utcnow()
        profile.verified_by = admin_id
        profile.rejection_reason = rejection_reason
        profile.is_available = False
        
        # Update user back to client
        user_result = await db.execute(select(User).where(User.id == profile.user_id))
        user = user_result.scalar_one()
        user.is_professional = False
        user.is_client = True
        
        await db.flush()
        
        # Send notification
        from app.services.notification_service import NotificationService
        await NotificationService.send_push_notification(
            user_id=profile.user_id,
            title="❌ Professional Application Rejected",
            body=f"Reason: {rejection_reason}. You can reapply with corrections.",
            data={"type": "rejection"}
        )
        
        return {
            "message": "Professional rejected",
            "profile": profile
        }
```

---

## 🌐 API Endpoints

### `app/api/professionals.py`

```python
from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.dependencies import get_current_user, get_current_admin
from app.models.user import User
from app.schemas.professional import (
    ProfessionalRegistration, ProfessionalUpdate, ProfessionalResponse,
    VerificationAction
)
from app.services.professional_service import ProfessionalService

router = APIRouter(prefix="/api/professionals", tags=["Professionals"])

@router.post("/register", response_model=dict)
async def register_professional(
    email: str = Form(...),
    skill_ids: str = Form(...),  # JSON string
    province: str = Form(...),
    district: str = Form(...),
    municipality: str = Form(...),
    ward: int = Form(...),
    experience: int = Form(...),
    rate: float = Form(...),
    about_yourself: str = Form(None),
    latitude: float = Form(None),
    longitude: float = Form(None),
    profile_picture: UploadFile = File(...),
    citizenship_front: UploadFile = File(None),
    citizenship_back: UploadFile = File(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Register as a professional with KYC documents"""
    import json
    skill_ids_list = json.loads(skill_ids)
    
    registration_data = ProfessionalRegistration(
        email=email,
        skill_ids=skill_ids_list,
        province=province,
        district=district,
        municipality=municipality,
        ward=ward,
        experience=experience,
        rate=rate,
        about_yourself=about_yourself,
        latitude=latitude,
        longitude=longitude
    )
    
    return await ProfessionalService.register_professional(
        db, current_user.id, registration_data,
        profile_picture, citizenship_front, citizenship_back
    )

@router.put("/profile", response_model=ProfessionalResponse)
async def update_professional_profile(
    email: str = Form(None),
    skill_ids: str = Form(None),
    province: str = Form(None),
    district: str = Form(None),
    municipality: str = Form(None),
    ward: int = Form(None),
    experience: int = Form(None),
    rate: float = Form(None),
    about_yourself: str = Form(None),
    latitude: float = Form(None),
    longitude: float = Form(None),
    profile_picture: UploadFile = File(None),
    citizenship_front: UploadFile = File(None),
    citizenship_back: UploadFile = File(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update professional profile"""
    import json
    skill_ids_list = json.loads(skill_ids) if skill_ids else None
    
    update_data = ProfessionalUpdate(
        email=email,
        skill_ids=skill_ids_list,
        province=province,
        district=district,
        municipality=municipality,
        ward=ward,
        experience=experience,
        rate=rate,
        about_yourself=about_yourself,
        latitude=latitude,
        longitude=longitude
    )
    
    profile = await ProfessionalService.update_professional(
        db, current_user.id, update_data,
        profile_picture, citizenship_front, citizenship_back
    )
    return profile

@router.post("/toggle-availability")
async def toggle_availability(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Toggle professional availability"""
    return await ProfessionalService.toggle_availability(db, current_user.id)

# Admin endpoints
@router.post("/{profile_id}/approve")
async def approve_professional(
    profile_id: int,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Admin approves professional"""
    return await ProfessionalService.approve_professional(db, profile_id, current_admin.id)

@router.post("/{profile_id}/reject")
async def reject_professional(
    profile_id: int,
    action: VerificationAction,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Admin rejects professional with reason"""
    if not action.rejection_reason:
        raise HTTPException(status_code=400, detail="Rejection reason required")
    
    return await ProfessionalService.reject_professional(
        db, profile_id, current_admin.id, action.rejection_reason
    )
```

---

## 📱 Flutter Integration

```dart
// lib/services/professional_service.dart
import 'package:dio/dio.dart';

class ProfessionalService {
  final Dio _dio;
  
  ProfessionalService(this._dio);
  
  // Register as professional
  Future<Map<String, dynamic>> registerProfessional({
    required String email,
    required List<int> skillIds,
    required String province,
    required String district,
    required String municipality,
    required int ward,
    required int experience,
    required double rate,
    String? aboutYourself,
    double? latitude,
    double? longitude,
    required String profilePicturePath,
    String? citizenshipFrontPath,
    String? citizenshipBackPath,
  }) async {
    try {
      final formData = FormData.fromMap({
        'email': email,
        'skill_ids': skillIds.toString(),
        'province': province,
        'district': district,
        'municipality': municipality,
        'ward': ward,
        'experience': experience,
        'rate': rate,
        'about_yourself': aboutYourself,
        'latitude': latitude,
        'longitude': longitude,
        'profile_picture': await MultipartFile.fromFile(profilePicturePath),
        if (citizenshipFrontPath != null)
          'citizenship_front': await MultipartFile.fromFile(citizenshipFrontPath),
        if (citizenshipBackPath != null)
          'citizenship_back': await MultipartFile.fromFile(citizenshipBackPath),
      });
      
      final response = await _dio.post(
        '/api/professionals/register',
        data: formData,
      );
      
      return response.data;
    } catch (e) {
      throw Exception('Registration failed: $e');
    }
  }
  
  // Toggle availability
  Future<Map<String, dynamic>> toggleAvailability() async {
    try {
      final response = await _dio.post('/api/professionals/toggle-availability');
      return response.data;
    } catch (e) {
      throw Exception('Failed to toggle availability: $e');
    }
  }
}
```

---

## ✅ Testing

```python
# tests/test_professionals.py
@pytest.mark.asyncio
async def test_register_professional(client, auth_token, test_image):
    """Test professional registration"""
    formData = {
        'email': 'test@example.com',
        'skill_ids': '[1, 2]',
        'province': 'Bagmati',
        'district': 'Kathmandu',
        'municipality': 'Kathmandu',
        'ward': 1,
        'experience': 2,
        'rate': 250,
        'profile_picture': test_image,
    }
    
    response = await client.post(
        '/api/professionals/register',
        headers={'Authorization': f'Bearer {auth_token}'},
        data=formData
    )
    
    assert response.status_code == 200
    assert response.json()['status'] == 'PENDING'

@pytest.mark.asyncio
async def test_approve_professional(client, admin_token, pending_profile_id):
    """Test admin approval"""
    response = await client.post(
        f'/api/professionals/{pending_profile_id}/approve',
        headers={'Authorization': f'Bearer {admin_token}'}
    )
    
    assert response.status_code == 200
```

---

**Next:** Location services and geospatial queries ➡️ See `06-LOCATION-SERVICES.md`
