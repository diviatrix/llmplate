"""
Provider factory for creating LLM provider instances.
"""
from typing import Dict, Optional
from app.providers.base import LLMProvider
from app.providers.openrouter import OpenRouterProvider
from app.providers.ollama import OllamaProvider


class ProviderFactory:
    """Factory for creating and managing LLM providers."""
    
    # Registry of available providers
    _providers: Dict[str, type] = {
        "openrouter": OpenRouterProvider,
        "ollama": OllamaProvider
    }
    
    # Cached instances
    _instances: Dict[str, LLMProvider] = {}
    
    @classmethod
    def get_provider(cls, provider_id: str) -> Optional[LLMProvider]:
        """Get a provider instance by ID."""
        if provider_id not in cls._providers:
            return None
        
        # Return cached instance if exists
        if provider_id in cls._instances:
            return cls._instances[provider_id]
        
        # Create new instance
        provider_class = cls._providers[provider_id]
        instance = provider_class()
        cls._instances[provider_id] = instance
        
        return instance
    
    @classmethod
    def get_all_providers(cls) -> Dict[str, LLMProvider]:
        """Get all available provider instances."""
        providers = {}
        
        for provider_id in cls._providers:
            provider = cls.get_provider(provider_id)
            if provider:
                providers[provider_id] = provider
        
        return providers
    
    @classmethod
    def register_provider(cls, provider_id: str, provider_class: type):
        """Register a new provider type."""
        cls._providers[provider_id] = provider_class
        
        # Clear cached instance if exists
        if provider_id in cls._instances:
            del cls._instances[provider_id]
    
    @classmethod
    def clear_cache(cls):
        """Clear all cached provider instances."""
        cls._instances.clear()