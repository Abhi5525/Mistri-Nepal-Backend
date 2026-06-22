from datetime import datetime
from typing import Optional
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProfessionalRegistrationRequest(BaseModel):
    """Professional registration request model"""
    model_config = ConfigDict(from_attributes=True)
    
    province: str = Field(..., min_length=2, max_length=100)
    district: str = Field(..., min_length=2, max_length=100)
    municipality: str = Field(..., min_length=2, max_length=100)
    ward: int = Field(..., ge=1, le=32)
    
    experience: int = Field(default=0, ge=0, le=50)
    about_yourself: Optional[str] = Field(None, max_length=500)
    hourly_rate: float = Field(default=0, ge=0, le=99999)
    
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    
    skill_ids: Optional[list[int]] = Field(default=None)
    
    @field_validator("province", "district", "municipality")
    @classmethod
    def validate_location_fields(cls, v):
        if not re.match(r'^[a-zA-Z\s\-\']+$', v):
            raise ValueError("Location fields must contain only letters, spaces, hyphens, and apostrophes")
        return v.strip()
    
    @field_validator("about_yourself")
    @classmethod
    def validate_about(cls, v):
        if v and len(v.strip()) < 10:
            raise ValueError("About yourself must be at least 10 characters")
        return v.strip() if v else None


class ProfessionalProfileCreate(BaseModel):
    """Professional profile create model"""
    model_config = ConfigDict(from_attributes=True)
    
    user_id: str
    province: str
    district: str
    municipality: str
    ward: int
    experience: int = 0
    about_yourself: Optional[str] = None
    hourly_rate: float = 0
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class ProfessionalProfileResponse(BaseModel):
    """Professional profile response model"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    user_id: str
    province: str
    district: str
    municipality: str
    ward: int
    
    experience: int
    about_yourself: Optional[str] = None
    hourly_rate: float
    
    average_rating: float
    total_reviews: int
    
    is_available: bool
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    verification_status: str
    verified_at: Optional[datetime] = None
    verified_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ProfessionalProfileUpdate(BaseModel):
    """Professional profile update model"""
    model_config = ConfigDict(from_attributes=True)
    
    province: Optional[str] = None
    district: Optional[str] = None
    municipality: Optional[str] = None
    ward: Optional[int] = None
    
    experience: Optional[int] = None
    about_yourself: Optional[str] = None
    hourly_rate: Optional[float] = None
    
    is_available: Optional[bool] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    @field_validator("province", "district", "municipality", mode="before")
    @classmethod
    def validate_location_fields(cls, v):
        if v and not re.match(r'^[a-zA-Z\s\-\']+$', v):
            raise ValueError("Location fields must contain only letters, spaces, hyphens, and apostrophes")
        return v.strip() if v else None
    
    @field_validator("about_yourself", mode="before")
    @classmethod
    def validate_about(cls, v):
        if v and len(v.strip()) < 10:
            raise ValueError("About yourself must be at least 10 characters")
        return v.strip() if v else None


class ProfessionalDetailResponse(BaseModel):
    """Professional detail response with user info"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    user_id: str
    full_name: str
    phone_number: str
    email: Optional[str] = None
    
    province: str
    district: str
    municipality: str
    ward: int
    
    experience: int
    about_yourself: Optional[str] = None
    hourly_rate: float
    
    average_rating: float
    total_reviews: int
    
    is_available: bool
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    verification_status: str
    verified_at: Optional[datetime] = None
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ProfessionalRegistrationSuccessResponse(BaseModel):
    """Professional registration success response"""
    message: str = "Professional profile registered successfully. Awaiting verification."
    data: ProfessionalProfileResponse


class ProfessionalVerificationRequest(BaseModel):
    """Professional verification request by admin"""
    verification_status: str = Field(..., pattern="^(APPROVED|REJECTED)$")
    rejection_reason: Optional[str] = Field(None, max_length=500)
    
    @field_validator("rejection_reason")
    @classmethod
    def validate_rejection_reason(cls, v, info):
        if info.data.get("verification_status") == "REJECTED" and not v:
            raise ValueError("rejection_reason is required when rejecting a professional")
        return v


class SkillAssignmentRequest(BaseModel):
    """Model for assigning skills to professional"""
    skill_id: int = Field(..., gt=0)