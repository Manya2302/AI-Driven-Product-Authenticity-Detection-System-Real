"""
Analytics API endpoints for dashboard and insights
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from ..models.user import UserInDB
from ..models.analytics import (
    DashboardStats, AnalyticsResponse, TemporalTrend,
    ProductAnalytics, LocationStats, LocationHeatmapResponse
)
from ..database import (
    get_scans_collection, get_scan_results_collection,
    get_products_collection, get_fake_locations_collection,
    get_users_collection
)
from ..core.dependencies import get_current_admin
from ..models.scan import Classification

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    current_admin: UserInDB = Depends(get_current_admin)
):
    """
    Get overall dashboard statistics
    
    Args:
        current_admin: Current admin user
        
    Returns:
        Dashboard statistics
    """
    scans_collection = get_scans_collection()
    results_collection = get_scan_results_collection()
    products_collection = get_products_collection()
    
    # Get all completed scans
    total_scans = await results_collection.count_documents({})
    
    # Count by classification
    fake_count = await results_collection.count_documents({
        "classification": Classification.LIKELY_FAKE
    })
    real_count = await results_collection.count_documents({
        "classification": Classification.LIKELY_REAL
    })
    suspicious_count = await results_collection.count_documents({
        "classification": Classification.SUSPICIOUS
    })
    
    # Calculate percentage
    fake_percentage = (fake_count / total_scans * 100) if total_scans > 0 else 0.0
    
    # Time-based counts
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)
    month_start = now - timedelta(days=30)
    
    scans_today = await scans_collection.count_documents({
        "timestamp": {"$gte": today_start}
    })
    scans_this_week = await scans_collection.count_documents({
        "timestamp": {"$gte": week_start}
    })
    scans_this_month = await scans_collection.count_documents({
        "timestamp": {"$gte": month_start}
    })
    
    # Top fake products
    pipeline = [
        {"$match": {"classification": Classification.LIKELY_FAKE}},
        {"$group": {"_id": "$scan_id", "scan_id": {"$first": "$scan_id"}}},
        {"$limit": 1000}
    ]
    
    fake_results = await results_collection.aggregate(pipeline).to_list(length=1000)
    fake_scan_ids = [r["scan_id"] for r in fake_results]
    
    # Get product stats
    product_fake_counts = defaultdict(int)
    if fake_scan_ids:
        fake_scans = await scans_collection.find({"scan_id": {"$in": fake_scan_ids}}).to_list(length=1000)
        for scan in fake_scans:
            product_fake_counts[scan["product_id"]] += 1
    
    # Get product details and calculate stats
    top_fake_products = []
    for product_id, fake_count in sorted(product_fake_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        product = await products_collection.find_one({"product_id": product_id})
        if product:
            # Count all scans for this product
            all_scans = await scans_collection.count_documents({"product_id": product_id})
            
            # Count by classification
            product_scan_ids = [s["scan_id"] async for s in scans_collection.find({"product_id": product_id})]
            product_fake = await results_collection.count_documents({
                "scan_id": {"$in": product_scan_ids},
                "classification": Classification.LIKELY_FAKE
            })
            product_real = await results_collection.count_documents({
                "scan_id": {"$in": product_scan_ids},
                "classification": Classification.LIKELY_REAL
            })
            product_suspicious = await results_collection.count_documents({
                "scan_id": {"$in": product_scan_ids},
                "classification": Classification.SUSPICIOUS
            })
            
            fake_pct = (product_fake / all_scans * 100) if all_scans > 0 else 0.0
            
            top_fake_products.append(ProductAnalytics(
                product_id=product_id,
                product_name=product["product_name"],
                brand_name=product["brand_name"],
                total_scans=all_scans,
                fake_count=product_fake,
                real_count=product_real,
                suspicious_count=product_suspicious,
                fake_percentage=fake_pct
            ))
    
    # Recent fake detections (last 24 hours)
    recent_fake = await results_collection.count_documents({
        "classification": Classification.LIKELY_FAKE,
        "analysis_timestamp": {"$gte": now - timedelta(hours=24)}
    })
    
    return DashboardStats(
        total_scans=total_scans,
        total_fake=fake_count,
        total_real=real_count,
        total_suspicious=suspicious_count,
        fake_percentage=fake_percentage,
        scans_today=scans_today,
        scans_this_week=scans_this_week,
        scans_this_month=scans_this_month,
        top_fake_products=top_fake_products,
        recent_fake_detections=recent_fake
    )

@router.get("/trends", response_model=List[TemporalTrend])
async def get_temporal_trends(
    days: int = 30,
    current_admin: UserInDB = Depends(get_current_admin)
):
    """
    Get temporal trends of fake product detections
    
    Args:
        days: Number of days to analyze
        current_admin: Current admin user
        
    Returns:
        List of daily trends
    """
    scans_collection = get_scans_collection()
    results_collection = get_scan_results_collection()
    
    trends = []
    now = datetime.utcnow()
    
    for i in range(days):
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        # Get scans for this day
        day_scans = await scans_collection.find({
            "timestamp": {"$gte": day_start, "$lt": day_end},
            "status": "completed"
        }).to_list(length=10000)
        
        scan_ids = [s["scan_id"] for s in day_scans]
        
        if scan_ids:
            fake_count = await results_collection.count_documents({
                "scan_id": {"$in": scan_ids},
                "classification": Classification.LIKELY_FAKE
            })
            real_count = await results_collection.count_documents({
                "scan_id": {"$in": scan_ids},
                "classification": Classification.LIKELY_REAL
            })
            suspicious_count = await results_collection.count_documents({
                "scan_id": {"$in": scan_ids},
                "classification": Classification.SUSPICIOUS
            })
        else:
            fake_count = real_count = suspicious_count = 0
        
        trends.append(TemporalTrend(
            date=day_start.date().isoformat(),
            fake_count=fake_count,
            real_count=real_count,
            suspicious_count=suspicious_count,
            total_scans=len(scan_ids)
        ))
    
    # Reverse to show oldest first
    trends.reverse()
    
    return trends

@router.get("/products", response_model=List[ProductAnalytics])
async def get_product_analytics(
    current_admin: UserInDB = Depends(get_current_admin)
):
    """
    Get analytics for all products
    
    Args:
        current_admin: Current admin user
        
    Returns:
        List of product analytics
    """
    scans_collection = get_scans_collection()
    results_collection = get_scan_results_collection()
    products_collection = get_products_collection()
    
    # Get all products
    products = await products_collection.find({"is_active": True}).to_list(length=1000)
    
    product_analytics = []
    
    for product in products:
        product_id = product["product_id"]
        
        # Get all scans for this product
        product_scans = await scans_collection.find({
            "product_id": product_id,
            "status": "completed"
        }).to_list(length=10000)
        
        scan_ids = [s["scan_id"] for s in product_scans]
        total_scans = len(scan_ids)
        
        if scan_ids:
            fake_count = await results_collection.count_documents({
                "scan_id": {"$in": scan_ids},
                "classification": Classification.LIKELY_FAKE
            })
            real_count = await results_collection.count_documents({
                "scan_id": {"$in": scan_ids},
                "classification": Classification.LIKELY_REAL
            })
            suspicious_count = await results_collection.count_documents({
                "scan_id": {"$in": scan_ids},
                "classification": Classification.SUSPICIOUS
            })
        else:
            fake_count = real_count = suspicious_count = 0
        
        fake_pct = (fake_count / total_scans * 100) if total_scans > 0 else 0.0
        
        product_analytics.append(ProductAnalytics(
            product_id=product_id,
            product_name=product["product_name"],
            brand_name=product["brand_name"],
            total_scans=total_scans,
            fake_count=fake_count,
            real_count=real_count,
            suspicious_count=suspicious_count,
            fake_percentage=fake_pct
        ))
    
    # Sort by fake count
    product_analytics.sort(key=lambda x: x.fake_count, reverse=True)
    
    return product_analytics

@router.get("/locations/heatmap", response_model=LocationHeatmapResponse)
async def get_location_heatmap(
    current_admin: UserInDB = Depends(get_current_admin)
):
    """
    Get location-based heatmap of fake products
    
    Args:
        current_admin: Current admin user
        
    Returns:
        Location heatmap data
    """
    locations_collection = get_fake_locations_collection()
    
    # Get all fake product locations
    locations = await locations_collection.find({}).to_list(length=10000)
    
    # Aggregate by location levels
    country_counts = defaultdict(int)
    state_counts = defaultdict(int)
    city_counts = defaultdict(int)
    district_counts = defaultdict(int)
    
    for loc in locations:
        location = loc.get("location", {})
        country = location.get("country", "Unknown")
        state = location.get("state")
        city = location.get("city")
        district = location.get("district")
        
        country_counts[country] += 1
        if state:
            state_counts[f"{country} > {state}"] += 1
        if city:
            city_counts[f"{country} > {state or 'Unknown'} > {city}"] += 1
        if district:
            district_counts[f"{country} > {state or 'Unknown'} > {city or 'Unknown'} > {district}"] += 1
    
    total_fake = len(locations)
    
    # Format response
    countries = [
        LocationStats(
            location=loc,
            fake_count=count,
            percentage=(count / total_fake * 100) if total_fake > 0 else 0.0
        )
        for loc, count in sorted(country_counts.items(), key=lambda x: x[1], reverse=True)
    ]
    
    states = [
        LocationStats(
            location=loc,
            fake_count=count,
            percentage=(count / total_fake * 100) if total_fake > 0 else 0.0
        )
        for loc, count in sorted(state_counts.items(), key=lambda x: x[1], reverse=True)
    ]
    
    cities = [
        LocationStats(
            location=loc,
            fake_count=count,
            percentage=(count / total_fake * 100) if total_fake > 0 else 0.0
        )
        for loc, count in sorted(city_counts.items(), key=lambda x: x[1], reverse=True)
    ]
    
    districts = [
        LocationStats(
            location=loc,
            fake_count=count,
            percentage=(count / total_fake * 100) if total_fake > 0 else 0.0
        )
        for loc, count in sorted(district_counts.items(), key=lambda x: x[1], reverse=True)
    ]
    
    return LocationHeatmapResponse(
        countries=countries[:20],  # Top 20
        states=states[:50],  # Top 50
        cities=cities[:100],  # Top 100
        districts=districts[:100],  # Top 100
        total_fake_products=total_fake
    )

@router.get("/complete", response_model=AnalyticsResponse)
async def get_complete_analytics(
    days: int = 30,
    current_admin: UserInDB = Depends(get_current_admin)
):
    """
    Get complete analytics data for admin dashboard
    
    Args:
        days: Number of days for trends
        current_admin: Current admin user
        
    Returns:
        Complete analytics response
    """
    # Get all components
    overview = await get_dashboard_stats(current_admin)
    temporal_trends = await get_temporal_trends(days, current_admin)
    product_analytics = await get_product_analytics(current_admin)
    location_distribution = await get_location_heatmap(current_admin)
    
    return AnalyticsResponse(
        overview=overview,
        temporal_trends=temporal_trends,
        product_analytics=product_analytics,
        location_distribution=location_distribution
    )
