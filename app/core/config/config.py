from pydantic_settings import BaseSettings
from typing import List
from pydantic import field_validator

class Settings(BaseSettings):
    """Application configuration settings"""
    
    # App
    APP_NAME: str = "Mistri Nepal API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Security
    BCRYPT_ROUNDS: int = 12
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 5242880  # 5MB
    UPLOAD_DIR: str = "./uploads"
    
    # Firebase
    FIREBASE_CREDENTIALS_PATH: str = "./serviceAccountKey.json"
    
    # Cloudinary settings
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str
    CLOUDINARY_FOLDER: str 
    
    # eSewa
    ESEWA_MERCHANT_CODE: str = "EPAYTEST"
    ESEWA_SECRET_KEY: str = "8gBm/:&EnhH.1/q"
    ESEWA_BASE_URL: str = "https://rc-epay.esewa.com.np/api/epay/main/v2/form"
    
    @field_validator('ALLOWED_ORIGINS', mode='before')
    @classmethod
    def parse_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.strip('[]').split(',')]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
