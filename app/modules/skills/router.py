from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.database import get_db
from app.modules.skills import service
from app.modules.skills.schemas import SkillResponse, SkillCreate, SkillUpdate

skill_router = APIRouter(prefix="/skills", tags=["Skills"])


# ✅ CREATE SKILL (ADMIN ONLY)
@skill_router.post("/", response_model=SkillResponse)
async def create_skill(
    data: SkillCreate,
    db: AsyncSession = Depends(get_db)
):
    result = await service.create_skill(db=db, data=data)
    return result


# ✅ GET ALL SKILLS
@skill_router.get("/", response_model=list[SkillResponse])
async def get_all_skills(db: AsyncSession = Depends(get_db)):
    return await service.get_all_skills(db=db)


# ✅ UPDATE SKILL
@skill_router.put("/{skill_id}", response_model=SkillResponse)
async def update_skill(
    skill_id: int,
    data: SkillUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await service.update_skill(db=db, skill_id=skill_id, data=data)

    if not result:
        raise HTTPException(status_code=404, detail="Skill not found")

    return result


# ❌ DELETE SKILL
@skill_router.delete("/{skill_id}")
async def delete_skill(
    skill_id: int,
    db: AsyncSession = Depends(get_db)
):
    success = await service.delete_skill(db=db, skill_id=skill_id)

    if not success:
        raise HTTPException(status_code=404, detail="Skill not found")

    return {"message": "Skill deleted successfully"}