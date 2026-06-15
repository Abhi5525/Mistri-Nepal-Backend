from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from app.modules.professional.models import ProfessionalProfile
from app.modules.auth.models import User
from app.modules.skill.models import Skill


# ✅ CREATE PROFESSIONAL PROFILE
async def create_professional_profile(
    db: AsyncSession,
    user_id: int,
    email: str,
    province: str,
    district: str,
    municipality: str,
    ward: int,
    experience: int = 0,
    about_yourself: str = None,
    rate: float = 0,
) -> ProfessionalProfile:
    try:
        # check if already exists
        result = await db.execute(
            select(ProfessionalProfile).where(ProfessionalProfile.user_id == user_id)
        )
        existing = result.scalar_one_or_none()

        if existing:
            raise HTTPException(
                status_code=400,
                detail="Professional profile already exists for this user"
            )

        new_profile = ProfessionalProfile(
            user_id=user_id,
            email=email,
            province=province,
            district=district,
            municipality=municipality,
            ward=ward,
            experience=experience,
            about_yourself=about_yourself,
            rate=rate,
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
        raise HTTPException(500, "Failed to create professional profile")


# ✅ GET PROFESSIONAL BY USER ID
async def get_professional_by_user_id(
    db: AsyncSession,
    user_id: int
):
    result = await db.execute(
        select(ProfessionalProfile)
        .options(
            selectinload(ProfessionalProfile.skills),
            selectinload(ProfessionalProfile.user),
        )
        .where(ProfessionalProfile.user_id == user_id)
    )

    return result.scalar_one_or_none()


# ✅ GET PROFESSIONAL BY PROFILE ID
async def get_professional_by_id(
    db: AsyncSession,
    profile_id: int
):
    result = await db.execute(
        select(ProfessionalProfile)
        .options(
            selectinload(ProfessionalProfile.skills),
            selectinload(ProfessionalProfile.user),
        )
        .where(ProfessionalProfile.id == profile_id)
    )

    return result.scalar_one_or_none()


# ✅ ATTACH SKILL TO PROFESSIONAL
async def add_skill_to_professional(
    db: AsyncSession,
    professional: ProfessionalProfile,
    skill: Skill
):
    try:
        if skill in professional.skills:
            raise HTTPException(400, "Skill already added")

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
        print("Error adding skill:", str(e))
        raise HTTPException(500, "Failed to add skill")