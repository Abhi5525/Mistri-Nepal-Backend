from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enum.file_type_enum import FileTypeEnum
from app.core.security.security import get_current_user
from app.core.db.database import get_db
from app.modules.auth.schemas import JwtPayload
from app.modules.file.service import delete_file, save_file, update_file

file_router = APIRouter(
    prefix="/file",
    tags=["Files"],
)


@file_router.post("/upload", summary="Upload a file")
async def upload_route(
    file: UploadFile = File(...),
    file_type: FileTypeEnum = Form(...),  # 👈 now body (form-data)
    current_user: JwtPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a file and return its URL.
    """
    file_info = await save_file(
        db=db, file=file, uploaded_by=current_user.sub, file_type=file_type
    )
    return file_info


@file_router.patch("/update/{file_id}")
async def update_route(
    file_id: str,
    file: UploadFile = File(...),
    current_user: JwtPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a file and return its new URL.
    """
    updated_file = await update_file(
        db=db,
        file=file,
        file_id=file_id,
        current_user_id=current_user.sub,
    )
    return updated_file


@file_router.delete("/delete/{file_id}", summary="Delete a file",)
async def delete_route(
    file_id: str,
    current_user: JwtPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a file.
    """
    await delete_file(db=db, file_ids=file_id)
    return {"detail": "File deleted successfully"}


# @router.post("/upload/profile", summary="Upload a profile file")
# async def upload_profile_route(
#     file: UploadFile = File(...),
#     file_type: FileTypeEnum = Form(FileTypeEnum.HOSPITAL),  # 👈 now body (form-data)
#     current_user: JwtPayload = Depends(get_current_user),
#     db: AsyncSession = Depends(get_db),
# ):
#     """
#     Upload a file and return its URL.
#     """
#     file_info = await save_file(
#         db=db, file=file, uploaded_by=current_user.sub, file_type=file_type
#     )
#     return file_info
