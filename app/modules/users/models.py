from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.models.timestamp_mixin import TimestampMixin
from app.core.db.database import Base
if TYPE_CHECKING:
    from app.modules.auth.models import Role
    from app.modules.file.models import File 

class User(Base, TimestampMixin):
    __tablename__ = "user"

    id: Mapped[str] = mapped_column(String(13), primary_key=True, index=True)

    phone_number: Mapped[str] = mapped_column(
        String(10), unique=True, index=True, nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=True
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    fcm_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # 🔥 Foreign key to Role (one role per user)
    role_id: Mapped[str] = mapped_column(
        ForeignKey("role.id"), nullable=False
    )

    # 🔥 Relationship (many users → one role)
    role: Mapped["Role"] = relationship(back_populates="users")
    files: Mapped[list["File"]] = relationship(back_populates="user")
    
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self):
        return (
            f"<User(id={self.id}, phone_number='{self.phone_number}', "
            f"email='{self.email}', full_name='{self.full_name}')>"
        )