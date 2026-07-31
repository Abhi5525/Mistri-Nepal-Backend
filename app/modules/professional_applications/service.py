from datetime import datetime, timezone
from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.common.enum.role_enum import RoleEnum
from app.core.utils.string_utils import StringUtils
from app.modules.auth.models import Role
from app.modules.file.models import File
from app.modules.professional_applications.models import (
    ProfessionalApplication,
    ApplicationStatusEnum,
)
from app.modules.professional_applications.schemas import (
    ProfessionalApplicationCreate,
    ProfessionalApplicationFilterQuery,
    ProfessionalApplicationUpdateStatus,
)
from app.modules.professionals.models import ProfessionalProfile
from app.modules.skills.models import Skill
from app.modules.users.models import User


async def create_professional_application(
    db: AsyncSession,
    user_id: str,
    data: ProfessionalApplicationCreate,
) -> ProfessionalApplication:
    """
    Submits a new professional application after validating file references,
    skills, and checking for existing applications/profiles.
    """
    try:
        # 1. Check for existing professional profile
        existing_profile = await db.execute(
            select(ProfessionalProfile).where(ProfessionalProfile.user_id == user_id)
        )
        if existing_profile.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a registered professional",
            )

        # 2. Check for duplicate application
        existing_app = await db.execute(
            select(ProfessionalApplication).where(ProfessionalApplication.user_id == user_id)
        )
        if existing_app.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Professional application has already been submitted for this user",
            )

        # 3. Validate existence of referenced files
        file_ids = [
            data.profile_image_id,
            data.citizenship_front_id,
            data.citizenship_back_id,
        ]
        files_result = await db.execute(
            select(File).where(File.file_id.in_(file_ids))
        )
        found_files = {file.file_id for file in files_result.scalars().all()}

        missing_files = set(file_ids) - found_files
        if missing_files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file reference(s): {', '.join(missing_files)}",
            )

        # 4. Validate skills if provided
        selected_skills = []
        if data.skill_ids:
            skills_result = await db.execute(
                select(Skill).where(Skill.id.in_(data.skill_ids))
            )
            selected_skills = list(skills_result.scalars().all())
            found_skill_ids = {s.id for s in selected_skills}
            missing_skill_ids = set(data.skill_ids) - found_skill_ids
            if missing_skill_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid skill ID(s): {', '.join(map(str, missing_skill_ids))}",
                )

        # 5. Generate unique ID with PA_ prefix using StringUtils
        application_id = f"PA_{StringUtils.randomAlphaNumeric(10)}"

        # 6. Create entity
        new_application = ProfessionalApplication(
            professional_application_id=application_id,
            user_id=user_id,
            email=data.email,
            province=data.province,
            district=data.district,
            municipality=data.municipality,
            ward=data.ward,
            experience=data.experience,
            about_yourself=data.about_yourself,
            other_skills=data.other_skills,
            base_rate=data.base_rate,
            latitude=data.latitude,
            longitude=data.longitude,
            profile_image_id=data.profile_image_id,
            citizenship_front_id=data.citizenship_front_id,
            citizenship_back_id=data.citizenship_back_id,
            status=ApplicationStatusEnum.PENDING,
            skills=selected_skills,
        )

        db.add(new_application)
        await db.commit()

        # Fetch with relationships for response
        query = (
            select(ProfessionalApplication)
            .options(
                selectinload(ProfessionalApplication.user),
                selectinload(ProfessionalApplication.profile_image),
                selectinload(ProfessionalApplication.citizenship_front),
                selectinload(ProfessionalApplication.citizenship_back),
                selectinload(ProfessionalApplication.skills),
            )
            .where(ProfessionalApplication.professional_application_id == application_id)
        )
        result = await db.execute(query)
        return result.scalar_one()

    except HTTPException as http_exc:
        await db.rollback()
        raise http_exc
    except Exception as e:
        await db.rollback()
        print("Error in create_professional_application:", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit professional application",
        )


