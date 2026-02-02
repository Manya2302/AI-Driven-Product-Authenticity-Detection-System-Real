"""
Database connection and initialization for MongoDB
"""
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
from loguru import logger
from typing import Optional
from .config import settings

class Database:
    """MongoDB database manager"""
    
    client: Optional[AsyncIOMotorClient] = None
    db = None
    
    @classmethod
    async def connect_db(cls):
        """Connect to MongoDB"""
        try:
            cls.client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                serverSelectionTimeoutMS=5000
            )
            # Test connection
            await cls.client.admin.command('ping')
            cls.db = cls.client[settings.DATABASE_NAME]
            
            # Create indexes
            await cls.create_indexes()
            
            # Initialize admin user
            await cls.initialize_admin()
            
            logger.info(f"✅ Connected to MongoDB: {settings.DATABASE_NAME}")
            
        except ConnectionFailure as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            raise
    
    @classmethod
    async def close_db(cls):
        """Close MongoDB connection"""
        if cls.client:
            cls.client.close()
            logger.info("MongoDB connection closed")
    
    @classmethod
    async def create_indexes(cls):
        """Create database indexes for performance"""
        
        # Users collection indexes
        await cls.db.users.create_index("email", unique=True)
        await cls.db.users.create_index("role")
        
        # Products collection indexes
        await cls.db.products.create_index("product_id", unique=True)
        await cls.db.products.create_index("category")
        await cls.db.products.create_index("brand_name")
        
        # Product features collection
        await cls.db.product_features.create_index("product_id", unique=True)
        
        # Scans collection indexes
        await cls.db.scans.create_index("user_id")
        await cls.db.scans.create_index("product_id")
        await cls.db.scans.create_index("timestamp")
        await cls.db.scans.create_index([("user_id", 1), ("timestamp", -1)])
        
        # Scan results collection
        await cls.db.scan_results.create_index("scan_id", unique=True)
        await cls.db.scan_results.create_index("classification")
        
        # Fake locations collection
        await cls.db.fake_locations.create_index("product_id")
        await cls.db.fake_locations.create_index([
            ("location.country", 1),
            ("location.state", 1),
            ("location.city", 1)
        ])
        await cls.db.fake_locations.create_index("timestamp")
        
        # Analytics collection
        await cls.db.analytics.create_index("date")
        await cls.db.analytics.create_index("metric_type")
        
        logger.info("✅ Database indexes created")
    
    @classmethod
    async def initialize_admin(cls):
        """Initialize default admin user if not exists"""
        from .core.security import get_password_hash
        
        admin_exists = await cls.db.users.find_one({
            "email": settings.DEFAULT_ADMIN_EMAIL
        })
        
        if not admin_exists:
            admin_user = {
                "email": settings.DEFAULT_ADMIN_EMAIL,
                "hashed_password": get_password_hash(settings.DEFAULT_ADMIN_PASSWORD),
                "full_name": "System Administrator",
                "role": "admin",
                "is_active": True,
                "is_blocked": False,
                "created_at": None,  # Will be set by model
            }
            await cls.db.users.insert_one(admin_user)
            logger.info(f"✅ Default admin created: {settings.DEFAULT_ADMIN_EMAIL}")

# Database collections
def get_database():
    """Get database instance"""
    return Database.db

# Collection getters
def get_users_collection():
    return Database.db.users

def get_products_collection():
    return Database.db.products

def get_product_features_collection():
    return Database.db.product_features

def get_scans_collection():
    return Database.db.scans

def get_scan_results_collection():
    return Database.db.scan_results

def get_fake_locations_collection():
    return Database.db.fake_locations

def get_analytics_collection():
    return Database.db.analytics
