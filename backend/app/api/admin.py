"""
Admin API endpoints for product and user management
"""
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List, Optional
import uuid
from datetime import datetime
from pathlib import Path
import shutil

from ..models.user import UserInDB, UserResponse, UserUpdate
from ..models.product import (
    Product, ProductCreate, ProductResponse, ProductListResponse,
    ProductImage, ProductImageType, ProductFeatureProfile
)
from ..database import (
    get_users_collection, get_products_collection,
    get_product_features_collection
)
from ..core.dependencies import get_current_admin
from ..config import settings
from ...ai_models import preprocessor, feature_extractor

router = APIRouter(prefix="/api/admin", tags=["Admin"])

# ==================== PRODUCT MANAGEMENT ====================

@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_name: str = Form(...),
    category: str = Form(...),
    brand_name: str = Form(...),
    description: Optional[str] = Form(None),
    front_image: UploadFile = File(...),
    back_image: UploadFile = File(...),
    left_image: UploadFile = File(...),
    right_image: UploadFile = File(...),
    top_image: UploadFile = File(...),
    bottom_image: UploadFile = File(...),
    label_image: UploadFile = File(...),
    cap_seal_image: UploadFile = File(...),
    current_admin: UserInDB = Depends(get_current_admin)
):
    """
    Create new verified product with multi-angle images
    Admin only - extracts and stores AI features
    
    Args:
        product_name: Product name
        category: Product category
        brand_name: Brand name
        description: Optional description
        front_image: Front view image
        back_image: Back view image
        left_image: Left side image
        right_image: Right side image
        top_image: Top view image
        bottom_image: Bottom view image
        label_image: Label close-up
        cap_seal_image: Cap/seal image
        current_admin: Current admin user
        
    Returns:
        Created product information
    """
    products_collection = get_products_collection()
    features_collection = get_product_features_collection()
    
    # Generate product ID
    product_id = str(uuid.uuid4())
    
    # Prepare upload directory
    product_dir = settings.UPLOAD_DIR / "products" / product_id
    product_dir.mkdir(parents=True, exist_ok=True)
    
    # Image mapping
    image_files = {
        ProductImageType.FRONT: front_image,
        ProductImageType.BACK: back_image,
        ProductImageType.LEFT: left_image,
        ProductImageType.RIGHT: right_image,
        ProductImageType.TOP: top_image,
        ProductImageType.BOTTOM: bottom_image,
        ProductImageType.LABEL: label_image,
        ProductImageType.CAP_SEAL: cap_seal_image
    }
    
    # Save images and extract features
    saved_images = []
    extracted_features = {}
    
    for image_type, image_file in image_files.items():
        # Validate file extension
        file_ext = Path(image_file.filename).suffix.lower()
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file extension for {image_type.value}: {file_ext}"
            )
        
        # Save image
        file_path = product_dir / f"{image_type.value}{file_ext}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image_file.file, buffer)
        
        # Record image metadata
        saved_images.append(ProductImage(
            image_type=image_type,
            file_path=str(file_path.relative_to(settings.UPLOAD_DIR)),
            uploaded_at=datetime.utcnow()
        ))
        
        # Extract AI features
        try:
            image_tensor, original_image = preprocessor.preprocess_for_inference(str(file_path))
            features = feature_extractor.extract_comprehensive_features(image_tensor, original_image)
            extracted_features[image_type.value] = features
        except Exception as e:
            # Clean up on error
            shutil.rmtree(product_dir, ignore_errors=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to extract features from {image_type.value}: {str(e)}"
            )
    
    # Create product document
    product = Product(
        product_id=product_id,
        product_name=product_name,
        category=category,
        brand_name=brand_name,
        description=description,
        images=saved_images,
        added_by=current_admin.email,
        created_at=datetime.utcnow(),
        is_active=True
    )
    
    # Save to database
    await products_collection.insert_one(product.model_dump())
    
    # Create feature profile
    feature_profile = ProductFeatureProfile(
        product_id=product_id,
        visual_features=extracted_features,
        created_at=datetime.utcnow(),
        model_version="1.0.0"
    )
    
    await features_collection.insert_one(feature_profile.model_dump())
    
    # Return response
    return ProductResponse(
        product_id=product.product_id,
        product_name=product.product_name,
        category=product.category,
        brand_name=product.brand_name,
        description=product.description,
        images_count=len(saved_images),
        added_by=product.added_by,
        created_at=product.created_at,
        is_active=product.is_active
    )

