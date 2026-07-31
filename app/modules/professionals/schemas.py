from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.modules.file.schemas import FileResponseSchema
from app.modules.skills.schemas import SkillResponse


class ProfessionalProfileResponse(BaseModel):
    """Professional profile response model"""
    model_config = ConfigDict(from_attributes=True)

    id: int
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


class ProfessionalProfileUpdate(BaseModel):
    """Professional profile update model (citizenship files cannot be modified)"""
    model_config = ConfigDict(from_attributes=True)

    about_yourself: Optional[str] = None
    other_skills: Optional[str] = None
    base_rate: Optional[float] = None
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