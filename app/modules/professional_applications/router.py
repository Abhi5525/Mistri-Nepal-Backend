import math

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.pagination import PaginatedResponse, PaginationMeta
from app.core.db.database import get_db
from app.core.security.authorization import authorize
from app.core.security.security import get_current_user
from app.modules.auth.schemas import JwtPayload
from app.modules.professional_applications.schemas import (
    ProfessionalApplicationCreate,
    ProfessionalApplicationFilterQuery,
    ProfessionalApplicationResponse,
    ProfessionalApplicationUpdateStatus,
)
from app.modules.professional_applications.service import (
    create_professional_application,
    get_all_professional_applications,
    get_user_professional_application,
    respond_to_professional_application,
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
    "/me",
    response_model=ProfessionalApplicationResponse,
    summary="Get professional application of logged-in user",
)
async def get_my_application(
    current_user: JwtPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _=Depends(authorize),
):
    """
    Fetch the professional application details submitted by the currently logged-in user.
    """
    application = await get_user_professional_application(
        db=db,
        user_id=current_user.sub,
    )
    return application


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

    total_pages = (
        math.ceil(total_records / filter_query.size) if total_records > 0 else 0
    )

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


@professional_application_router.patch(
    "/{application_id}/status",
    response_model=ProfessionalApplicationResponse,
    summary="Respond to a professional application (Admin Only)",
)
async def respond_application_status(
    application_id: str,
    data: ProfessionalApplicationUpdateStatus,
    current_user: JwtPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _=Depends(authorize),
):
    """
    Respond to a PENDING professional application by ID (Admin only).
    - Json body: status ('APPROVED' or 'REJECTED') and rejection_reason/description/reason.
    - If APPROVED: Creates ProfessionalProfile for the user and promotes user role to PROFESSIONAL.
    - If REJECTED: Updates application status with rejection reason.
    - Ensures only PENDING applications can be responded to.
    """
    return await respond_to_professional_application(
        db=db,
        application_id=application_id,
        admin_user_id=current_user.sub,
        data=data,
    )
