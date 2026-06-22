from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.models.timestamp_mixin import TimestampMixin
from app.core.db.database import Base

if TYPE_CHECKING:
    from app.modules.professionals.models import ProfessionalProfile
    from app.modules.file.models import File


class ProfessionalDocument(Base, TimestampMixin):
    """Professional profile documents (citizenship, certificates, etc)"""
    __tablename__ = "professional_documents"

    doc_id: Mapped[str] = mapped_column(String(13), primary_key=True, index=True)

    professional_id: Mapped[str] = mapped_column(
        ForeignKey("professional_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    file_id: Mapped[str] = mapped_column(
        ForeignKey("file.file_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    document_type: Mapped[str] = mapped_column(String(50), nullable=False)  # CITIZENSHIP_FRONT, CITIZENSHIP_BACK, CERTIFICATE, etc

    verified: Mapped[bool] = mapped_column(default=False)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    professional: Mapped["ProfessionalProfile"] = relationship(
        back_populates="documents"
    )
    file: Mapped["File"] = relationship()

    def __repr__(self):
        return f"<ProfessionalDocument(id={self.doc_id}, document_type='{self.document_type}')>"