@router.get("/products", response_model=ProductListResponse)
async def list_products(
    page: int = 1,
    page_size: int = 20,
    category: Optional[str] = None,
    search: Optional[str] = None,
    current_admin: UserInDB = Depends(get_current_admin)
):
    """
    List all products with pagination and filtering
    
    Args:
        page: Page number
        page_size: Items per page
        category: Filter by category
        search: Search by name or brand
        current_admin: Current admin user
        
    Returns:
        Paginated list of products
    """
    products_collection = get_products_collection()
    
    # Build query
    query = {}
    if category:
        query["category"] = category
    if search:
        query["$or"] = [
            {"product_name": {"$regex": search, "$options": "i"}},
            {"brand_name": {"$regex": search, "$options": "i"}}
        ]
    
    # Get total count
    total = await products_collection.count_documents(query)
    
    # Get paginated results
    skip = (page - 1) * page_size
    cursor = products_collection.find(query).skip(skip).limit(page_size).sort("created_at", -1)
    products = await cursor.to_list(length=page_size)
    
    # Format response
    product_responses = [
        ProductResponse(
            product_id=p["product_id"],
            product_name=p["product_name"],
            category=p["category"],
            brand_name=p["brand_name"],
            description=p.get("description"),
            images_count=len(p.get("images", [])),
            added_by=p["added_by"],
            created_at=p["created_at"],
            is_active=p.get("is_active", True)
        )
        for p in products
    ]
    
    return ProductListResponse(
        products=product_responses,
        total=total,
        page=page,
        page_size=page_size
    )

@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    current_admin: UserInDB = Depends(get_current_admin)
):
    """Get product details by ID"""
    products_collection = get_products_collection()
    
    product = await products_collection.find_one({"product_id": product_id})
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return ProductResponse(
        product_id=product["product_id"],
        product_name=product["product_name"],
        category=product["category"],
        brand_name=product["brand_name"],
        description=product.get("description"),
        images_count=len(product.get("images", [])),
        added_by=product["added_by"],
        created_at=product["created_at"],
        is_active=product.get("is_active", True)
    )

@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: str,
    current_admin: UserInDB = Depends(get_current_admin)
):
    """Delete product (soft delete - mark as inactive)"""
    products_collection = get_products_collection()
    
    result = await products_collection.update_one(
        {"product_id": product_id},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return None

# ==================== USER MANAGEMENT ====================

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    page: int = 1,
    page_size: int = 50,
    role: Optional[str] = None,
    current_admin: UserInDB = Depends(get_current_admin)
):
    """
    List all users
    
    Args:
        page: Page number
        page_size: Items per page
        role: Filter by role
        current_admin: Current admin user
        
    Returns:
        List of users
    """
    users_collection = get_users_collection()
    
    # Build query
    query = {}
    if role:
        query["role"] = role
    
    # Get paginated results
    skip = (page - 1) * page_size
    cursor = users_collection.find(query).skip(skip).limit(page_size).sort("created_at", -1)
    users = await cursor.to_list(length=page_size)
    
    # Format response
    user_responses = [
        UserResponse(
            email=u["email"],
            full_name=u["full_name"],
            role=u["role"],
            is_active=u.get("is_active", True),
            is_blocked=u.get("is_blocked", False),
            created_at=u.get("created_at", datetime.utcnow()),
            last_login=u.get("last_login")
        )
        for u in users
    ]
    
    return user_responses

@router.patch("/users/{user_email}", response_model=UserResponse)
async def update_user(
    user_email: str,
    update_data: UserUpdate,
    current_admin: UserInDB = Depends(get_current_admin)
):
    """
    Update user (block/unblock, activate/deactivate)
    
    Args:
        user_email: User email
        update_data: Update data
        current_admin: Current admin user
        
    Returns:
        Updated user information
    """
    users_collection = get_users_collection()
    
    # Prepare update
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    update_dict["updated_at"] = datetime.utcnow()
    
    # Update user
    result = await users_collection.find_one_and_update(
        {"email": user_email},
        {"$set": update_dict},
        return_document=True
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        email=result["email"],
        full_name=result["full_name"],
        role=result["role"],
        is_active=result.get("is_active", True),
        is_blocked=result.get("is_blocked", False),
        created_at=result.get("created_at", datetime.utcnow()),
        last_login=result.get("last_login")
    )
