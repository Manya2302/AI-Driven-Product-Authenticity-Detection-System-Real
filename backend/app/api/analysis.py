"""
Product analysis API endpoints for users
"""
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form
from typing import Optional
import uuid
from datetime import datetime
from pathlib import Path
import shutil

from ..models.user import UserInDB
from ..models.scan import (
    Scan, ScanResult, ScanRequest, ScanResponse,
    ScanHistoryItem, ScanHistoryResponse,
    ScanStatus, Classification
)
from ..models.analytics import LocationRequest, FakeProductLocation, Location
from ..database import (
    get_scans_collection, get_scan_results_collection,
    get_products_collection, get_product_features_collection,
    get_fake_locations_collection
)
from ..core.dependencies import get_current_active_user
from ..config import settings
from ...ai_models import decision_engine

router = APIRouter(prefix="/api/analysis", tags=["Analysis"])

@router.post("/scan", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
async def scan_product(
    product_id: str = Form(...),
    image: UploadFile = File(...),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Scan and analyze product for authenticity
    
    Args:
        product_id: Product ID to scan
        image: Product image from user
        current_user: Current authenticated user
        
    Returns:
        Analysis results with authenticity verdict
    """
    scans_collection = get_scans_collection()
    results_collection = get_scan_results_collection()
    products_collection = get_products_collection()
    features_collection = get_product_features_collection()
    
    # Verify product exists
    product = await products_collection.find_one({"product_id": product_id, "is_active": True})
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Get reference features
    reference_profile = await features_collection.find_one({"product_id": product_id})
    if not reference_profile:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Product reference features not available"
        )
    
    # Validate image
    file_ext = Path(image.filename).suffix.lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file extension: {file_ext}"
        )
    
    # Generate scan ID
    scan_id = str(uuid.uuid4())
    
    # Save uploaded image
    scan_dir = settings.UPLOAD_DIR / "scans" / scan_id
    scan_dir.mkdir(parents=True, exist_ok=True)
    image_path = scan_dir / f"uploaded{file_ext}"
    
    with open(image_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
    
    # Create scan record
    scan = Scan(
        scan_id=scan_id,
        user_id=current_user.email,
        product_id=product_id,
        image_path=str(image_path.relative_to(settings.UPLOAD_DIR)),
        status=ScanStatus.PROCESSING,
        timestamp=datetime.utcnow()
    )
    
    await scans_collection.insert_one(scan.model_dump())
    
    try:
        # Run AI analysis
        analysis_results = decision_engine.analyze_product(
            image_path=str(image_path),
            reference_profile=reference_profile,
            product_info={
                'product_name': product['product_name'],
                'brand_name': product['brand_name'],
                'category': product['category']
            },
            user_intent=product['product_name']  # User's selected product provides intent context
        )
        
        # Create result record
        result = ScanResult(
            scan_id=scan_id,
            classification=analysis_results['classification'],
            confidence_score=analysis_results['confidence_score'],
            visual_similarity_score=analysis_results['visual_similarity_score'],
            text_validation_score=analysis_results['text_validation_score'],
            anomaly_score=analysis_results['anomaly_score'],
            pattern_consistency_score=analysis_results['pattern_consistency_score'],
            generic_authenticity_score=analysis_results.get('generic_authenticity_score', 0.5),
            deception_probability=analysis_results.get('deception_probability', 0.0),
            is_likely_lookalike=analysis_results.get('is_likely_lookalike', False),
            explanations=analysis_results['explanations'],
            suspicious_regions=analysis_results.get('suspicious_regions', []),
            extracted_text=', '.join(analysis_results.get('extracted_text', [])),
            text_issues=analysis_results.get('text_issues', []),
            requires_location_sharing=analysis_results.get('requires_location_sharing', False),
            analysis_timestamp=datetime.utcnow(),
            processing_time_seconds=analysis_results['processing_time_seconds']
        )
        
        await results_collection.insert_one(result.model_dump())
        
        # Update scan status
        await scans_collection.update_one(
            {"scan_id": scan_id},
            {"$set": {"status": ScanStatus.COMPLETED, "completed_at": datetime.utcnow()}}
        )
        
        # Prepare response
        return ScanResponse(
            scan_id=scan_id,
            product_name=product['product_name'],
            classification=analysis_results['classification'],
            confidence_score=analysis_results['confidence_score'],
            visual_similarity=analysis_results['visual_similarity_score'],
            text_validation=analysis_results['text_validation_score'],
            anomaly_detection=analysis_results['anomaly_score'],
            pattern_consistency=analysis_results['pattern_consistency_score'],
            generic_authenticity=analysis_results.get('generic_authenticity_score', 0.5),
            deception_probability=analysis_results.get('deception_probability', 0.0),
            is_lookalike=analysis_results.get('is_likely_lookalike', False),
            verdict=analysis_results['verdict'],
            key_findings=analysis_results['explanations'],
            recommendations=analysis_results['recommendations'],
            has_heatmap=False,
            heatmap_url=None,
            requires_location_sharing=analysis_results.get('requires_location_sharing', False),
            analyzed_at=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        # Update scan status to failed
        await scans_collection.update_one(
            {"scan_id": scan_id},
            {"$set": {"status": ScanStatus.FAILED}}
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )

@router.get("/history", response_model=ScanHistoryResponse)
async def get_scan_history(
    page: int = 1,
    page_size: int = 20,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Get user's scan history
    
    Args:
        page: Page number
        page_size: Items per page
        current_user: Current authenticated user
        
    Returns:
        Paginated scan history
    """
    scans_collection = get_scans_collection()
    results_collection = get_scan_results_collection()
    products_collection = get_products_collection()
    
    # Query user's scans
    query = {"user_id": current_user.email, "status": ScanStatus.COMPLETED}
    
    # Get total count
    total = await scans_collection.count_documents(query)
    
    # Get paginated results
    skip = (page - 1) * page_size
    cursor = scans_collection.find(query).skip(skip).limit(page_size).sort("timestamp", -1)
    scans = await cursor.to_list(length=page_size)
    
    # Format response
    history_items = []
    for scan in scans:
        # Get result
        result = await results_collection.find_one({"scan_id": scan["scan_id"]})
        
        # Get product info
        product = await products_collection.find_one({"product_id": scan["product_id"]})
        
        if result and product:
            history_items.append(ScanHistoryItem(
                scan_id=scan["scan_id"],
                product_name=product["product_name"],
                brand_name=product["brand_name"],
                classification=result["classification"],
                confidence_score=result["confidence_score"],
                timestamp=scan["timestamp"].isoformat(),
                image_thumbnail=None
            ))
    
    return ScanHistoryResponse(
        scans=history_items,
        total=total,
        page=page,
        page_size=page_size
    )

@router.get("/results/{scan_id}", response_model=ScanResponse)
async def get_scan_result(
    scan_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Get detailed results for a specific scan
    
    Args:
        scan_id: Scan ID
        current_user: Current authenticated user
        
    Returns:
        Detailed scan results
    """
    scans_collection = get_scans_collection()
    results_collection = get_scan_results_collection()
    products_collection = get_products_collection()
    
    # Get scan
    scan = await scans_collection.find_one({"scan_id": scan_id, "user_id": current_user.email})
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found"
        )
    
    # Get result
    result = await results_collection.find_one({"scan_id": scan_id})
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan results not available"
        )
    
    # Get product
    product = await products_collection.find_one({"product_id": scan["product_id"]})
    
    # Regenerate explanations
    from ...ai_models.gradcam import explainer
    explanation = explainer.generate_textual_explanation(result)
    
    return ScanResponse(
        scan_id=scan_id,
        product_name=product["product_name"] if product else "Unknown",
        classification=result["classification"],
        confidence_score=result["confidence_score"],
        visual_similarity=result["visual_similarity_score"],
        text_validation=result["text_validation_score"],
        anomaly_detection=result["anomaly_score"],
        pattern_consistency=result["pattern_consistency_score"],
        verdict=explanation["verdict"],
        key_findings=explanation["explanations"],
        recommendations=explanation["recommendations"],
        has_heatmap=False,
        heatmap_url=None,
        analyzed_at=result["analysis_timestamp"].isoformat()
    )

@router.post("/location/share", status_code=status.HTTP_201_CREATED)
async def share_fake_location(
    location_data: LocationRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Share location of fake product (user consent required)
    
    Args:
        location_data: Location data
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    scans_collection = get_scans_collection()
    results_collection = get_scan_results_collection()
    products_collection = get_products_collection()
    locations_collection = get_fake_locations_collection()
    
    # Verify user consent
    if not location_data.consent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User consent required to share location"
        )
    
    # Get scan and result
    scan = await scans_collection.find_one({
        "scan_id": location_data.scan_id,
        "user_id": current_user.email
    })
    
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found"
        )
    
    result = await results_collection.find_one({"scan_id": location_data.scan_id})
    
    # Only allow sharing for fake detections
    if result and result["classification"] != Classification.LIKELY_FAKE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Location sharing only allowed for fake product detections"
        )
    
    # Get product info
    product = await products_collection.find_one({"product_id": scan["product_id"]})
    
    # Create location record (anonymized - no user info)
    location_record = FakeProductLocation(
        scan_id=location_data.scan_id,
        product_id=scan["product_id"],
        product_name=product["product_name"] if product else "Unknown",
        brand_name=product["brand_name"] if product else "Unknown",
        location=Location(
            country=location_data.country,
            state=location_data.state,
            city=location_data.city,
            district=location_data.district,
            latitude=location_data.latitude,
            longitude=location_data.longitude
        ),
        user_consent=True,
        timestamp=datetime.utcnow()
    )
    
    await locations_collection.insert_one(location_record.model_dump())
    
    return {"message": "Location shared successfully. Thank you for helping fight counterfeits!"}
