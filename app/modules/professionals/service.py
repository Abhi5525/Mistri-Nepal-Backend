from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from app.core.utils.string_utils import StringUtils
from app.modules.professionals.models import ProfessionalProfile
from app.modules.users.models import User
from app.modules.skills.models import Skill
from app.common.enum.role_enum import RoleEnum
from app.modules.auth.models import Role


# ✅ CREATE PROFESSIONAL PROFILE
async def create_professional_profile(
    db: AsyncSession,
    user_id: str,
    province: str,
    district: str,
    municipality: str,
    ward: int,
    experience: int = 0,
    about_yourself: str = None,
    hourly_rate: float = 0,
    latitude: float = None,
    longitude: float = None,
) -> ProfessionalProfile:
    """Create a new professional profile for a user"""
    try:
        # Check if user exists
        user_result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if professional profile already exists
        existing_result = await db.execute(
            select(ProfessionalProfile).where(ProfessionalProfile.user_id == user_id)
        )
        existing = existing_result.scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Professional profile already exists for this user"
            )
        
        # Update user role to PROFESSIONAL if not already
        if user.role.role != RoleEnum.PROFESSIONAL:
            professional_role = await db.execute(
                select(Role).where(Role.role == RoleEnum.PROFESSIONAL)
            )
            prof_role = professional_role.scalar_one_or_none()
            if prof_role:
                user.role_id = prof_role.id
        
        # Create new professional profile
        prof_id = "PR_" + StringUtils.randomAlphaNumeric(10)
        new_profile = ProfessionalProfile(
            professional_profile_id=prof_id,
            user_id=user_id,
            province=province,
            district=district,
            municipality=municipality,
            ward=ward,
            experience=experience,
            about_yourself=about_yourself,
            hourly_rate=hourly_rate,
            latitude=latitude,
            longitude=longitude,
            verification_status="PENDING",
            is_available=False,
        )
        
        db.add(new_profile)
        await db.commit()
        await db.refresh(new_profile)
        
        return new_profile

    except HTTPException as http_exc:
        await db.rollback()
        raise http_exc
    except Exception as e:
        await db.rollback()
        print("Error in create_professional_profile:", str(e))
        raise HTTPException(status_code=500, detail="Failed to create professional profile")


