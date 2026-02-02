"""
Authentication API endpoints
"""
from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime, timedelta
from ..models.user import (
    User, UserCreate, UserInDB, UserResponse,
    LoginRequest, LoginResponse
)
from ..database import get_users_collection
from ..core.security import (
    verify_password, get_password_hash,
    create_access_token, validate_password_strength
)
from ..config import settings
from ..core.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/signup", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate):
    """
    Register a new user (USER role only - admins are created manually)
    
    Args:
        user_data: User registration data
        
    Returns:
        LoginResponse with access token and user info
    """
    users_collection = get_users_collection()
    
    # Check if user already exists
    existing_user = await users_collection.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate password strength
    is_valid, message = validate_password_strength(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    # Ensure role is USER (prevent admin self-registration)
    if user_data.role != "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot self-register as admin"
        )
    
    # Create user
    user_dict = {
        "email": user_data.email,
        "hashed_password": get_password_hash(user_data.password),
        "full_name": user_data.full_name,
        "role": "user",
        "is_active": True,
        "is_blocked": False,
        "created_at": datetime.utcnow(),
        "last_login": None
    }
    
    result = await users_collection.insert_one(user_dict)
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user_data.email, "role": "user"}
    )
    
    # Prepare response
    user_response = UserResponse(
        email=user_data.email,
        full_name=user_data.full_name,
        role="user",
        is_active=True,
        is_blocked=False,
        created_at=user_dict["created_at"],
        last_login=None
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )

@router.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest):
    """
    Login with email and password
    
    Args:
        credentials: Login credentials
        
    Returns:
        LoginResponse with access token and user info
    """
    users_collection = get_users_collection()
    
    # Find user
    user_data = await users_collection.find_one({"email": credentials.email})
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Verify password
    if not verify_password(credentials.password, user_data["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Check if user is blocked
    if user_data.get("is_blocked", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is blocked. Contact administrator."
        )
    
    # Check if user is active
    if not user_data.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )
    
    # Update last login
    await users_collection.update_one(
        {"email": credentials.email},
        {"$set": {"last_login": datetime.utcnow()}}
    )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": credentials.email, "role": user_data["role"]}
    )
    
    # Prepare response
    user_response = UserResponse(
        email=user_data["email"],
        full_name=user_data["full_name"],
        role=user_data["role"],
        is_active=user_data.get("is_active", True),
        is_blocked=user_data.get("is_blocked", False),
        created_at=user_data.get("created_at", datetime.utcnow()),
        last_login=datetime.utcnow()
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )

@router.post("/logout")
async def logout():
    """
    Logout (client-side token removal)
    
    Returns:
        Success message
    """
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get current user information
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User information
    """
    return UserResponse(
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active,
        is_blocked=current_user.is_blocked,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )
