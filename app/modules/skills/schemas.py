from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.common.pagination import PaginationQuery, PaginatedResponse


class SkillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class SkillCreate(BaseModel):
    name: str


class SkillUpdate(BaseModel):
    name: Optional[str] = None


class SkillFilterQuery(PaginationQuery):
    """Query filter parameters for skills, extending global PaginationQuery"""

    name: Optional[str] = None


# Alias for type annotation if needed
PaginatedSkillResponse = PaginatedResponse[list[SkillResponse]]