"""
Unit tests for LLM provider endpoints.
Following TDD - writing tests first.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.unit
class TestProvidersEndpoints:
    """Test provider listing and information endpoints."""
    
    async def test_list_providers(self, client: AsyncClient):
        """Should return list of available providers."""
        response = await client.get("/providers")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) >= 2  # At least OpenRouter and Ollama
        
        # Check provider structure
        for provider in data:
            assert "id" in provider
            assert "name" in provider
            assert "available" in provider
            assert isinstance(provider["available"], bool)
        
        # Check specific providers exist
        provider_ids = [p["id"] for p in data]
        assert "openrouter" in provider_ids
        assert "ollama" in provider_ids
    
    async def test_list_models_all(self, client: AsyncClient):
        """Should return all available models from all providers."""
        response = await client.get("/providers/models")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Check model structure
        for model in data:
            assert "id" in model
            assert "name" in model
            assert "provider" in model
            assert "pricing" in model
            assert "capabilities" in model
            
            # Check pricing structure
            pricing = model["pricing"]
            assert "input" in pricing
            assert "output" in pricing
            assert isinstance(pricing["input"], (int, float))
            assert isinstance(pricing["output"], (int, float))
            
            # Check capabilities
            capabilities = model["capabilities"]
            assert "max_tokens" in capabilities
            assert isinstance(capabilities["online"], bool)
    
    async def test_list_models_with_filters(self, client: AsyncClient):
        """Should filter models based on query parameters."""
        # Test free models filter
        response = await client.get("/providers/models?free=true")
        assert response.status_code == 200
        free_models = response.json()
        
        for model in free_models:
            assert model["pricing"]["input"] == 0
            assert model["pricing"]["output"] == 0
        
        # Test paid models filter
        response = await client.get("/providers/models?free=false")
        assert response.status_code == 200
        paid_models = response.json()
        
        for model in paid_models:
            assert model["pricing"]["input"] > 0 or model["pricing"]["output"] > 0
        
        # Test online capability filter
        response = await client.get("/providers/models?online=true")
        assert response.status_code == 200
        online_models = response.json()
        
        for model in online_models:
            assert model["capabilities"]["online"] is True
        
        # Test provider filter
        response = await client.get("/providers/models?provider=openrouter")
        assert response.status_code == 200
        openrouter_models = response.json()
        
        for model in openrouter_models:
            assert model["provider"] == "openrouter"
    
    async def test_get_model_details(self, client: AsyncClient):
        """Should return detailed information about a specific model."""
        # Test OpenRouter model
        response = await client.get("/providers/models/anthropic/claude-3.5-sonnet")
        
        assert response.status_code == 200
        model = response.json()
        
        assert model["id"] == "anthropic/claude-3.5-sonnet"
        assert model["provider"] == "openrouter"
        assert "description" in model
        assert "context_length" in model["capabilities"]
        assert "pricing" in model
        assert "supported_parameters" in model
    
    async def test_get_model_not_found(self, client: AsyncClient):
        """Should return 404 for non-existent model."""
        response = await client.get("/providers/models/non-existent/model")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    async def test_provider_connection_test(self, client: AsyncClient, auth_headers):
        """Should test provider connection."""
        # Test OpenRouter connection
        response = await client.post(
            "/providers/test",
            json={"provider": "openrouter"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "message" in data
        assert "response_time_ms" in data
    
    async def test_provider_connection_test_unauthorized(self, client: AsyncClient):
        """Should require authentication for provider testing."""
        response = await client.post(
            "/providers/test",
            json={"provider": "openrouter"}
        )
        
        assert response.status_code == 401


@pytest.mark.unit
class TestOpenRouterProvider:
    """Test OpenRouter provider implementation."""
    
    async def test_openrouter_models_metadata(self, client: AsyncClient):
        """Should return comprehensive OpenRouter models metadata."""
        response = await client.get("/providers/models?provider=openrouter")
        
        assert response.status_code == 200
        models = response.json()
        
        # Check for expected popular models
        model_ids = [m["id"] for m in models]
        
        # Claude models
        assert any("claude" in id for id in model_ids)
        
        # GPT models
        assert any("gpt" in id for id in model_ids)
        
        # Open source models
        assert any("llama" in id for id in model_ids)
        
        # Check metadata completeness
        for model in models:
            if "claude" in model["id"]:
                assert model["capabilities"]["max_tokens"] >= 4096
                assert "anthropic" in model["id"].lower()
            
            if "gpt-4" in model["id"]:
                assert model["capabilities"]["max_tokens"] >= 4096
                assert "openai" in model["id"].lower()
    
    async def test_openrouter_pricing_info(self, client: AsyncClient):
        """Should include accurate pricing information."""
        response = await client.get("/providers/models?provider=openrouter")
        models = response.json()
        
        # Find a known model with pricing
        claude_model = next((m for m in models if "claude-3.5-sonnet" in m["id"]), None)
        assert claude_model is not None
        
        # Check pricing is reasonable (in dollars per million tokens)
        assert 0 < claude_model["pricing"]["input"] < 100
        assert 0 < claude_model["pricing"]["output"] < 100
        assert claude_model["pricing"]["output"] > claude_model["pricing"]["input"]


@pytest.mark.unit
class TestOllamaProvider:
    """Test Ollama provider implementation."""
    
    async def test_ollama_models_list(self, client: AsyncClient):
        """Should return list of locally available Ollama models."""
        response = await client.get("/providers/models?provider=ollama")
        
        assert response.status_code == 200
        models = response.json()
        
        # Ollama models should be free
        for model in models:
            assert model["provider"] == "ollama"
            assert model["pricing"]["input"] == 0
            assert model["pricing"]["output"] == 0
            assert model["capabilities"]["online"] is False  # Local models
    
    async def test_ollama_connection_status(self, client: AsyncClient):
        """Should check Ollama availability."""
        response = await client.get("/providers")
        providers = response.json()
        
        ollama_provider = next((p for p in providers if p["id"] == "ollama"), None)
        assert ollama_provider is not None
        
        # Should have connection status
        assert "available" in ollama_provider
        assert isinstance(ollama_provider["available"], bool)
        
        if ollama_provider["available"]:
            assert "models_count" in ollama_provider
            assert isinstance(ollama_provider["models_count"], int)