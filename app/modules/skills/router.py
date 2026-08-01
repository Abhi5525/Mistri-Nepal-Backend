import math

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.pagination import PaginationMeta
from app.core.db.database import get_db
from app.core.security.authorization import authorize
from app.core.security.security import get_current_user
from app.modules.auth.schemas import JwtPayload
from app.modules.skills import service
from app.modules.skills.schemas import (
    PaginatedSkillResponse,
    SkillCreate,
    SkillFilterQuery,
    SkillResponse,
    SkillUpdate,
)

skill_router = APIRouter(prefix="/skills", tags=["Skills"])


# ✅ CREATE SKILL (ADMIN ONLY)
@skill_router.post("", response_model=SkillResponse)
async def create_skill(
    data: SkillCreate,
    db: AsyncSession = Depends(get_db),
    user: JwtPayload = Depends(get_current_user),
    _=Depends(authorize),
):
    result = await service.create_skill(db=db, name=data.name)
    return result


# ✅ GET ALL SKILLS (WITH PAGINATION AND NAME SEARCH)
@skill_router.get("", response_model=PaginatedSkillResponse)
async def get_all_skills(
    filter_query: SkillFilterQuery = Depends(), db: AsyncSession = Depends(get_db)
):
    skills, total_records = await service.get_all_skills(
        db=db, filter_query=filter_query
    )

    total_pages = (
        math.ceil(total_records / filter_query.size) if total_records > 0 else 0
    )

    return PaginatedSkillResponse(
        message="Skills retrieved successfully",
        data=skills,
        paginationMeta=PaginationMeta(
            totalPage=total_pages,
            currentPage=filter_query.page,
            pageSize=filter_query.size,
            totalRecords=total_records,
        ),
    )


# ✅ UPDATE SKILL
@skill_router.patch("/{skill_id}", response_model=SkillResponse)
async def update_skill(
    skill_id: int,
    data: SkillUpdate,
    db: AsyncSession = Depends(get_db),
    user: JwtPayload = Depends(get_current_user),
    _=Depends(authorize),
):
    """Get skill by ID"""
    result = await service.get_skill_by_id(db=db, skill_id=skill_id)

    if not result:
        raise HTTPException(status_code=404, detail="Skill not found")

    return result



# ✅ DELETE SKILL (ADMIN ONLY)
@skill_router.delete("/{skill_id}")
async def delete_skill(
    skill_id: int,
    db: AsyncSession = Depends(get_db),
    user: JwtPayload = Depends(get_current_user),
    _=Depends(authorize),
):
    """Delete a skill (admin only)"""
    success = await service.delete_skill(db=db, skill_id=skill_id)

    return {"message": "Skill deleted successfully"}
