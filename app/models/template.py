"""
Template model using Beanie ODM for MongoDB.
"""
from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import Field
from beanie import Document, Link
from .user import User


class Template(Document):
    """Template document model."""
    
    # Basic info
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    category: str = Field(..., description="Template category")
    tags: List[str] = Field(default_factory=list, description="Template tags")
    
    # Prompts
    system_prompt: str = Field(..., description="System prompt for LLM")
    user_prompt: str = Field(..., description="User prompt template with variables")
    
    # Variables and schema
    variables: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, 
        description="Template variables schema"
    )
    output_schema: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Expected output JSON schema"
    )
    
    # Provider settings
    provider_settings: Dict[str, Any] = Field(
        default_factory=dict,
        description="Recommended provider settings"
    )
    
    # Validation
    validation_mode: str = Field(
        default="strict", 
        description="Validation mode: strict, custom, none"
    )
    validation_rules: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom validation rules"
    )
    
    # Metadata
    is_public: bool = Field(default=True, description="Is template public")
    created_by: Link[User] = Field(..., description="Template creator")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        collection = "templates"
        indexes = [
            [("category", 1)],
            [("is_public", 1)],
            [("created_by", 1)],
            [("tags", 1)],
        ]
    
    def dict_public(self) -> dict:
        """Return public template data."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "tags": self.tags,
            "system_prompt": self.system_prompt,
            "user_prompt": self.user_prompt,
            "variables": self.variables,
            "output_schema": self.output_schema,
            "provider_settings": self.provider_settings,
            "validation_mode": self.validation_mode,
            "validation_rules": self.validation_rules,
            "is_public": self.is_public,
            "created_by": str(self.created_by.ref.id) if self.created_by else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }