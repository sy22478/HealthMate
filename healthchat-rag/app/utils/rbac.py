"""
Role-Based Access Control (RBAC) System
Provides role and permission management for HealthMate application
"""
from enum import Enum
from functools import wraps
from typing import List, Optional, Callable, Any
from fastapi import HTTPException, status, Depends
from app.models.user import User
from app.utils.auth_middleware import get_current_user
import logging

logger = logging.getLogger(__name__)

class UserRole(str, Enum):
    """User roles enumeration"""
    PATIENT = "patient"
    DOCTOR = "doctor"
    ADMIN = "admin"
    RESEARCHER = "researcher"

class Permission(str, Enum):
    """Permission enumeration"""
    # User management
    READ_OWN_PROFILE = "read_own_profile"
    UPDATE_OWN_PROFILE = "update_own_profile"
    DELETE_OWN_ACCOUNT = "delete_own_account"
    
    # Health data
    READ_OWN_HEALTH_DATA = "read_own_health_data"
    UPDATE_OWN_HEALTH_DATA = "update_own_health_data"
    DELETE_OWN_HEALTH_DATA = "delete_own_health_data"
    
    # Chat and conversations
    SEND_MESSAGE = "send_message"
    READ_OWN_CONVERSATIONS = "read_own_conversations"
    DELETE_OWN_CONVERSATIONS = "delete_own_conversations"
    
    # Doctor permissions
    READ_PATIENT_DATA = "read_patient_data"
    UPDATE_PATIENT_DATA = "update_patient_data"
    CREATE_TREATMENT_PLAN = "create_treatment_plan"
    VIEW_ALL_CONVERSATIONS = "view_all_conversations"
    
    # Admin permissions
    MANAGE_USERS = "manage_users"
    MANAGE_SYSTEM = "manage_system"
    VIEW_ANALYTICS = "view_analytics"
    MANAGE_ROLES = "manage_roles"
    
    # Researcher permissions
    ACCESS_ANONYMIZED_DATA = "access_anonymized_data"
    CONDUCT_RESEARCH = "conduct_research"

class RolePermissions:
    """Role-based permission mapping"""
    
    ROLE_PERMISSIONS = {
        UserRole.PATIENT: [
            Permission.READ_OWN_PROFILE,
            Permission.UPDATE_OWN_PROFILE,
            Permission.DELETE_OWN_ACCOUNT,
            Permission.READ_OWN_HEALTH_DATA,
            Permission.UPDATE_OWN_HEALTH_DATA,
            Permission.DELETE_OWN_HEALTH_DATA,
            Permission.SEND_MESSAGE,
            Permission.READ_OWN_CONVERSATIONS,
            Permission.DELETE_OWN_CONVERSATIONS,
        ],
        UserRole.DOCTOR: [
            Permission.READ_OWN_PROFILE,
            Permission.UPDATE_OWN_PROFILE,
            Permission.READ_OWN_HEALTH_DATA,
            Permission.UPDATE_OWN_HEALTH_DATA,
            Permission.SEND_MESSAGE,
            Permission.READ_OWN_CONVERSATIONS,
            Permission.READ_PATIENT_DATA,
            Permission.UPDATE_PATIENT_DATA,
            Permission.CREATE_TREATMENT_PLAN,
            Permission.VIEW_ALL_CONVERSATIONS,
        ],
        UserRole.ADMIN: [
            Permission.READ_OWN_PROFILE,
            Permission.UPDATE_OWN_PROFILE,
            Permission.READ_OWN_HEALTH_DATA,
            Permission.UPDATE_OWN_HEALTH_DATA,
            Permission.SEND_MESSAGE,
            Permission.READ_OWN_CONVERSATIONS,
            Permission.MANAGE_USERS,
            Permission.MANAGE_SYSTEM,
            Permission.VIEW_ANALYTICS,
            Permission.MANAGE_ROLES,
            Permission.VIEW_ALL_CONVERSATIONS,
        ],
        UserRole.RESEARCHER: [
            Permission.READ_OWN_PROFILE,
            Permission.UPDATE_OWN_PROFILE,
            Permission.ACCESS_ANONYMIZED_DATA,
            Permission.CONDUCT_RESEARCH,
        ]
    }
    
    @classmethod
    def get_permissions_for_role(cls, role: UserRole) -> List[Permission]:
        """Get permissions for a specific role"""
        return cls.ROLE_PERMISSIONS.get(role, [])
    
    @classmethod
    def has_permission(cls, role: UserRole, permission: Permission) -> bool:
        """Check if a role has a specific permission"""
        return permission in cls.get_permissions_for_role(role)
    
    @classmethod
    def get_roles_with_permission(cls, permission: Permission) -> List[UserRole]:
        """Get all roles that have a specific permission"""
        roles = []
        for role, permissions in cls.ROLE_PERMISSIONS.items():
            if permission in permissions:
                roles.append(role)
        return roles

