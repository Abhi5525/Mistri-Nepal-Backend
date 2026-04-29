from typing import TYPE_CHECKING, List

from app.common.models.timestamp_mixin import TimestampMixin
from app.core.db.database import Base 
from sqlalchemy import String, ForeignKey
from sqlalchemy.dialects.postgresql import ENUM as SQLEnum ,JSONB
from sqlalchemy.orm import Mapped, relationship, mapped_column
from app.common.enum.role_enum import RoleEnum

if TYPE_CHECKING:
    from app.modules.users.models import User
class Authorization(Base, TimestampMixin):
    __tablename__ = "authorization"
    id: Mapped[str] = mapped_column(String(8), primary_key=True, index=True)
    role_id: Mapped[str] = mapped_column(ForeignKey("role.id"), nullable=False)
    path: Mapped[str] = mapped_column(String, nullable=False)
    methods: Mapped[List[str]] = mapped_column(JSONB, nullable=False)

    # Use string reference
    role: Mapped["Role"] = relationship(back_populates="authorization")


class Role(Base, TimestampMixin):
    __tablename__ = "role"

    id: Mapped[str] = mapped_column(String(8), primary_key=True, index=True)
    role: Mapped[RoleEnum] = mapped_column(
        SQLEnum(RoleEnum, name="role_enum"), nullable=False
    )
    description: Mapped[str] = mapped_column(String, nullable=True)

    # Use string reference to avoid circular import
    users: Mapped[List["User"]] = relationship(
        back_populates="role", cascade="all, delete"
    )
    authorization: Mapped[List["Authorization"]] = relationship(
        back_populates="role", cascade="all, delete"
    )
    