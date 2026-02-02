"""
Dependencies for authentication and authorization
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from ..database import get_users_collection
from ..models.user import UserInDB
from .security import decode_access_token

# Security scheme
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserInDB:
    """
    Get current authenticated user from JWT token
    
    Args:
        credentials: HTTP Bearer token
        
    Returns:
        UserInDB: Current user object
        
    Raises:
        HTTPException: If user not found or blocked
    """
    token = credentials.credentials
    
    # Decode token
    payload = decode_access_token(token)
    email: str = payload.get("sub")
    
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    # Get user from database
    users_collection = get_users_collection()
    user_data = await users_collection.find_one({"email": email})
    
    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    user = UserInDB(**user_data)
    
    # Check if user is blocked
    if user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is blocked"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return user

async def get_current_admin(
    current_user: UserInDB = Depends(get_current_user)
) -> UserInDB:
    """
    Verify that current user has admin role
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        UserInDB: Admin user object
        
    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return current_user

async def get_current_active_user(
    current_user: UserInDB = Depends(get_current_user)
) -> UserInDB:
    """
    Get current active user (admin or regular user)
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        UserInDB: Active user object
    """
    return current_user

class RoleChecker:
    """Role-based access control checker"""
    
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles
    
    async def __call__(
        self,
        current_user: UserInDB = Depends(get_current_user)
    ) -> UserInDB:
        """
        Check if user has required role
        
        Args:
            current_user: Current authenticated user
            
        Returns:
            UserInDB: User with required role
            
        Raises:
            HTTPException: If user doesn't have required role
        """
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(self.allowed_roles)}"
            )
        
        return current_user
