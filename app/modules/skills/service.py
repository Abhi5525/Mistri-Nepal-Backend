from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.modules.skills.models import Skill


# ✅ CREATE SKILL
async def create_skill(
    db: AsyncSession,
    name: str,
) -> Skill:
    """Create a new skill"""
    try:
        # Check if skill already exists
        result = await db.execute(
            select(Skill).where(Skill.name.ilike(name))
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Skill '{name}' already exists"
            )
        
        new_skill = Skill(name=name.strip())
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
        raise HTTPException(status_code=500, detail="Failed to create skill")


# ✅ GET ALL SKILLS
async def get_all_skills(db: AsyncSession) -> list[Skill]:
    """Get all skills"""
    try:
        result = await db.execute(select(Skill).order_by(Skill.name))
        return result.scalars().all()
    except Exception as e:
        print("Error in get_all_skills:", str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch skills")


# ✅ GET SKILL BY ID
async def get_skill_by_id(db: AsyncSession, skill_id: int) -> Skill:
    """Get skill by ID"""
    try:
        result = await db.execute(
            select(Skill).where(Skill.id == skill_id)
        )
        return result.scalar_one_or_none()
    except Exception as e:
        print("Error in get_skill_by_id:", str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch skill")


# ✅ UPDATE SKILL
async def update_skill(
    db: AsyncSession,
    skill_id: int,
    name: str = None,
) -> Skill:
    """Update a skill"""
    try:
        result = await db.execute(
            select(Skill).where(Skill.id == skill_id)
        )
        skill = result.scalar_one_or_none()
        
        if not skill:
            raise HTTPException(status_code=404, detail="Skill not found")
        
        if name:
            # Check if new name already exists
            existing = await db.execute(
                select(Skill).where(
                    (Skill.name.ilike(name)) & (Skill.id != skill_id)
                )
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=400,
                    detail=f"Skill '{name}' already exists"
                )
            skill.name = name.strip()
        
        db.add(skill)
        await db.commit()
        await db.refresh(skill)
        
        return skill
    
    except HTTPException as http_exc:
        await db.rollback()
        raise http_exc
    except Exception as e:
        await db.rollback()
        print("Error in update_skill:", str(e))
        raise HTTPException(status_code=500, detail="Failed to update skill")


# ✅ DELETE SKILL
async def delete_skill(db: AsyncSession, skill_id: int) -> bool:
    """Delete a skill"""
    try:
        result = await db.execute(
            select(Skill).where(Skill.id == skill_id)
        )
        skill = result.scalar_one_or_none()
        
        if not skill:
            raise HTTPException(status_code=404, detail="Skill not found")
        
        # Check if skill is being used by any professionals
        if skill.professionals:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete skill that is assigned to professionals. Unassign it first."
            )
        
        await db.delete(skill)
        await db.commit()
        
        return True
    
    except HTTPException as http_exc:
        await db.rollback()
        raise http_exc
    except Exception as e:
        await db.rollback()
        print("Error in delete_skill:", str(e))
        raise HTTPException(status_code=500, detail="Failed to delete skill")


# ✅ SEARCH SKILLS
async def search_skills(
    db: AsyncSession,
    query: str,
    skip: int = 0,
    limit: int = 10
) -> list[Skill]:
    """Search skills by name"""
    try:
        result = await db.execute(
            select(Skill)
            .where(Skill.name.ilike(f"%{query}%"))
            .order_by(Skill.name)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    except Exception as e:
        print("Error in search_skills:", str(e))
        raise HTTPException(status_code=500, detail="Failed to search skills")
