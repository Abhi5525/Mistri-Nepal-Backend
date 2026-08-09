import re
from pydantic import field_validator
from datetime import datetime, time
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.modules.file.schemas import FileResponseSchema
from app.modules.skills.schemas import SkillResponse


class ProfessionalProfileResponse(BaseModel):
    """Professional profile response model"""
    model_config = ConfigDict(from_attributes=True)

    professional_profile_id: str
    user_id: str

    experience: str
    about_yourself: Optional[str] = None
    other_skills: Optional[str] = None
    base_rate: float

    average_rating: float
    total_reviews: int
    total_completed_jobs: int

    profile_image_id: Optional[str] = None
    citizenship_front_id: str
    citizenship_back_id: str

    profile_image: Optional[FileResponseSchema] = None
    citizenship_front: Optional[FileResponseSchema] = None
    citizenship_back: Optional[FileResponseSchema] = None

    skills: list[SkillResponse] = []
    is_available: bool
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # --- Scalable Scheduling Fields ---
    work_start_time: Optional[time] = None
    work_end_time: Optional[time] = None
    buffer_between_bookings_minutes: int = 30
    max_advance_booking_days: int = 3
    min_advance_booking_minutes: int = 60


class ProfessionalProfileUpdate(BaseModel):
    """Professional profile update model (citizenship files cannot be modified)"""
    model_config = ConfigDict(from_attributes=True)

    about_yourself: Optional[str] = None
    other_skills: Optional[str] = None
    base_rate: Optional[float] = None
    is_available: Optional[bool] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    work_start_time: Optional[time] = None
    work_end_time: Optional[time] = None
    buffer_between_bookings_minutes: Optional[int] = None
    max_advance_booking_days: Optional[int] = None
    min_advance_booking_minutes: Optional[int] = None
    
 
    @field_validator("about_yourself", mode="before")
    @classmethod
    def validate_about(cls, v):
        if v and len(v.strip()) < 10:
            raise ValueError("About yourself must be at least 10 characters")
        return v.strip() if v else None


class ProfessionalDetailResponse(BaseModel):
    """Professional detail response with user info"""
    model_config = ConfigDict(from_attributes=True)
    
    professional_profile_id: str
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