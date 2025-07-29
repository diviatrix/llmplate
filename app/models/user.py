"""
User model using Beanie ODM for MongoDB.
"""
from datetime import datetime
from typing import Optional
from pydantic import Field, EmailStr
from beanie import Document


class User(Document):
    """User document model."""
    
    email: EmailStr = Field(..., description="User email address", unique=True)
    full_name: str = Field(..., description="User's full name")
    hashed_password: str = Field(..., description="Hashed password")
    is_active: bool = Field(default=True, description="Is user active")
    is_superuser: bool = Field(default=False, description="Is user a superuser")
    
    # OAuth fields
    oauth_provider: Optional[str] = Field(default=None, description="OAuth provider (google, github)")
    oauth_provider_id: Optional[str] = Field(default=None, description="OAuth provider user ID")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        collection = "users"
        indexes = [
            [("email", 1)],  # Unique index on email
            [("oauth_provider", 1), ("oauth_provider_id", 1)],  # OAuth lookup
        ]
    
    def dict_public(self) -> dict:
        """Return public user data (without sensitive fields)."""
        return {
            "id": str(self.id),
            "email": self.email,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "oauth_provider": self.oauth_provider
        }