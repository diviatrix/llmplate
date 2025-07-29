"""
Generation model using Beanie ODM for MongoDB.
"""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional
from pydantic import Field
from beanie import Document, Link
from .user import User
from .template import Template


class GenerationStatus(str, Enum):
    """Generation job status."""
    
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Generation(Document):
    """Generation document model."""
    
    # Job information
    job_id: str = Field(..., description="Unique job identifier")
    user: Link[User] = Field(..., description="User who created the generation")
    template: Link[Template] = Field(..., description="Template used for generation")
    
    # For direct access without loading relations
    user_id: str = Field(..., description="User ID for direct queries")
    template_id: str = Field(..., description="Template ID for direct queries")
    
    # Generation configuration
    provider: str = Field(..., description="LLM provider (openrouter/ollama)")
    model: str = Field(..., description="Model identifier")
    variables: Dict[str, Any] = Field(default_factory=dict, description="Template variables")
    count: int = Field(1, ge=1, le=100, description="Number of items to generate")
    
    # Status tracking
    status: GenerationStatus = Field(
        GenerationStatus.PENDING,
        description="Current job status"
    )
    progress: int = Field(0, ge=0, le=100, description="Progress percentage")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    # Results
    results: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Generated results"
    )
    prompt_rendered: Optional[str] = Field(None, description="Final rendered prompt sent to LLM")
    
    # Cost tracking
    total_tokens: int = Field(0, description="Total tokens used")
    prompt_tokens: int = Field(0, description="Prompt tokens used")
    completion_tokens: int = Field(0, description="Completion tokens used")
    cost: float = Field(0.0, description="Total cost in USD")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = Field(None, description="When processing started")
    completed_at: Optional[datetime] = Field(None, description="When generation completed")
    
    # Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    
    class Settings:
        collection = "generations"
        indexes = [
            [("job_id", 1)],
            [("user", 1)],
            [("template", 1)],
            [("user_id", 1)],
            [("template_id", 1)],
            [("status", 1)],
            [("created_at", -1)],
            [("user_id", 1), ("created_at", -1)],  # For history queries
            [("template_id", 1), ("status", 1)],  # For template usage stats
        ]
    
    def dict_public(self) -> dict:
        """Return public generation data."""
        return {
            "id": str(self.id),
            "job_id": self.job_id,
            "user_id": self.user_id,
            "template_id": self.template_id,
            "provider": self.provider,
            "model": self.model,
            "variables": self.variables,
            "count": self.count,
            "status": self.status.value,
            "progress": self.progress,
            "error_message": self.error_message,
            "results": self.results,
            "total_tokens": self.total_tokens,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "cost": self.cost,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata
        }