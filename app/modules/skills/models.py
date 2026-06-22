from typing import TYPE_CHECKING
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.database import Base

if TYPE_CHECKING:
    from app.modules.professionals.models import ProfessionalProfile


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    professionals: Mapped[list["ProfessionalProfile"]] = relationship(
        "ProfessionalProfile",
        secondary="professional_skills",
        back_populates="skills"
    )
    
    def __repr__(self):
        return f"<Skill(id={self.id}, name='{self.name}')>"