"""
Location and analytics models
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime, date
from enum import Enum
import uuid

class Location(BaseModel):
    """Geographic location information"""
    country: str
    state: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class FakeProductLocation(BaseModel):
    """Fake product location record"""
    location_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scan_id: str
    product_id: str
    product_name: str
    brand_name: str
    
    # Location data (anonymized)
    location: Location
    
    # User consent
    user_consent: bool = True
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class LocationRequest(BaseModel):
    """Location sharing request from user"""
    scan_id: str
    country: str
    state: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    consent: bool = True

class LocationStats(BaseModel):
    """Location-based statistics"""
    location: str
    fake_count: int
    percentage: float

class LocationHeatmapResponse(BaseModel):
    """Location heatmap data"""
    countries: List[LocationStats]
    states: List[LocationStats]
    cities: List[LocationStats]
    districts: List[LocationStats]
    total_fake_products: int

class AnalyticsMetric(str, Enum):
    """Analytics metric types"""
    TOTAL_SCANS = "total_scans"
    FAKE_DETECTIONS = "fake_detections"
    REAL_DETECTIONS = "real_detections"
    SUSPICIOUS_DETECTIONS = "suspicious_detections"
    UNIQUE_USERS = "unique_users"
    PRODUCTS_SCANNED = "products_scanned"

class DailyAnalytics(BaseModel):
    """Daily analytics record"""
    date: date
    metric_type: AnalyticsMetric
    value: int
    metadata: Optional[Dict] = {}
    
    class Config:
        use_enum_values = True
        json_encoders = {
            date: lambda v: v.isoformat()
        }

class ProductAnalytics(BaseModel):
    """Product-specific analytics"""
    product_id: str
    product_name: str
    brand_name: str
    total_scans: int
    fake_count: int
    real_count: int
    suspicious_count: int
    fake_percentage: float

class DashboardStats(BaseModel):
    """Overall dashboard statistics"""
    total_scans: int
    total_fake: int
    total_real: int
    total_suspicious: int
    fake_percentage: float
    
    # Trends
    scans_today: int
    scans_this_week: int
    scans_this_month: int
    
    # Top fake products
    top_fake_products: List[ProductAnalytics]
    
    # Recent activity
    recent_fake_detections: int
    
class TemporalTrend(BaseModel):
    """Temporal trend data"""
    date: str
    fake_count: int
    real_count: int
    suspicious_count: int
    total_scans: int

class AnalyticsResponse(BaseModel):
    """Complete analytics response"""
    overview: DashboardStats
    temporal_trends: List[TemporalTrend]
    product_analytics: List[ProductAnalytics]
    location_distribution: LocationHeatmapResponse
