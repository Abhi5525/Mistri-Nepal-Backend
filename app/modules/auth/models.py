from sqlalchemy import Boolean, column, Integer, String, DateTime
from sqlalchemy import func
from app.core.db.database import Base 

class User(Base):
    __tablename__ = "users"

    id = column(Integer, primary_key=True, index=True)
    phone_number = column(String(10), unique=True, index=True, nullable=False)
    email = column(String(255), unique=True, index=True, nullable=False)
    full_name = column(String(255), nullable=False)
    password = column(String(255), nullable=False)
    is_client = column(Boolean, default=True)
    is_professional = column(Boolean, default=False)
    is_active = column(Boolean, default=True)
    is_staff = column(Boolean, default=False)
    is_superuser = column(Boolean, default=False)
    fcm_token = column(String(255), nullable=True)
    created_at = column(DateTime(timezone=True), server_default=func.now())
    updated_at = column(DateTime(timezone=True), onupdate=func.now())
    last_login = column(DateTime(timezone=True), nullable=True)
    def __repr__(self):
        return f"<User(id={self.id}, phone_number='{self.phone_number}', email='{self.email}', full_name='{self.full_name}')>"
   