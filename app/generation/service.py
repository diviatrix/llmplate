"""Generation service for managing LLM generations."""
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from beanie import PydanticObjectId

from app.models.generation import Generation, GenerationStatus
from app.models.template import Template
from app.models.user import User
from app.templates.renderer import TemplateRenderer
from app.templates.validator import TemplateValidator
from app.providers.factory import get_provider
from app.generation.tasks import generate_items_task


class GenerationService:
    """Service for managing generations."""
    
    def __init__(self):
        """Initialize generation service."""
        self.renderer = TemplateRenderer()
        self.validator = TemplateValidator()
    
    async def start_generation(
        self,
        user: User,
        template_id: str,
        provider: str,
        model: str,
        variables: Dict[str, Any],
        count: int = 1
    ) -> Generation:
        """Start a new generation job."""
        # Load template
        template = await Template.get(template_id)
        if not template:
            raise ValueError("Template not found")
        
        # Check access
        if not template.is_public and template.created_by.id != user.id:
            raise ValueError("Access denied to private template")
        
        # Validate variables if needed
        if template.validation_mode != "none":
            is_valid, errors, warnings = self.validator.validate_variables(
                variables,
                template.variables,
                template.validation_mode,
                template.validation_rules
            )
            if not is_valid:
                raise ValueError(f"Validation failed: {', '.join(errors)}")
        
        # Create generation record
        generation = Generation(
            job_id=f"gen_{uuid.uuid4().hex[:8]}",
            user=user,
            template=template,
            user_id=str(user.id),
            template_id=str(template.id),
            provider=provider,
            model=model,
            variables=variables,
            count=count,
            status=GenerationStatus.PENDING,
            metadata={
                "template_name": template.name,
                "validation_warnings": warnings if template.validation_mode != "none" else []
            }
        )
        await generation.save()
        
        # Queue async task
        generate_items_task.delay(str(generation.id))
        
        return generation
    
    async def get_generation_status(self, job_id: str, user: User) -> Optional[Generation]:
        """Get generation status by job ID."""
        generation = await Generation.find_one({
            "job_id": job_id,
            "user_id": str(user.id)
        })
        return generation
    
    async def get_generation_result(self, job_id: str, user: User) -> Optional[Generation]:
        """Get generation result if completed."""
        generation = await self.get_generation_status(job_id, user)
        if not generation:
            return None
        
        if generation.status != GenerationStatus.COMPLETED:
            raise ValueError("Generation not completed")
        
        return generation
    
    async def cancel_generation(self, job_id: str, user: User) -> bool:
        """Cancel a generation job."""
        generation = await self.get_generation_status(job_id, user)
        if not generation:
            raise ValueError("Generation job not found")
        
        if generation.status in [GenerationStatus.COMPLETED, GenerationStatus.FAILED]:
            raise ValueError(f"Cannot cancel {generation.status.value} generation")
        
        # Update status
        generation.status = GenerationStatus.CANCELLED
        generation.error_message = "Cancelled by user"
        generation.completed_at = datetime.utcnow()
        await generation.save()
        
        # TODO: Cancel Celery task if running
        
        return True
    
    async def get_user_history(
        self,
        user: User,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        template_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get user's generation history."""
        # Build query
        query = {"user_id": str(user.id)}
        if status:
            query["status"] = status
        if template_id:
            query["template_id"] = template_id
        
        # Get total count
        total = await Generation.find(query).count()
        
        # Get paginated results
        generations = await Generation.find(query).sort("-created_at").skip(skip).limit(limit).to_list()
        
        return {
            "items": [gen.dict_public() for gen in generations],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    
    async def export_generation(
        self,
        job_id: str,
        user: User,
        format: str = "json"
    ) -> Dict[str, Any]:
        """Export generation results in specified format."""
        generation = await self.get_generation_result(job_id, user)
        if not generation:
            raise ValueError("Generation not found")
        
        # Get export handler (will be implemented with export module)
        from app.generation.export import export_results
        
        return export_results(generation.results, format)
    
    async def start_batch_generation(
        self,
        user: User,
        generations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Start multiple generation jobs."""
        jobs = []
        
        for gen_config in generations:
            try:
                generation = await self.start_generation(
                    user=user,
                    template_id=gen_config["template_id"],
                    provider=gen_config["provider"],
                    model=gen_config["model"],
                    variables=gen_config["variables"],
                    count=gen_config.get("count", 1)
                )
                jobs.append({
                    "job_id": generation.job_id,
                    "status": generation.status.value,
                    "template_id": generation.template_id
                })
            except Exception as e:
                jobs.append({
                    "error": str(e),
                    "template_id": gen_config.get("template_id")
                })
        
        return jobs


# Singleton instance
generation_service = GenerationService()