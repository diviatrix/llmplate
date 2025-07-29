"""
Ollama provider implementation for local models.
"""
import time
from typing import Dict, List, Any, Optional, AsyncIterator
import httpx
import json

from app.config import get_settings
from app.providers.base import LLMProvider, ModelInfo, GenerationRequest, GenerationResponse


class OllamaProvider(LLMProvider):
    """Ollama provider for local LLM models."""
    
    def __init__(self):
        super().__init__()
        self.id = "ollama"
        self.name = "Ollama (Local)"
        
        settings = get_settings()
        self.base_url = settings.ollama_base_url
        self.available = False
        
        # Check connection on init
        self._check_initial_connection()
    
    def _check_initial_connection(self):
        """Quick sync check for initial availability."""
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=1)
            self.available = response.status_code == 200
        except:
            self.available = False
    
    async def check_connection(self) -> Dict[str, Any]:
        """Check Ollama connection and availability."""
        try:
            start_time = time.time()
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/tags",
                    timeout=5.0
                )
                response.raise_for_status()
                data = response.json()
                
            response_time = (time.time() - start_time) * 1000
            models_count = len(data.get("models", []))
            
            self.available = True
            
            return {
                "available": True,
                "response_time_ms": round(response_time, 2),
                "models_count": models_count,
                "version": data.get("version", "unknown")
            }
            
        except Exception as e:
            self.available = False
            return {
                "available": False,
                "error": f"Cannot connect to Ollama at {self.base_url}: {str(e)}"
            }
    
    async def list_models(self) -> List[ModelInfo]:
        """List available Ollama models."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/tags",
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
            
            models = []
            for model_data in data.get("models", []):
                model_name = model_data.get("name", "")
                model_size = model_data.get("size", 0)
                
                # Parse model family and size
                model_family = model_name.split(":")[0] if ":" in model_name else model_name
                
                # Estimate context length based on model
                context_length = 4096  # Default
                if "llama3" in model_name:
                    context_length = 8192
                elif "mistral" in model_name:
                    context_length = 8192
                elif "qwen" in model_name:
                    context_length = 32768
                elif "deepseek" in model_name:
                    context_length = 16384
                
                # Determine capabilities
                capabilities = {
                    "max_tokens": min(4096, context_length),
                    "online": False,  # Local models don't have internet
                    "functions": "function" in model_name or "instruct" in model_name,
                    "vision": "vision" in model_name or "llava" in model_name
                }
                
                model = ModelInfo(
                    id=model_name,
                    name=f"{model_family} ({self._format_size(model_size)})",
                    provider=self.id,
                    description=f"Local {model_family} model via Ollama",
                    pricing={"input": 0.0, "output": 0.0},  # Free for local
                    capabilities=capabilities,
                    context_length=context_length
                )
                models.append(model)
            
            return models
            
        except Exception as e:
            print(f"Error fetching Ollama models: {e}")
            return []
    
    def _format_size(self, size_bytes: int) -> str:
        """Format size in bytes to human readable."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f}TB"
    
    async def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """Get information about a specific model."""
        models = await self.list_models()
        return next((m for m in models if m.id == model_id), None)
    
    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate text using Ollama."""
        # Convert messages to Ollama format
        prompt = self._messages_to_prompt(request.messages)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": request.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": request.temperature,
                        "top_p": request.top_p,
                        "top_k": request.top_k,
                        "num_predict": request.max_tokens
                    }
                },
                timeout=300.0  # Long timeout for generation
            )
            response.raise_for_status()
            data = response.json()
        
        # Estimate token counts (Ollama doesn't always provide exact counts)
        prompt_tokens = len(prompt.split()) * 1.3  # Rough estimate
        completion_tokens = len(data.get("response", "").split()) * 1.3
        
        return GenerationResponse(
            id=f"ollama-{int(time.time())}",
            model=request.model,
            choices=[{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": data.get("response", "")
                },
                "finish_reason": "stop"
            }],
            usage={
                "prompt_tokens": int(prompt_tokens),
                "completion_tokens": int(completion_tokens),
                "total_tokens": int(prompt_tokens + completion_tokens)
            },
            created=int(time.time()),
            provider=self.id
        )
    
    async def generate_stream(
        self, request: GenerationRequest
    ) -> AsyncIterator[Dict[str, Any]]:
        """Generate text with streaming."""
        prompt = self._messages_to_prompt(request.messages)
        
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/generate",
                json={
                    "model": request.model,
                    "prompt": prompt,
                    "stream": True,
                    "options": {
                        "temperature": request.temperature,
                        "top_p": request.top_p,
                        "top_k": request.top_k,
                        "num_predict": request.max_tokens
                    }
                },
                timeout=300.0
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            yield {
                                "id": f"ollama-{int(time.time())}",
                                "model": request.model,
                                "choices": [{
                                    "index": 0,
                                    "delta": {
                                        "content": data.get("response", "")
                                    },
                                    "finish_reason": "stop" if data.get("done") else None
                                }],
                                "provider": self.id
                            }
                        except json.JSONDecodeError:
                            continue
    
    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert OpenAI-style messages to a single prompt."""
        prompt_parts = []
        
        for message in messages:
            role = message.get("role", "")
            content = message.get("content", "")
            
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        prompt_parts.append("Assistant:")  # Prompt for response
        return "\n\n".join(prompt_parts)