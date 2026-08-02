from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enum.role_enum import RoleEnum
from app.core.db.database import get_db
from app.core.security.security import get_current_user
from app.modules.auth.schemas import JwtPayload
from app.modules.professionals import documents_service, service
from app.modules.professionals.schemas import (
    ProfessionalProfileResponse,
    ProfessionalProfileUpdate,
    ProfessionalRegistrationRequest,
    ProfessionalRegistrationSuccessResponse,
    ProfessionalVerificationRequest,
    SkillAssignmentRequest,
)

prof_router = APIRouter(prefix="/professionals", tags=["Professional"])


# ✅ REGISTER AS PROFESSIONAL
@prof_router.post("/register", response_model=ProfessionalRegistrationSuccessResponse)
async def register_professional(
    data: ProfessionalRegistrationRequest,
    current_user: JwtPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Register current user as a professional"""
    result = await service.create_professional_profile(
        db=db,
        user_id=current_user.sub,
        province=data.province,
        district=data.district,
        municipality=data.municipality,
        ward=data.ward,
        experience=data.experience,
        about_yourself=data.about_yourself,
        hourly_rate=data.hourly_rate,
        latitude=data.latitude,
        longitude=data.longitude,
    )
    return ProfessionalRegistrationSuccessResponse(data=result)


# ✅ GET OWN PROFESSIONAL PROFILE
@prof_router.get("/me", response_model=ProfessionalProfileResponse)
async def get_my_profile(
    current_user: JwtPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's professional profile"""
    result = await service.get_professional_by_user_id(db=db, user_id=current_user.sub)
    
    if not result:
        raise HTTPException(status_code=404, detail="Professional profile not found")
    
    return result


# ✅ GET PROFESSIONAL PROFILE BY ID
@prof_router.get("/{profile_id}", response_model=ProfessionalProfileResponse)
async def get_professional_by_id(
    profile_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get professional profile by ID"""
    result = await service.get_professional_by_id(db=db, profile_id=profile_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Professional profile not found")
    
    return result


# ✅ UPDATE OWN PROFESSIONAL PROFILE
@prof_router.put("/me", response_model=ProfessionalProfileResponse)
async def update_my_profile(
    data: ProfessionalProfileUpdate,
    current_user: JwtPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user's professional profile"""
    # Get current profile first
    profile = await service.get_professional_by_user_id(db=db, user_id=current_user.sub)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Professional profile not found")
    
    # Update with provided fields
    result = await service.update_professional_profile(
        db=db,
        profile_id=profile.professional_profile_id,
        **data.model_dump(exclude_unset=True)
    )
    
    return result


# ✅ UPDATE PROFESSIONAL PROFILE (ADMIN)
@prof_router.put("/{profile_id}", response_model=ProfessionalProfileResponse)
async def update_professional(
    profile_id: str,
    data: ProfessionalProfileUpdate,
    current_user: JwtPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update professional profile (admin only)"""
    if current_user.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can update other professional profiles")
    
    result = await service.update_professional_profile(
        db=db,
        profile_id=profile_id,
        **data.model_dump(exclude_unset=True)
    )
    
    return result


# ✅ GET PROFESSIONAL BY USER ID
@prof_router.get("/user/{user_id}", response_model=ProfessionalProfileResponse)
async def get_by_user_id(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get professional profile by user ID"""
    result = await service.get_professional_by_user_id(db=db, user_id=user_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Professional profile not found")
    
    return result


# ✅ ADD SKILL TO PROFESSIONAL
@prof_router.post("/{profile_id}/skills", response_model=ProfessionalProfileResponse)
async def add_skill(
    profile_id: str,
    data: SkillAssignmentRequest,
    current_user: JwtPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a skill to professional profile"""
    # Get professional profile
    profile = await service.get_professional_by_id(db=db, profile_id=profile_id)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Professional profile not found")
    
    # Only professional or admin can add skills to their profile
    if profile.user_id != current_user.sub and current_user.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="You can only add skills to your own profile")
    
    result = await service.add_skill_to_professional(
        db=db,
        profile_id=profile_id,
        skill_id=data.skill_id
    )
    
    return result


# ✅ REMOVE SKILL FROM PROFESSIONAL
@prof_router.delete("/{profile_id}/skills/{skill_id}", response_model=ProfessionalProfileResponse)
async def remove_skill(
    profile_id: str,
    skill_id: int,
    current_user: JwtPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a skill from professional profile"""
    # Get professional profile
    profile = await service.get_professional_by_id(db=db, profile_id=profile_id)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Professional profile not found")
    
    # Only professional or admin can remove skills from their profile
    if profile.user_id != current_user.sub and current_user.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="You can only remove skills from your own profile")
    
    result = await service.remove_skill_from_professional(
        db=db,
        profile_id=profile_id,
        skill_id=skill_id
    )
    
    return result


# ✅ VERIFY PROFESSIONAL (ADMIN)
@prof_router.patch("/{profile_id}/verify", response_model=ProfessionalProfileResponse)
async def verify_professional(
    profile_id: str,
    data: ProfessionalVerificationRequest,
    current_user: JwtPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Verify or reject professional profile (admin only)"""
    if current_user.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can verify professionals")
    
    result = await service.verify_professional(
        db=db,
        profile_id=profile_id,
        verification_status=data.verification_status,
        verified_by_id=current_user.sub,
        rejection_reason=data.rejection_reason,
    )
    
    return result


# ✅ GET PENDING PROFESSIONALS (ADMIN)
@prof_router.get("/admin/pending", response_model=list[ProfessionalProfileResponse])
async def get_pending_professionals(
    skip: int = 0,
    limit: int = 10,
    current_user: JwtPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all pending professional profiles (admin only)"""
    if current_user.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can view pending professionals")
    
    result = await service.get_pending_professionals(db=db, skip=skip, limit=limit)
    
    return result


# ✅ SEARCH PROFESSIONALS BY LOCATION
@prof_router.get("/search/location", response_model=list[ProfessionalProfileResponse])
async def search_by_location(
    district: str,
    skill_id: int | None = None,
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """Search professionals by district and optional skill"""
    result = await service.search_professionals_by_location(
        db=db,
        district=district,
        skill_id=skill_id,
        skip=skip,
        limit=limit
    )
    
    return result

