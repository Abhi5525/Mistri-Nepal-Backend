from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ProfessionalDocumentResponse(BaseModel):
    """Professional document response"""
    model_config = ConfigDict(from_attributes=True)
    
    doc_id: str
    professional_id: str
    file_id: str
    document_type: str
    verified: bool
    verified_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class ProfessionalDocumentUploadResponse(BaseModel):
    """Response after document upload"""
    message: str = "Document uploaded successfully"
    data: ProfessionalDocumentResponse


class DocumentVerificationRequest(BaseModel):
    """Request to verify/reject a document"""
    verified: bool


class DocumentListResponse(BaseModel):
    """List of professional documents"""
    documents: list[ProfessionalDocumentResponse]
    total: int
