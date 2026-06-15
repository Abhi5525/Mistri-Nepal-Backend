from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ProfessionalProfileCreate(BaseModel):
    """Professional profile create model"""
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    email: str

    province: str
    district: str
    municipality: str
    ward: int

    experience: int = 0
    about_yourself: Optional[str] = None
    rate: float = 0

    profile_picture: Optional[str] = None
    citizenship_front: Optional[str] = None
    citizenship_back: Optional[str] = None

    latitude: Optional[float] = None
    longitude: Optional[float] = None

    
class ProfessionalProfileResponse(BaseModel):
    """Professional profile response model"""
    model_config = ConfigDict(from_attributes=True)

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
    citizenship_front: Optional[str] = None
    citizenship_back: Optional[str] = None

    is_available: bool

    latitude: Optional[float] = None
    longitude: Optional[float] = None

    verification_status: str
    verified_at: Optional[datetime] = None
    verified_by: Optional[int] = None
    rejection_reason: Optional[str] = None


class ProfessionalProfileUpdate(BaseModel):
    """Professional profile update model"""
    model_config = ConfigDict(from_attributes=True)

    email: Optional[str] = None

    province: Optional[str] = None
    district: Optional[str] = None
    municipality: Optional[str] = None
    ward: Optional[int] = None

    experience: Optional[int] = None
    about_yourself: Optional[str] = None
    rate: Optional[float] = None

    average_rating: Optional[float] = None
    total_reviews: Optional[int] = None

    profile_picture: Optional[str] = None
    citizenship_front: Optional[str] = None
    citizenship_back: Optional[str] = None

    is_available: Optional[bool] = None

    latitude: Optional[float] = None
    longitude: Optional[float] = None

    verification_status: Optional[str] = None
    verified_at: Optional[datetime] = None
    verified_by: Optional[int] = None
    rejection_reason: Optional[str] = None