from typing import Optional
from pydantic import BaseModel, ConfigDict


class SkillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class SkillCreate(BaseModel):
    name: str


class SkillUpdate(BaseModel):
    name: Optional[str] = None