class RBACMiddleware:
    """RBAC middleware for permission checking"""
    
    @staticmethod
    def require_permission(permission: Permission):
        """
        Decorator to require a specific permission
        
        Args:
            permission: Required permission
            
        Returns:
            Decorated function
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Get current user from kwargs or dependencies
                current_user = kwargs.get('current_user')
                if not current_user:
                    # Try to get from dependencies
                    for arg in args:
                        if isinstance(arg, User):
                            current_user = arg
                            break
                
                if not current_user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )
                
                # Check if user has the required permission
                if not RBACMiddleware.has_permission(current_user, permission):
                    logger.warning(
                        f"User {current_user.email} attempted to access {permission} without authorization"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Insufficient permissions. Required: {permission}"
                    )
                
                return await func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    @staticmethod
    def require_role(role: UserRole):
        """
        Decorator to require a specific role
        
        Args:
            role: Required role
            
        Returns:
            Decorated function
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Get current user from kwargs or dependencies
                current_user = kwargs.get('current_user')
                if not current_user:
                    # Try to get from dependencies
                    for arg in args:
                        if isinstance(arg, User):
                            current_user = arg
                            break
                
                if not current_user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )
                
                # Check if user has the required role
                if current_user.role != role:
                    logger.warning(
                        f"User {current_user.email} attempted to access role-restricted endpoint without proper role"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Insufficient role. Required: {role}"
                    )
                
                return await func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    @staticmethod
    def has_permission(user: User, permission: Permission) -> bool:
        """
        Check if a user has a specific permission
        
        Args:
            user: User object
            permission: Permission to check
            
        Returns:
            True if user has permission, False otherwise
        """
        if not user.role:
            return False
        
        try:
            user_role = UserRole(user.role)
            return RolePermissions.has_permission(user_role, permission)
        except ValueError:
            logger.error(f"Invalid role '{user.role}' for user {user.email}")
            return False
    
    @staticmethod
    def get_user_permissions(user: User) -> List[Permission]:
        """
        Get all permissions for a user
        
        Args:
            user: User object
            
        Returns:
            List of user permissions
        """
        if not user.role:
            return []
        
        try:
            user_role = UserRole(user.role)
            return RolePermissions.get_permissions_for_role(user_role)
        except ValueError:
            logger.error(f"Invalid role '{user.role}' for user {user.email}")
            return []

# Convenience functions for dependency injection
def require_permission(permission: Permission):
    """FastAPI dependency for requiring a specific permission"""
    def dependency(current_user: User = Depends(get_current_user)):
        if not RBACMiddleware.has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {permission}"
            )
        return current_user
    return dependency

def require_role(roles: List[UserRole]):
    """FastAPI dependency for requiring specific roles"""
    async def dependency(current_user: User = Depends(get_current_user)):
        if current_user.role not in [role.value for role in roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient role. Required: {[role.value for role in roles]}"
            )
        return current_user
    return dependency 