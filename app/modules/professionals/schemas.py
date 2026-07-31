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