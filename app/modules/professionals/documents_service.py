from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, UploadFile

from app.core.utils.string_utils import StringUtils
from app.modules.professionals.documents_model import ProfessionalDocument
from app.modules.professionals.models import ProfessionalProfile
from app.modules.file.service import save_file
from app.common.enum.file_type_enum import FileTypeEnum
from datetime import datetime


# ✅ UPLOAD PROFESSIONAL DOCUMENT
async def upload_professional_document(
    db: AsyncSession,
    professional_id: str,
    file: UploadFile,
    document_type: str,
    user_id: str,
) -> ProfessionalDocument:
    """Upload a document for a professional profile"""
    try:
        # Check if professional exists
        prof_result = await db.execute(
            select(ProfessionalProfile).where(ProfessionalProfile.id == professional_id)
        )
        professional = prof_result.scalar_one_or_none()
        
        if not professional:
            raise HTTPException(status_code=404, detail="Professional profile not found")
        
        # Only professional can upload their own documents
        if professional.user_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="You can only upload documents for your own profile"
            )
        
        # Map document type to file type enum
        file_type_map = {
            "CITIZENSHIP_FRONT": FileTypeEnum.CITIZENSHIP_FRONT,
            "CITIZENSHIP_BACK": FileTypeEnum.CITIZENSHIP_BACK,
            "CERTIFICATE": FileTypeEnum.MISTRI_CERTIFICATE,
        }
        
        if document_type not in file_type_map:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid document type. Allowed: {', '.join(file_type_map.keys())}"
            )
        
        file_type = file_type_map[document_type]
        
        # Check if document of this type already exists
        existing = await db.execute(
            select(ProfessionalDocument).where(
                (ProfessionalDocument.professional_id == professional_id) &
                (ProfessionalDocument.document_type == document_type)
            )
        )
        existing_doc = existing.scalar_one_or_none()
        
        if existing_doc:
            raise HTTPException(
                status_code=400,
                detail=f"Document of type '{document_type}' already uploaded. Delete or update the existing one."
            )
        
        # Upload file using file service
        file_obj = await save_file(
            db=db,
            file=file,
            uploaded_by=user_id,
            file_type=file_type
        )
        
        # Create professional document record
        doc_id = "DOC_" + StringUtils.randomAlphaNumeric(10)
        new_doc = ProfessionalDocument(
            doc_id=doc_id,
            professional_id=professional_id,
            file_id=file_obj.file_id,
            document_type=document_type,
            verified=False,
        )
        
        db.add(new_doc)
        await db.commit()
        await db.refresh(new_doc)
        
        return new_doc
    
    except HTTPException as http_exc:
        await db.rollback()
        raise http_exc
    except Exception as e:
        await db.rollback()
        print("Error in upload_professional_document:", str(e))
        raise HTTPException(status_code=500, detail="Failed to upload document")


# ✅ GET PROFESSIONAL DOCUMENTS
async def get_professional_documents(
    db: AsyncSession,
    professional_id: str,
) -> list[ProfessionalDocument]:
    """Get all documents for a professional"""
    try:
        result = await db.execute(
            select(ProfessionalDocument)
            .options(selectinload(ProfessionalDocument.file))
            .where(ProfessionalDocument.professional_id == professional_id)
            .order_by(ProfessionalDocument.created_at.desc())
        )
        return result.scalars().all()
    except Exception as e:
        print("Error in get_professional_documents:", str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch documents")


# ✅ DELETE PROFESSIONAL DOCUMENT
async def delete_professional_document(
    db: AsyncSession,
    doc_id: str,
    professional_id: str,
    user_id: str,
) -> bool:
    """Delete a professional document"""
    try:
        result = await db.execute(
            select(ProfessionalDocument).where(
                (ProfessionalDocument.doc_id == doc_id) &
                (ProfessionalDocument.professional_id == professional_id)
            )
        )
        doc = result.scalar_one_or_none()
        
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check if user owns this professional profile
        prof_result = await db.execute(
            select(ProfessionalProfile).where(ProfessionalProfile.id == professional_id)
        )
        professional = prof_result.scalar_one_or_none()
        
        if professional.user_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="You can only delete documents from your own profile"
            )
        
        # Delete from file service will be handled by cascade
        await db.delete(doc)
        await db.commit()
        
        return True
    
    except HTTPException as http_exc:
        await db.rollback()
        raise http_exc
    except Exception as e:
        await db.rollback()
        print("Error in delete_professional_document:", str(e))
        raise HTTPException(status_code=500, detail="Failed to delete document")


# ✅ VERIFY PROFESSIONAL DOCUMENT (ADMIN)
async def verify_professional_document(
    db: AsyncSession,
    doc_id: str,
    admin_id: str,
    verified: bool,
) -> ProfessionalDocument:
    """Verify or reject a professional document (admin only)"""
    try:
        result = await db.execute(
            select(ProfessionalDocument).where(ProfessionalDocument.doc_id == doc_id)
        )
        doc = result.scalar_one_or_none()
        
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        doc.verified = verified
        if verified:
            doc.verified_at = datetime.now()
        else:
            doc.verified_at = None
        
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
        
        return doc
    
    except HTTPException as http_exc:
        await db.rollback()
        raise http_exc
    except Exception as e:
        await db.rollback()
        print("Error in verify_professional_document:", str(e))
        raise HTTPException(status_code=500, detail="Failed to verify document")


# ✅ GET UNVERIFIED DOCUMENTS (ADMIN)
async def get_unverified_documents(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 10,
) -> list[ProfessionalDocument]:
    """Get all unverified documents for admin review"""
    try:
        result = await db.execute(
            select(ProfessionalDocument)
            .options(
                selectinload(ProfessionalDocument.file),
                selectinload(ProfessionalDocument.professional)
            )
            .where(ProfessionalDocument.verified == False)
            .order_by(ProfessionalDocument.created_at)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    except Exception as e:
        print("Error in get_unverified_documents:", str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch unverified documents")
