import re
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.common.pagination import PaginationQuery, PaginatedResponse


class SkillResponse(BaseModel):
    """Skill response model"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str


class SkillCreate(BaseModel):
    """Skill creation model"""
    name: str = Field(..., min_length=2, max_length=100)
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if not re.match(r'^[a-zA-Z\s\-]+$', v):
            raise ValueError("Skill name must contain only letters, spaces, and hyphens")
        return v.strip()


class SkillUpdate(BaseModel):
    name: Optional[str] = None


class SkillFilterQuery(PaginationQuery):
    """Query filter parameters for skills, extending global PaginationQuery"""

    name: Optional[str] = None


# Alias for type annotation if needed
PaginatedSkillResponse = PaginatedResponse[list[SkillResponse]]
