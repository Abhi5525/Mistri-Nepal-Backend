from typing import Optional
import re
from pydantic import BaseModel, ConfigDict, Field, field_validator


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
    """Skill update model"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    
    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, v):
        if v and not re.match(r'^[a-zA-Z\s\-]+$', v):
            raise ValueError("Skill name must contain only letters, spaces, and hyphens")
        return v.strip() if v else None


class SkillSearchResponse(BaseModel):
    """Skill search response"""
    model_config = ConfigDict(from_attributes=True)
    
    results: list[SkillResponse]
    total: int
