import math
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enum.role_enum import RoleEnum
from app.common.pagination import PaginatedResponse, PaginationMeta
from app.core.db.database import get_db
from app.core.security.authorization import authorize
from app.core.security.security import get_current_user
from app.modules.auth.schemas import JwtPayload
from app.modules.professional_applications.schemas import (
    ProfessionalApplicationCreate,
    ProfessionalApplicationFilterQuery,
    ProfessionalApplicationResponse,
)
from app.modules.professional_applications.service import (
    create_professional_application,
    get_all_professional_applications,
)

professional_application_router = APIRouter(
    prefix="/professionalApplication",
    tags=["Professional Applications"],
)


@professional_application_router.post(
    "",
    response_model=ProfessionalApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a professional application",
)
async def apply_professional(
    data: ProfessionalApplicationCreate,
    current_user: JwtPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _=Depends(authorize),
):
    """
    Submit an application to become a professional.
    Validates file references and prevents duplicate submissions.
    """
    return await create_professional_application(
        db=db,
        user_id=current_user.sub,
        data=data,
    )


@professional_application_router.get(
    "",
    response_model=PaginatedResponse[list[ProfessionalApplicationResponse]],
    summary="Get all professional applications (Admin Only)",
)
async def get_all_applications(
    filter_query: ProfessionalApplicationFilterQuery = Depends(),
    current_user: JwtPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _=Depends(authorize),
):
    """
    Retrieve all professional applications with pagination and filters (name/email, status).
    Only accessible by Admin.
    """
    applications, total_records = await get_all_professional_applications(
        db=db, filter_query=filter_query
    )

    total_pages = math.ceil(total_records / filter_query.size) if total_records > 0 else 0

    return PaginatedResponse[list[ProfessionalApplicationResponse]](
        message="Professional applications retrieved successfully",
        data=applications,
        paginationMeta=PaginationMeta(
            totalPage=total_pages,
            currentPage=filter_query.page,
            pageSize=filter_query.size,
            totalRecords=total_records,
        ),
    )
