from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.database import get_db
from app.core.security.security import get_current_user
from app.modules.auth.schemas import JwtPayload
from app.modules.skills import service
from app.modules.skills.schemas import SkillResponse, SkillCreate, SkillUpdate
from app.common.enum.role_enum import RoleEnum

skill_router = APIRouter(prefix="/skills", tags=["Skills"])


# ✅ CREATE SKILL (ADMIN ONLY)
@skill_router.post("/", response_model=SkillResponse)
async def create_skill(
    data: SkillCreate,
    current_user: JwtPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new skill (admin only)"""
    if current_user.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can create skills")
    
    result = await service.create_skill(db=db, name=data.name)
    return result


# ✅ GET ALL SKILLS
@skill_router.get("/", response_model=list[SkillResponse])
async def get_all_skills(db: AsyncSession = Depends(get_db)):
    """Get all available skills"""
    return await service.get_all_skills(db=db)


# ✅ GET SKILL BY ID
@skill_router.get("/{skill_id}", response_model=SkillResponse)
async def get_skill_by_id(
    skill_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get skill by ID"""
    result = await service.get_skill_by_id(db=db, skill_id=skill_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    return result


# ✅ SEARCH SKILLS
@skill_router.get("/search/{query}", response_model=list[SkillResponse])
async def search_skills(
    query: str,
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Search skills by name"""
    return await service.search_skills(db=db, query=query, skip=skip, limit=limit)


# ✅ UPDATE SKILL (ADMIN ONLY)
@skill_router.put("/{skill_id}", response_model=SkillResponse)
async def update_skill(
    skill_id: int,
    data: SkillUpdate,
    current_user: JwtPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a skill (admin only)"""
    if current_user.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can update skills")
    
    result = await service.update_skill(db=db, skill_id=skill_id, name=data.name)
    
    return result


# ✅ DELETE SKILL (ADMIN ONLY)
@skill_router.delete("/{skill_id}")
async def delete_skill(
    skill_id: int,
    current_user: JwtPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a skill (admin only)"""
    if current_user.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can delete skills")
    
    success = await service.delete_skill(db=db, skill_id=skill_id)
    
    return {"message": "Skill deleted successfully"}