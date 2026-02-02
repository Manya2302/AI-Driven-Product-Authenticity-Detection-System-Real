"""
Scan and analysis models
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum
import uuid

class ScanStatus(str, Enum):
    """Scan processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Classification(str, Enum):
    """Product authenticity classification"""
    LIKELY_REAL = "likely_real"
    SUSPICIOUS = "suspicious"
    LIKELY_FAKE = "likely_fake"

class Scan(BaseModel):
    """Scan request model"""
    scan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    product_id: str  # Product being scanned
    
    # Uploaded image
    image_path: str
    
    # Status
    status: ScanStatus = ScanStatus.PENDING
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ScanResult(BaseModel):
    """Analysis result for a scan"""
    scan_id: str
    
    # Classification
    classification: Classification
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    
    # Detailed scores
    visual_similarity_score: float = Field(..., ge=0.0, le=1.0)
    text_validation_score: float = Field(..., ge=0.0, le=1.0)
    anomaly_score: float = Field(..., ge=0.0, le=1.0)
    pattern_consistency_score: float = Field(..., ge=0.0, le=1.0)
    
    # Generic authenticity AI (Brain 3)
    generic_authenticity_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    # Deception detection (Phase 4)
    deception_probability: Optional[float] = Field(None, ge=0.0, le=1.0)
    is_likely_lookalike: Optional[bool] = None
    
    # Explanations
    explanations: List[str] = []
    
    # Visual evidence
    gradcam_heatmap_path: Optional[str] = None
    suspicious_regions: List[Dict] = []  # Bounding boxes of suspicious areas
    
    # Text analysis
    extracted_text: Optional[str] = None
    brand_text_similarity: Optional[float] = None
    text_issues: List[str] = []
    
    # Location sharing requirement (Phase 7)
    requires_location_sharing: Optional[bool] = None
    
    # Metadata
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)
    processing_time_seconds: Optional[float] = None
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ScanRequest(BaseModel):
    """User scan request"""
    product_id: str

class ScanResponse(BaseModel):
    """Scan response with analysis"""
    scan_id: str
    product_name: str
    classification: str
    confidence_score: float
    
    # Detailed analysis
    visual_similarity: float
    text_validation: float
    anomaly_detection: float
    pattern_consistency: float
    
    # Generic authenticity score (Brain 3)
    generic_authenticity: Optional[float] = None
    
    # Deception detection
    deception_probability: Optional[float] = None
    is_lookalike: Optional[bool] = None
    
    # Explanations
    verdict: str
    key_findings: List[str]
    recommendations: List[str]
    
    # Visual evidence
    has_heatmap: bool
    heatmap_url: Optional[str] = None
    
    # Location sharing requirement
    requires_location_sharing: Optional[bool] = None
    
    # Timestamp
    analyzed_at: str
    
class ScanHistoryItem(BaseModel):
    """Scan history item for user"""
    scan_id: str
    product_name: str
    brand_name: str
    classification: str
    confidence_score: float
    timestamp: str
    image_thumbnail: Optional[str] = None

class ScanHistoryResponse(BaseModel):
    """User scan history response"""
    scans: List[ScanHistoryItem]
    total: int
    page: int
    page_size: int
