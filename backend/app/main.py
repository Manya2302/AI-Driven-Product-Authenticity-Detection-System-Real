"""
Main FastAPI application
AI-Driven Product Authenticity Detection System
"""
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from loguru import logger

from .config import settings
from .database import Database
from .api import auth, admin, analysis, analytics

# Lifespan context manager for startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup
    logger.info("🚀 Starting AI Product Authenticity Detection System...")
    logger.info(f"Version: {settings.APP_VERSION}")
    logger.info(f"Environment: {'Development' if settings.DEBUG else 'Production'}")
    
    # Connect to database
    await Database.connect_db()
    
    logger.info("✅ Application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    await Database.close_db()
    logger.info("✅ Application shut down successfully")

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Advanced AI/ML system for detecting counterfeit products using computer vision and deep learning",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(analysis.router)
app.include_router(analytics.router)

# Mount static files
if settings.UPLOAD_DIR.exists():
    app.mount("/uploads", StaticFiles(directory=str(settings.UPLOAD_DIR)), name="uploads")

# Health check endpoint
@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint
    
    Returns:
        System health status
    """
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": "development" if settings.DEBUG else "production"
    }

# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint with API information
    
    Returns:
        API information
    """
    return {
        "message": "AI-Driven Product Authenticity Detection System API",
        "version": settings.APP_VERSION,
        "docs": "/api/docs" if settings.DEBUG else "Documentation disabled in production",
        "endpoints": {
            "authentication": "/api/auth",
            "admin": "/api/admin",
            "analysis": "/api/analysis",
            "analytics": "/api/analytics"
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
