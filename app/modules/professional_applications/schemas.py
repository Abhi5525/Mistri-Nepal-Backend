from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.modules.file.schemas import FileResponseSchema
from app.modules.professional_applications.models import ApplicationStatusEnum
from app.modules.skills.schemas import SkillResponse


class ProfessionalApplicationCreate(BaseModel):
    """Schema for submitting a professional application"""

    model_config = ConfigDict(from_attributes=True)

    email: EmailStr = Field(..., description="Contact email address")
    province: str = Field(..., description="Province name")
    district: str = Field(..., description="District name")
    municipality: str = Field(..., description="Municipality name")
    ward: int = Field(..., description="Ward number")

    experience: str = Field(..., description="Experience description or duration")
    about_yourself: Optional[str] = Field(None, description="Brief bio/description")
    other_skills: Optional[str] = Field(None, description="Optional custom skills not listed in available skills")
    base_rate: float = Field(0.0, description="Base rate for services")

    latitude: Optional[float] = Field(None, description="Location latitude")
    longitude: Optional[float] = Field(None, description="Location longitude")

    profile_image_id: str = Field(..., description="File ID for profile image")
    citizenship_front_id: str = Field(..., description="File ID for citizenship front image")
    citizenship_back_id: str = Field(..., description="File ID for citizenship back image")

    skill_ids: list[int] = Field(default_factory=list, description="List of selected skill IDs")


class ProfessionalApplicationUpdateStatus(BaseModel):
    """Schema for updating application workflow status (Admin review)"""

    model_config = ConfigDict(from_attributes=True)

    status: ApplicationStatusEnum = Field(..., description="Application workflow status")
    rejection_reason: Optional[str] = Field(None, description="Reason for rejection if status is REJECTED")


class ProfessionalApplicationResponse(BaseModel):
    """Response schema for professional application details"""

    model_config = ConfigDict(from_attributes=True)

    professional_application_id: str = Field(..., description="Unique application ID")
    user_id: str = Field(..., description="ID of the applying user")

    email: str
    province: str
    district: str
    municipality: str
    ward: int

    experience: str
    about_yourself: Optional[str] = None
    other_skills: Optional[str] = None
    base_rate: float

    latitude: Optional[float] = None
    longitude: Optional[float] = None

    profile_image_id: str
    citizenship_front_id: str
    citizenship_back_id: str

    profile_image: Optional[FileResponseSchema] = None
    citizenship_front: Optional[FileResponseSchema] = None
    citizenship_back: Optional[FileResponseSchema] = None

    skills: list[SkillResponse] = Field(default_factory=list)

    status: ApplicationStatusEnum
    rejection_reason: Optional[str] = None

    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None

    created_at: datetime
    updated_at: datetime
