"""
User model for authentication
"""

from typing import List, Optional
from pydantic import BaseModel, EmailStr


class User(BaseModel):
    """User model from JWT token payload"""
    
    id: str
    email: Optional[EmailStr] = None
    roles: List[str] = []
    
    def is_admin(self) -> bool:
        """Check if user has admin role"""
        return "admin" in self.roles or "Admin" in self.roles
    
    def has_role(self, role: str) -> bool:
        """Check if user has a specific role"""
        return role in self.roles or role.lower() in [r.lower() for r in self.roles]
