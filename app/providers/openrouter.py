"""
OpenRouter provider implementation.
"""
import time
from typing import Dict, List, Any, Optional, AsyncIterator
import httpx
from openai import AsyncOpenAI

from app.config import get_settings
from app.providers.base import LLMProvider, ModelInfo, GenerationRequest, GenerationResponse


class OpenRouterProvider(LLMProvider):
    """OpenRouter provider for accessing multiple LLM models."""
    
    def __init__(self):
        super().__init__()
        self.id = "openrouter"
        self.name = "OpenRouter"
        
        settings = get_settings()
        self.api_key = settings.openrouter_api_key
        self.base_url = settings.openrouter_base_url
        
        # Initialize OpenAI client with OpenRouter base URL
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            default_headers={
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "LLM Template System"
            }
        ) if self.api_key else None
        
        self.available = bool(self.api_key)
        
        # Cached models list
        self._models_cache: Optional[List[ModelInfo]] = None
        self._cache_timestamp: float = 0
        self._cache_ttl = 3600  # 1 hour
    
    async def check_connection(self) -> Dict[str, Any]:
        """Check OpenRouter connection."""
        if not self.client:
            return {
                "available": False,
                "error": "OpenRouter API key not configured"
            }
        
        try:
            start_time = time.time()
            # Try to list models as connection test
            await self._fetch_models()
            response_time = (time.time() - start_time) * 1000
            
            return {
                "available": True,
                "response_time_ms": round(response_time, 2),
                "models_count": len(self._models_cache) if self._models_cache else 0
            }
        except Exception as e:
            return {
                "available": False,
                "error": str(e)
            }
    
    async def _fetch_models(self) -> List[Dict[str, Any]]:
        """Fetch models list from OpenRouter API."""
        # Check cache
        if (self._models_cache and 
            time.time() - self._cache_timestamp < self._cache_ttl):
            return self._models_cache
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            response.raise_for_status()
            data = response.json()
            
            # Update cache
            self._models_cache = data.get("data", [])
            self._cache_timestamp = time.time()
            
            return self._models_cache
    
    async def list_models(self) -> List[ModelInfo]:
        """List all available OpenRouter models."""
        if not self.client:
            return []
        
        try:
            models_data = await self._fetch_models()
            models = []
            
            for model_data in models_data:
                # Extract model info from OpenRouter format
                model_id = model_data.get("id", "")
                
                # Parse pricing (OpenRouter provides in $/token)
                pricing = model_data.get("pricing", {})
                input_price = float(pricing.get("prompt", 0)) * 1_000_000  # Convert to per million
                output_price = float(pricing.get("completion", 0)) * 1_000_000
                
                # Determine capabilities
                context_length = model_data.get("context_length", 4096)
                capabilities = {
                    "max_tokens": min(4096, context_length),  # Conservative default
                    "online": "online" in model_data.get("description", "").lower() or 
                             "internet" in model_data.get("description", "").lower() or
                             "search" in model_data.get("description", "").lower(),
                    "functions": "function" in model_data.get("description", "").lower(),
                    "vision": "vision" in model_data.get("description", "").lower() or
                             "image" in model_data.get("description", "").lower()
                }
                
                # Add online capability for specific models
                if any(x in model_id for x in ["perplexity", "anthropic/claude-3", "gpt-4"]):
                    capabilities["online"] = True
                
                model = ModelInfo(
                    id=model_id,
                    name=model_data.get("name", model_id),
                    provider=self.id,
                    description=model_data.get("description", ""),
                    pricing={"input": input_price, "output": output_price},
                    capabilities=capabilities,
                    context_length=context_length
                )
                models.append(model)
            
            return models
            
        except Exception as e:
            print(f"Error fetching OpenRouter models: {e}")
            return []
    
    async def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """Get information about a specific model."""
        models = await self.list_models()
        return next((m for m in models if m.id == model_id), None)
    
    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate text using OpenRouter."""
        if not self.client:
            raise ValueError("OpenRouter API key not configured")
        
        # Create completion request
        completion = await self.client.chat.completions.create(
            model=request.model,
            messages=request.messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            top_p=request.top_p,
            frequency_penalty=request.frequency_penalty,
            presence_penalty=request.presence_penalty,
            stop=request.stop,
            stream=False,
            **request.extra_params
        )
        
        # Convert to our response format
        return GenerationResponse(
            id=completion.id,
            model=completion.model,
            choices=[
                {
                    "index": choice.index,
                    "message": {
                        "role": choice.message.role,
                        "content": choice.message.content
                    },
                    "finish_reason": choice.finish_reason
                }
                for choice in completion.choices
            ],
            usage={
                "prompt_tokens": completion.usage.prompt_tokens,
                "completion_tokens": completion.usage.completion_tokens,
                "total_tokens": completion.usage.total_tokens
            },
            created=completion.created,
            provider=self.id
        )
    
    async def generate_stream(
        self, request: GenerationRequest
    ) -> AsyncIterator[Dict[str, Any]]:
        """Generate text with streaming."""
        if not self.client:
            raise ValueError("OpenRouter API key not configured")
        
        # Create streaming completion
        stream = await self.client.chat.completions.create(
            model=request.model,
            messages=request.messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            top_p=request.top_p,
            frequency_penalty=request.frequency_penalty,
            presence_penalty=request.presence_penalty,
            stop=request.stop,
            stream=True,
            **request.extra_params
        )
        
        # Stream chunks
        async for chunk in stream:
            yield {
                "id": chunk.id,
                "model": chunk.model,
                "choices": [
                    {
                        "index": choice.index,
                        "delta": {
                            "role": choice.delta.role if choice.delta.role else None,
                            "content": choice.delta.content if choice.delta.content else None
                        },
                        "finish_reason": choice.finish_reason
                    }
                    for choice in chunk.choices
                ],
                "provider": self.id
            }
    
    def estimate_cost(self, model_id: str, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for a generation request."""
        # Get model info (would need to be async in real usage)
        # For now, return a simple estimate
        input_cost_per_million = 1.0  # Default $1 per million tokens
        output_cost_per_million = 2.0  # Default $2 per million tokens
        
        total_cost = (
            (input_tokens / 1_000_000) * input_cost_per_million +
            (output_tokens / 1_000_000) * output_cost_per_million
        )
        
        return round(total_cost, 6)