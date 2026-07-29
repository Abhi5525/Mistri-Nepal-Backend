from typing import Optional, Tuple, List
from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.skills.models import Skill
from app.modules.skills.schemas import SkillCreate, SkillUpdate, SkillFilterQuery


async def create_skill(db: AsyncSession, data: SkillCreate) -> Skill:
    """
    Creates a new skill after validating that a skill with the same name doesn't already exist.
    """
    try:
        skill_name = data.name.strip()
        existing_skill = await db.execute(
            select(Skill).where(Skill.name.ilike(skill_name))
        )
        if existing_skill.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Skill with name '{skill_name}' already exists",
            )

        new_skill = Skill(name=skill_name)
        db.add(new_skill)
        await db.commit()
        await db.refresh(new_skill)
        return new_skill
    except HTTPException as http_exc:
        await db.rollback()
        raise http_exc
    except Exception as e:
        await db.rollback()
        print("Error in create_skill:", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create skill",
        )


async def get_all_skills(
    db: AsyncSession,
    filter_query: SkillFilterQuery,
) -> Tuple[List[Skill], int]:
    """
    Retrieves skills with optional name search filtering and pagination.
    Returns a tuple of (skills, total_records).
    """
    try:
        base_query = select(Skill)

        if filter_query.name and filter_query.name.strip():
            search_pattern = f"%{filter_query.name.strip()}%"
            base_query = base_query.where(Skill.name.ilike(search_pattern))

        # Count total records matching the filter
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await db.execute(count_query)
        total_records = total_result.scalar_one()

        # Apply pagination (using filter_query.offset and filter_query.size)
        paginated_query = (
            base_query.order_by(Skill.id.asc())
            .offset(filter_query.offset)
            .limit(filter_query.size)
        )

        result = await db.execute(paginated_query)
        skills = list(result.scalars().all())

        return skills, total_records
    except Exception as e:
        print("Error in get_all_skills:", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch skills",
        )


async def get_skill_by_id(db: AsyncSession, skill_id: int) -> Optional[Skill]:
    """
    Retrieves a skill by its ID.
    """
    try:
        result = await db.execute(select(Skill).where(Skill.id == skill_id))
        return result.scalar_one_or_none()
    except Exception as e:
        print("Error in get_skill_by_id:", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch skill",
        )


async def update_skill(
    db: AsyncSession, skill_id: int, data: SkillUpdate
) -> Optional[Skill]:
    """
    Updates an existing skill's details.
    """
    try:
        skill = await get_skill_by_id(db=db, skill_id=skill_id)
        if not skill:
            return None

        if data.name is not None and data.name.strip() != "":
            new_name = data.name.strip()
            existing = await db.execute(
                select(Skill).where(
                    Skill.name.ilike(new_name),
                    Skill.id != skill_id,
                )
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Skill with name '{new_name}' already exists",
                )
            skill.name = new_name

        await db.commit()
        await db.refresh(skill)
        return skill
    except HTTPException as http_exc:
        await db.rollback()
        raise http_exc
    except Exception as e:
        await db.rollback()
        print("Error in update_skill:", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update skill",
        )


async def delete_skill(db: AsyncSession, skill_id: int) -> bool:
    """
    Deletes a skill by its ID.
    """
    try:
        skill = await get_skill_by_id(db=db, skill_id=skill_id)
        if not skill:
            return False

        await db.delete(skill)
        await db.commit()
        return True
    except HTTPException as http_exc:
        await db.rollback()
        raise http_exc
    except Exception as e:
        await db.rollback()
        print("Error in delete_skill:", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete skill",
        )
