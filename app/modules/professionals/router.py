from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.database import get_db
from app.modules.professionals import service
from app.modules.professionals.schemas import (
    ProfessionalProfileResponse,
    ProfessionalProfileCreate,
    ProfessionalProfileUpdate
)

prof_router = APIRouter(prefix="/professionals", tags=["Professional"])


# ✅ CREATE PROFESSIONAL PROFILE
@prof_router.post("/", response_model=ProfessionalProfileResponse)
async def create_professional(
    data: ProfessionalProfileCreate,
    db: AsyncSession = Depends(get_db)
):
    result = await service.create_professional_profile(db=db, data=data)
    return result


# ✅ GET BY USER ID
@prof_router.get("/user/{user_id}", response_model=ProfessionalProfileResponse)
async def get_by_user_id(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await service.get_professional_by_user_id(db=db, user_id=user_id)

    if not result:
        raise HTTPException(status_code=404, detail="Professional not found")

    return result


# ✅ UPDATE PROFILE
@prof_router.put("/{profile_id}", response_model=ProfessionalProfileResponse)
async def update_professional(
    profile_id: int,
    data: ProfessionalProfileUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await service.update_professional_profile(
        db=db,
        profile_id=profile_id,
        data=data
    )

    return result