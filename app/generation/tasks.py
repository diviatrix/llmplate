"""Generation processing logic."""
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

from beanie import PydanticObjectId

from app.models.generation import Generation, GenerationStatus
from app.models.template import Template
from app.templates.renderer import TemplateRenderer
from app.providers.factory import get_provider
from app.providers.base import GenerationError


logger = logging.getLogger(__name__)


class GenerationProcessor:
    """Handles the actual generation processing."""
    
    def __init__(self):
        """Initialize processor."""
        self.renderer = TemplateRenderer()
    
    async def process_generation(self, generation_id: str) -> None:
        """Process a generation job."""
        try:
            # Load generation with relations
            generation = await Generation.get(generation_id)
            if not generation:
                logger.error(f"Generation {generation_id} not found")
                return
            
            # Update status to processing
            generation.status = GenerationStatus.PROCESSING
            generation.started_at = datetime.utcnow()
            generation.progress = 10
            await generation.save()
            
            # Load template
            await generation.fetch_link(Generation.template)
            template = generation.template
            
            # Get provider
            try:
                provider = get_provider(generation.provider)
            except ValueError as e:
                await self._fail_generation(generation, str(e))
                return
            
            # Generate items
            results = []
            total_tokens = 0
            total_cost = 0.0
            
            for i in range(generation.count):
                try:
                    # Update progress
                    progress = 10 + int((i / generation.count) * 80)
                    generation.progress = progress
                    await generation.save()
                    
                    # Prepare variables with index
                    variables = generation.variables.copy()
                    variables['index'] = i + 1
                    variables['date'] = datetime.utcnow().isoformat()
                    
                    # Render prompts
                    system_prompt = self.renderer.render(
                        template.system_prompt,
                        variables
                    )
                    user_prompt = self.renderer.render(
                        template.user_prompt,
                        variables
                    )
                    
                    # Store rendered prompt for first item
                    if i == 0:
                        generation.prompt_rendered = f"System: {system_prompt}\n\nUser: {user_prompt}"
                    
                    # Get provider settings
                    settings = template.provider_settings or {}
                    temperature = settings.get('temperature', 0.7)
                    max_tokens = settings.get('max_tokens', 1000)
                    
                    # Generate with provider
                    response = await provider.generate(
                        model=generation.model,
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        response_format="json" if template.output_schema else "text"
                    )
                    
                    # Parse response
                    if template.output_schema:
                        try:
                            result = json.loads(response['content'])
                        except json.JSONDecodeError:
                            result = {"content": response['content'], "raw": True}
                    else:
                        result = {"content": response['content']}
                    
                    results.append(result)
                    
                    # Track usage
                    if 'usage' in response:
                        usage = response['usage']
                        total_tokens += usage.get('total_tokens', 0)
                        generation.prompt_tokens += usage.get('prompt_tokens', 0)
                        generation.completion_tokens += usage.get('completion_tokens', 0)
                        
                        # Calculate cost
                        if 'cost' in response:
                            total_cost += response['cost']
                    
                except Exception as e:
                    logger.error(f"Error generating item {i+1}: {e}")
                    results.append({
                        "error": str(e),
                        "index": i + 1
                    })
            
            # Update generation with results
            generation.status = GenerationStatus.COMPLETED
            generation.results = results
            generation.total_tokens = total_tokens
            generation.cost = total_cost
            generation.progress = 100
            generation.completed_at = datetime.utcnow()
            await generation.save()
            
            logger.info(f"Generation {generation_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Generation {generation_id} failed: {e}")
            if 'generation' in locals():
                await self._fail_generation(generation, str(e))
    
    async def _fail_generation(self, generation: Generation, error: str) -> None:
        """Mark generation as failed."""
        generation.status = GenerationStatus.FAILED
        generation.error_message = error
        generation.completed_at = datetime.utcnow()
        generation.progress = 0
        await generation.save()


# Create processor instance
processor = GenerationProcessor()


# Mock Celery task for now
class MockTask:
    """Mock task for testing without Celery."""
    
    def delay(self, generation_id: str):
        """Mock delay method - runs synchronously for testing."""
        # Run in background without blocking
        asyncio.create_task(processor.process_generation(generation_id))


# Export task
generate_items_task = MockTask()


# Direct processing function for testing
async def process_generation(generation_id: str):
    """Process a generation job directly."""
    await processor.process_generation(generation_id)