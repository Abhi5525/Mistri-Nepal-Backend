from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.database import get_db
from app.core.security.security import get_current_user
from app.modules.auth.schemas import JwtPayload
from app.modules.professional_applications.schemas import (
    ProfessionalApplicationCreate,
    ProfessionalApplicationResponse,
)
from app.modules.professional_applications.service import (
    create_professional_application,
)

professional_application_router = APIRouter(
    prefix="/professionalApplications",
    tags=["Professional Applications"],
)


@professional_application_router.post(
    "/",
    response_model=ProfessionalApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a professional application",
)
async def apply_professional(
    data: ProfessionalApplicationCreate,
    current_user: JwtPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
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
