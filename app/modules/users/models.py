from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.db.database import Base
if TYPE_CHECKING:
    from app.modules.auth.models import Role

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    phone_number: Mapped[str] = mapped_column(
        String(10), unique=True, index=True, nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)

    is_client: Mapped[bool] = mapped_column(Boolean, default=True)
    is_professional: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_staff: Mapped[bool] = mapped_column(Boolean, default=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)

    fcm_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # 🔥 Foreign key to Role (one role per user)
    role_id: Mapped[str] = mapped_column(
        ForeignKey("role.id"), nullable=False
    )

    # 🔥 Relationship (many users → one role)
    role: Mapped["Role"] = relationship(back_populates="users")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self):
        return (
            f"<User(id={self.id}, phone_number='{self.phone_number}', "
            f"email='{self.email}', full_name='{self.full_name}')>"
        )