# ✅ GET PROFESSIONAL BY USER ID
async def get_professional_by_user_id(
    db: AsyncSession,
    user_id: str
) -> ProfessionalProfile:
    """Get professional profile by user ID"""
    try:
        result = await db.execute(
            select(ProfessionalProfile)
            .options(
                selectinload(ProfessionalProfile.skills),
                selectinload(ProfessionalProfile.user)
            )
            .where(ProfessionalProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()
    except Exception as e:
        print("Error in get_professional_by_user_id:", str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch professional profile")


# ✅ GET PROFESSIONAL BY PROFILE ID
async def get_professional_by_id(
    db: AsyncSession,
    profile_id: str
) -> ProfessionalProfile:
    """Get professional profile by profile ID"""
    try:
        result = await db.execute(
            select(ProfessionalProfile)
            .options(
                selectinload(ProfessionalProfile.skills),
                selectinload(ProfessionalProfile.user)
            )
            .where(ProfessionalProfile.professional_profile_id == profile_id)
        )
        return result.scalar_one_or_none()
    except Exception as e:
        print("Error in get_professional_by_id:", str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch professional profile")


# ✅ UPDATE PROFESSIONAL PROFILE
async def update_professional_profile(
    db: AsyncSession,
    profile_id: str,
    **kwargs
) -> ProfessionalProfile:
    """Update professional profile"""
    try:
        result = await db.execute(
            select(ProfessionalProfile).where(ProfessionalProfile.professional_profile_id == profile_id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            raise HTTPException(status_code=404, detail="Professional profile not found")
        
        # Update only provided fields
        for key, value in kwargs.items():
            if value is not None and hasattr(profile, key):
                setattr(profile, key, value)
        
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
        
        return profile

    except HTTPException as http_exc:
        await db.rollback()
        raise http_exc
    except Exception as e:
        await db.rollback()
        print("Error in update_professional_profile:", str(e))
        raise HTTPException(status_code=500, detail="Failed to update professional profile")


# ✅ ADD SKILL TO PROFESSIONAL
async def add_skill_to_professional(
    db: AsyncSession,
    profile_id: str,
    skill_id: int
) -> ProfessionalProfile:
    """Add a skill to professional"""
    try:
        # Get professional
        prof_result = await db.execute(
            select(ProfessionalProfile)
            .options(selectinload(ProfessionalProfile.skills))
            .where(ProfessionalProfile.professional_profile_id == profile_id)
        )
        professional = prof_result.scalar_one_or_none()
        
        if not professional:
            raise HTTPException(status_code=404, detail="Professional profile not found")
        
        # Get skill
        skill_result = await db.execute(
            select(Skill).where(Skill.id == skill_id)
        )
        skill = skill_result.scalar_one_or_none()
        
        if not skill:
            raise HTTPException(status_code=404, detail="Skill not found")
        
        # Check if skill already exists
        if skill in professional.skills:
            raise HTTPException(status_code=400, detail="Skill already assigned to this professional")
        
        professional.skills.append(skill)
        db.add(professional)
        await db.commit()
        await db.refresh(professional)
        
        return professional

    except HTTPException as http_exc:
        await db.rollback()
        raise http_exc
    except Exception as e:
        await db.rollback()
        print("Error in add_skill_to_professional:", str(e))
        raise HTTPException(status_code=500, detail="Failed to add skill")


# ✅ REMOVE SKILL FROM PROFESSIONAL
async def remove_skill_from_professional(
    db: AsyncSession,
    profile_id: str,
    skill_id: int
) -> ProfessionalProfile:
    """Remove a skill from professional"""
    try:
        # Get professional
        prof_result = await db.execute(
            select(ProfessionalProfile)
            .options(selectinload(ProfessionalProfile.skills))
            .where(ProfessionalProfile.professional_profile_id == profile_id)
        )
        professional = prof_result.scalar_one_or_none()
        
        if not professional:
            raise HTTPException(status_code=404, detail="Professional profile not found")
        
        # Get skill
        skill_result = await db.execute(
            select(Skill).where(Skill.id == skill_id)
        )
        skill = skill_result.scalar_one_or_none()
        
        if not skill:
            raise HTTPException(status_code=404, detail="Skill not found")
        
        # Check if skill exists
        if skill not in professional.skills:
            raise HTTPException(status_code=400, detail="Skill not assigned to this professional")
        
        professional.skills.remove(skill)
        db.add(professional)
        await db.commit()
        await db.refresh(professional)
        
        return professional

    except HTTPException as http_exc:
        await db.rollback()
        raise http_exc
    except Exception as e:
        await db.rollback()
        print("Error in remove_skill_from_professional:", str(e))
        raise HTTPException(status_code=500, detail="Failed to remove skill")


# ✅ VERIFY PROFESSIONAL (ADMIN)
async def verify_professional(
    db: AsyncSession,
    profile_id: str,
    verification_status: str,
    verified_by_id: str,
    rejection_reason: str = None
) -> ProfessionalProfile:
    """Verify or reject a professional profile"""
    try:
        # Get professional
        result = await db.execute(
            select(ProfessionalProfile).where(ProfessionalProfile.professional_profile_id == profile_id)
        )
        professional = result.scalar_one_or_none()
        
        if not professional:
            raise HTTPException(status_code=404, detail="Professional profile not found")
        
        # Get admin user
        admin_result = await db.execute(
            select(User).where(User.id == verified_by_id)
        )
        admin = admin_result.scalar_one_or_none()
        
        if not admin or admin.role.role != RoleEnum.ADMIN:
            raise HTTPException(status_code=403, detail="Only admins can verify professionals")
        
        # Update verification status
        professional.verification_status = verification_status
        professional.verified_by = verified_by_id
        
        if verification_status == "APPROVED":
            professional.is_available = True
            professional.rejection_reason = None
        elif verification_status == "REJECTED":
            professional.is_available = False
            professional.rejection_reason = rejection_reason
        
        from datetime import datetime
        professional.verified_at = datetime.now()
        
        db.add(professional)
        await db.commit()
        await db.refresh(professional)
        
        return professional

    except HTTPException as http_exc:
        await db.rollback()
        raise http_exc
    except Exception as e:
        await db.rollback()
        print("Error in verify_professional:", str(e))
        raise HTTPException(status_code=500, detail="Failed to verify professional")


# ✅ GET ALL PENDING PROFESSIONALS (FOR ADMIN)
async def get_pending_professionals(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 10
) -> list[ProfessionalProfile]:
    """Get all pending professional profiles"""
    try:
        result = await db.execute(
            select(ProfessionalProfile)
            .options(
                selectinload(ProfessionalProfile.user),
                selectinload(ProfessionalProfile.skills)
            )
            .where(ProfessionalProfile.verification_status == "PENDING")
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    except Exception as e:
        print("Error in get_pending_professionals:", str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch pending professionals")


# ✅ SEARCH PROFESSIONALS BY LOCATION
async def search_professionals_by_location(
    db: AsyncSession,
    district: str,
    skill_id: int = None,
    skip: int = 0,
    limit: int = 10
) -> list[ProfessionalProfile]:
    """Search professionals by district and optional skill"""
    try:
        query = select(ProfessionalProfile).options(
            selectinload(ProfessionalProfile.user),
            selectinload(ProfessionalProfile.skills)
        ).where(
            (ProfessionalProfile.district == district) &
            (ProfessionalProfile.verification_status == "APPROVED") &
            (ProfessionalProfile.is_available == True)
        )
        
        if skill_id:
            query = query.join(
                ProfessionalProfile.skills
            ).where(Skill.id == skill_id)
        
        result = await db.execute(
            query.offset(skip).limit(limit)
        )
        return result.scalars().all()
    except Exception as e:
        print("Error in search_professionals_by_location:", str(e))
        raise HTTPException(status_code=500, detail="Failed to search professionals")