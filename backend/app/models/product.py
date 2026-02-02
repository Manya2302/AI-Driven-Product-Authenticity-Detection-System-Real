"""
Product model for database
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum
import uuid

class ProductCategory(str, Enum):
    """Product category enumeration"""
    BEVERAGES = "beverages"
    COSMETICS = "cosmetics"
    ELECTRONICS = "electronics"
    PHARMACEUTICALS = "pharmaceuticals"
    APPAREL = "apparel"
    FOOD = "food"
    ACCESSORIES = "accessories"
    OTHER = "other"

class ProductImageType(str, Enum):
    """Product image type"""
    FRONT = "front"
    BACK = "back"
    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"
    LABEL = "label"
    CAP_SEAL = "cap_seal"

class ProductImage(BaseModel):
    """Product image metadata"""
    image_type: ProductImageType
    file_path: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

class Product(BaseModel):
    """Product base model"""
    product_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    product_name: str = Field(..., min_length=2, max_length=200)
    category: ProductCategory
    brand_name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    
    # Multi-angle images
    images: List[ProductImage] = []
    
    # Metadata
    added_by: str  # Admin email
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    is_active: bool = True
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ProductCreate(BaseModel):
    """Product creation model"""
    product_name: str = Field(..., min_length=2, max_length=200)
    category: ProductCategory
    brand_name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None

class ProductFeatureProfile(BaseModel):
    """AI-extracted feature profile for a product"""
    product_id: str
    
    # Deep learning features (embeddings)
    visual_features: Dict[str, List[float]] = {}  # Key: image_type, Value: embedding vector
    
    # OCR extracted data
    extracted_texts: Dict[str, str] = {}  # Key: image_type, Value: extracted text
    brand_text_normalized: Optional[str] = None
    
    # Color and texture features
    dominant_colors: Dict[str, List[List[int]]] = {}  # RGB values
    color_histograms: Dict[str, List[float]] = {}
    
    # Shape and layout features
    edge_features: Dict[str, List[float]] = {}
    layout_patterns: Dict[str, Dict] = {}
    
    # Statistical features
    feature_statistics: Dict[str, float] = {}
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    model_version: str = "1.0.0"
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ProductResponse(BaseModel):
    """Product response model"""
    product_id: str
    product_name: str
    category: str
    brand_name: str
    description: Optional[str]
    images_count: int
    added_by: str
    created_at: datetime
    is_active: bool
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ProductListResponse(BaseModel):
    """Product list response"""
    products: List[ProductResponse]
    total: int
    page: int
    page_size: int