async def get_all_professional_applications(
    db: AsyncSession,
    filter_query: ProfessionalApplicationFilterQuery,
) -> tuple[list[ProfessionalApplication], int]:
    """
    Retrieve paginated professional applications with optional filtering
    by applicant name/email and status.
    """
    try:
        query = (
            select(ProfessionalApplication)
            .join(ProfessionalApplication.user)
            .options(
                selectinload(ProfessionalApplication.user),
                selectinload(ProfessionalApplication.profile_image),
                selectinload(ProfessionalApplication.citizenship_front),
                selectinload(ProfessionalApplication.citizenship_back),
                selectinload(ProfessionalApplication.skills),
            )
        )

        count_query = (
            select(func.count(ProfessionalApplication.professional_application_id))
            .join(ProfessionalApplication.user)
        )

        # Filter by applicant name or email if provided
        if filter_query.name and filter_query.name.strip():
            search_term = f"%{filter_query.name.strip()}%"
            name_condition = or_(
                User.full_name.ilike(search_term),
                ProfessionalApplication.email.ilike(search_term),
            )
            query = query.where(name_condition)
            count_query = count_query.where(name_condition)

        # Filter by application status if provided
        if filter_query.status:
            status_condition = ProfessionalApplication.status == filter_query.status
            query = query.where(status_condition)
            count_query = count_query.where(status_condition)

        # Execute total record count
        count_result = await db.execute(count_query)
        total_records = count_result.scalar_one()

        # Apply ordering and pagination
        query = (
            query.order_by(ProfessionalApplication.created_at.desc())
            .offset(filter_query.offset)
            .limit(filter_query.size)
        )

        result = await db.execute(query)
        applications = list(result.scalars().all())

        return applications, total_records

    except Exception as e:
        print("Error in get_all_professional_applications:", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch professional applications",
        )


async def respond_to_professional_application(
    db: AsyncSession,
    application_id: str,
    admin_user_id: str,
    data: ProfessionalApplicationUpdateStatus,
) -> ProfessionalApplication:
    """
    Responds to a PENDING professional application (Admin only).
    - If APPROVED: Creates a new ProfessionalProfile for the user and updates user role to PROFESSIONAL.
    - If REJECTED: Updates status with rejection reason/description.
    - Ensures only PENDING applications can be responded to.
    """
    try:
        # 1. Fetch application with relationships
        query = (
            select(ProfessionalApplication)
            .options(
                selectinload(ProfessionalApplication.user),
                selectinload(ProfessionalApplication.profile_image),
                selectinload(ProfessionalApplication.citizenship_front),
                selectinload(ProfessionalApplication.citizenship_back),
                selectinload(ProfessionalApplication.skills),
            )
            .where(ProfessionalApplication.professional_application_id == application_id)
        )
        result = await db.execute(query)
        application = result.scalar_one_or_none()

        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Professional application not found",
            )

        # 2. Ensure only PENDING applications can be responded to
        if application.status != ApplicationStatusEnum.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only PENDING applications can be responded to. Current application status is '{application.status.value}'.",
            )

        # 3. Validate target status (must be APPROVED or REJECTED)
        if data.status == ApplicationStatusEnum.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Target status must be APPROVED or REJECTED",
            )

        # 4. Handle REJECTED
        if data.status == ApplicationStatusEnum.REJECTED:
            if not data.reason or not data.reason.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Rejection reason is required when rejecting an application",
                )

            application.status = ApplicationStatusEnum.REJECTED
            application.rejection_reason = data.reason.strip()
            application.reviewed_by = admin_user_id
            application.reviewed_at = datetime.now(timezone.utc)

            db.add(application)
            await db.commit()

            refreshed_res = await db.execute(query)
            return refreshed_res.scalar_one()

        # 5. Handle APPROVED (Accepting)
        if data.status == ApplicationStatusEnum.APPROVED:
            # Check if professional profile already exists
            existing_profile_res = await db.execute(
                select(ProfessionalProfile).where(ProfessionalProfile.user_id == application.user_id)
            )
            if existing_profile_res.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A professional profile already exists for this user",
                )

            # Create ProfessionalProfile for user
            new_profile = ProfessionalProfile(
                user_id=application.user_id,
                profile_image_id=application.profile_image_id,
                citizenship_front_id=application.citizenship_front_id,
                citizenship_back_id=application.citizenship_back_id,
                experience=application.experience,
                about_yourself=application.about_yourself,
                other_skills=application.other_skills,
                base_rate=application.base_rate,
                latitude=application.latitude,
                longitude=application.longitude,
                skills=list(application.skills),
            )
            db.add(new_profile)

            # Promote User role to PROFESSIONAL
            professional_role_res = await db.execute(
                select(Role).where(Role.role == RoleEnum.PROFESSIONAL)
            )
            professional_role = professional_role_res.scalar_one_or_none()
            if professional_role:
                user_res = await db.execute(
                    select(User).where(User.id == application.user_id)
                )
                user_obj = user_res.scalar_one_or_none()
                if user_obj:
                    user_obj.role_id = professional_role.id
                    db.add(user_obj)

            # Update application status
            application.status = ApplicationStatusEnum.APPROVED
            application.rejection_reason = None
            application.reviewed_by = admin_user_id
            application.reviewed_at = datetime.now(timezone.utc)

            db.add(application)
            await db.commit()

            # Re-fetch application with relationships
            refreshed_result = await db.execute(query)
            return refreshed_result.scalar_one()

    except HTTPException as http_exc:
        await db.rollback()
        raise http_exc
    except Exception as e:
        await db.rollback()
        print("Error in respond_to_professional_application:", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process application response",
        )
