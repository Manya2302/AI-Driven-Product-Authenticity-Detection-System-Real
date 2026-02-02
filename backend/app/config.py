"""
Configuration settings for the AI Product Authenticity Detection System
"""
from pydantic_settings import BaseSettings
from pydantic import model_validator
from typing import Optional
import os
from pathlib import Path

class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "AI Product Authenticity Detection System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_URI: Optional[str] = None
    DATABASE_NAME: str = "product_authenticity_db"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production-make-it-very-long-and-random"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:3000",
        "https://orange-garbanzo-jjqg4pjx7pwc555-5173.app.github.dev",
        "https://orange-garbanzo-jjqg4pjx7pwc555-5174.app.github.dev",
        "https://orange-garbanzo-jjqg4pjx7pwc555-8000.app.github.dev"
    ]
    
    # File Storage
    UPLOAD_DIR: Path = Path("uploads")
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: set = {".jpg", ".jpeg", ".png", ".webp"}
    
    # AI Models
    MODEL_DIR: Path = Path("models")
    DEVICE: str = "cuda" if os.environ.get("CUDA_VISIBLE_DEVICES") else "cpu"
    
    # Vision Transformer Settings
    VIT_MODEL_NAME: str = "google/vit-base-patch16-224"
    FEATURE_DIM: int = 768
    
    # Siamese Network Settings
    SIAMESE_EMBEDDING_DIM: int = 512
    SIMILARITY_THRESHOLD: float = 0.75
    
    # Autoencoder Settings
    AUTOENCODER_LATENT_DIM: int = 256
    ANOMALY_THRESHOLD: float = 0.60
    
    # Decision Engine Weights
    VISUAL_SIMILARITY_WEIGHT: float = 0.40
    TEXT_VALIDATION_WEIGHT: float = 0.30
    ANOMALY_WEIGHT: float = 0.20
    PATTERN_CONSISTENCY_WEIGHT: float = 0.10
    
    # Classification Thresholds
    REAL_THRESHOLD: float = 0.75
    SUSPICIOUS_THRESHOLD: float = 0.40
    
    # OCR Settings
    OCR_LANGUAGES: list = ['en']
    OCR_GPU: bool = False
    
    # Image Processing
    IMAGE_SIZE: tuple = (224, 224)
    NORMALIZATION_MEAN: list = [0.485, 0.456, 0.406]
    NORMALIZATION_STD: list = [0.229, 0.224, 0.225]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"

    # Environment
    ENVIRONMENT: str = "development"
    
    # Admin
    DEFAULT_ADMIN_EMAIL: str = "admin@authenticity.ai"
    DEFAULT_ADMIN_PASSWORD: str = "Admin@123"  # Change in production
    
    @model_validator(mode="after")
    def _apply_mongodb_uri(self):
        if self.MONGODB_URI and self.MONGODB_URL == "mongodb://localhost:27017":
            object.__setattr__(self, "MONGODB_URL", self.MONGODB_URI)
        return self

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

# Global settings instance
settings = Settings()

# Create necessary directories
settings.UPLOAD_DIR.mkdir(exist_ok=True)
settings.MODEL_DIR.mkdir(exist_ok=True)
Path(settings.LOG_FILE).parent.mkdir(exist_ok=True)
