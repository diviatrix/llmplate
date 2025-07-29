"""
Base LLM provider interface.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, AsyncIterator
from pydantic import BaseModel


class ModelInfo(BaseModel):
    """Information about an LLM model."""
    id: str
    name: str
    provider: str
    description: str = ""
    pricing: Dict[str, float] = {"input": 0.0, "output": 0.0}
    capabilities: Dict[str, Any] = {
        "max_tokens": 4096,
        "online": False,
        "functions": False,
        "vision": False
    }
    supported_parameters: List[str] = [
        "temperature", "max_tokens", "top_p", "top_k", 
        "frequency_penalty", "presence_penalty"
    ]
    context_length: int = 4096


class GenerationRequest(BaseModel):
    """Request for text generation."""
    model: str
    messages: List[Dict[str, str]]
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    top_k: Optional[int] = None
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stream: bool = False
    stop: Optional[List[str]] = None
    
    # Additional parameters for specific providers
    extra_params: Dict[str, Any] = {}


class GenerationResponse(BaseModel):
    """Response from text generation."""
    id: str
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int] = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0
    }
    created: int
    provider: str


class LLMProvider(ABC):
    """Base class for LLM providers."""
    
    def __init__(self):
        self.id = "base"
        self.name = "Base Provider"
        self.available = False
    
    @abstractmethod
    async def check_connection(self) -> Dict[str, Any]:
        """Check provider connection and availability."""
        pass
    
    @abstractmethod
    async def list_models(self) -> List[ModelInfo]:
        """List available models from this provider."""
        pass
    
    @abstractmethod
    async def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """Get detailed information about a specific model."""
        pass
    
    @abstractmethod
    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate text completion."""
        pass
    
    @abstractmethod
    async def generate_stream(
        self, request: GenerationRequest
    ) -> AsyncIterator[Dict[str, Any]]:
        """Generate text completion with streaming."""
        pass
    
    def estimate_cost(self, model_id: str, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for a generation request."""
        # Default implementation - can be overridden
        return 0.0