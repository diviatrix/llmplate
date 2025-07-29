"""Integration tests for complete generation flow."""
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.models.user import User
from app.models.template import Template
from app.models.generation import Generation, GenerationStatus


class TestGenerationFlow:
    """Test complete generation flow from start to export."""
    
    async def test_complete_generation_flow(
        self, client: AsyncClient, user_factory, template_factory
    ):
        """Test the complete flow: create template -> start generation -> check status -> get results -> export."""
        # 1. Create a user and login
        user = await user_factory(email="test@example.com")
        login_data = {"username": "test@example.com", "password": "TestPassword123!"}
        
        login_response = await client.post("/api/v1/auth/login", data=login_data)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Create a template
        template_data = {
            "name": "Integration Test Template",
            "description": "Template for integration testing",
            "category": "test",
            "tags": ["test", "integration"],
            "system_prompt": "You are a helpful assistant",
            "user_prompt": "Generate a {{item_type}} about {{topic}}",
            "variables": {
                "item_type": {
                    "type": "string",
                    "description": "Type of item to generate",
                    "default": "story"
                },
                "topic": {
                    "type": "string",
                    "description": "Topic for generation"
                }
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "content": {"type": "string"}
                },
                "required": ["title", "content"]
            },
            "validation_mode": "strict",
            "is_public": True
        }
        
        template_response = await client.post(
            "/api/v1/templates",
            json=template_data,
            headers=headers
        )
        assert template_response.status_code == 201
        template_id = template_response.json()["id"]
        
        # 3. Start generation
        generation_data = {
            "template_id": template_id,
            "provider": "openrouter",
            "model": "anthropic/claude-3.5-sonnet",
            "variables": {
                "item_type": "poem",
                "topic": "technology"
            },
            "count": 2
        }
        
        # Mock the provider to return predictable results
        mock_response = {
            "content": '{"title": "Digital Dreams", "content": "In circuits deep..."}',
            "usage": {
                "prompt_tokens": 50,
                "completion_tokens": 100,
                "total_tokens": 150
            },
            "cost": 0.0015
        }
        
        with patch("app.providers.openrouter.OpenRouterProvider.generate") as mock_generate:
            mock_generate.return_value = mock_response
            
            start_response = await client.post(
                "/api/v1/generate",
                json=generation_data,
                headers=headers
            )
        
        assert start_response.status_code == 202
        job_id = start_response.json()["job_id"]
        assert job_id.startswith("gen_")
        
        # 4. Wait for processing (in real scenario, this would be async)
        await asyncio.sleep(0.1)  # Give mock task time to process
        
        # 5. Check status
        status_response = await client.get(
            f"/api/v1/generate/{job_id}",
            headers=headers
        )
        assert status_response.status_code == 200
        status_data = status_response.json()
        
        # In mock, it should complete quickly
        assert status_data["job_id"] == job_id
        assert status_data["template_id"] == template_id
        
        # 6. Get results (if completed)
        if status_data["status"] == "completed":
            result_response = await client.get(
                f"/api/v1/generate/{job_id}/result",
                headers=headers
            )
            assert result_response.status_code == 200
            result_data = result_response.json()
            assert result_data["results"] is not None
            assert len(result_data["results"]) > 0
            
            # 7. Export in different formats
            for format in ["json", "csv", "markdown", "html"]:
                export_response = await client.get(
                    f"/api/v1/generate/{job_id}/export?format={format}",
                    headers=headers
                )
                assert export_response.status_code == 200
                
                # Check content type
                if format == "json":
                    assert "application/json" in export_response.headers["content-type"]
                elif format == "csv":
                    assert export_response.headers["content-type"] == "text/csv"
                elif format == "markdown":
                    assert export_response.headers["content-type"] == "text/markdown"
                elif format == "html":
                    assert export_response.headers["content-type"] == "text/html"
        
        # 8. Check history
        history_response = await client.get(
            "/api/v1/history",
            headers=headers
        )
        assert history_response.status_code == 200
        history_data = history_response.json()
        assert history_data["total"] >= 1
        assert any(item["job_id"] == job_id for item in history_data["items"])
    
    async def test_batch_generation_flow(
        self, client: AsyncClient, auth_headers: dict, template_factory
    ):
        """Test batch generation with multiple templates."""
        # Create multiple templates
        templates = []
        for i in range(2):
            template = await template_factory(
                name=f"Batch Template {i}",
                is_public=True
            )
            templates.append(template)
        
        # Prepare batch request
        batch_data = {
            "generations": [
                {
                    "template_id": str(templates[0].id),
                    "provider": "openrouter",
                    "model": "anthropic/claude-3.5-sonnet",
                    "variables": {"topic": "AI"},
                    "count": 1
                },
                {
                    "template_id": str(templates[1].id),
                    "provider": "openrouter",
                    "model": "meta-llama/llama-3.2-3b-instruct:free",
                    "variables": {"topic": "Space"},
                    "count": 2
                }
            ]
        }
        
        # Mock provider
        with patch("app.providers.factory.get_provider") as mock_factory:
            mock_provider = AsyncMock()
            mock_provider.generate.return_value = {
                "content": '{"result": "test"}',
                "usage": {"total_tokens": 100}
            }
            mock_factory.return_value = mock_provider
            
            # Start batch generation
            batch_response = await client.post(
                "/api/v1/generate/batch",
                json=batch_data,
                headers=auth_headers
            )
        
        assert batch_response.status_code == 202
        jobs = batch_response.json()["jobs"]
        assert len(jobs) == 2
        
        # Check each job
        for job in jobs:
            assert "job_id" in job
            assert job["status"] == "pending"
    
    async def test_generation_with_validation_error(
        self, client: AsyncClient, auth_headers: dict, template_factory
    ):
        """Test generation fails with validation error."""
        # Create template with strict validation
        template = await template_factory(
            variables={
                "count": {
                    "type": "number",
                    "min": 1,
                    "max": 5
                },
                "topic": {
                    "type": "string",
                    "minLength": 3
                }
            },
            validation_mode="strict"
        )
        
        # Try to generate with invalid variables
        generation_data = {
            "template_id": str(template.id),
            "provider": "openrouter",
            "model": "test-model",
            "variables": {
                "count": 10,  # Exceeds max
                "topic": "AI"  # Too short
            },
            "count": 1
        }
        
        response = await client.post(
            "/api/v1/generate",
            json=generation_data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "Validation failed" in response.json()["detail"]
    
    async def test_generation_cancellation(
        self, client: AsyncClient, auth_headers: dict, template_factory
    ):
        """Test cancelling a generation job."""
        template = await template_factory()
        
        # Start generation
        generation_data = {
            "template_id": str(template.id),
            "provider": "openrouter",
            "model": "test-model",
            "variables": {"topic": "test"},
            "count": 10  # Large count to ensure it takes time
        }
        
        # Mock slow generation
        with patch("app.generation.tasks.GenerationProcessor.process_generation") as mock_process:
            async def slow_process(gen_id):
                await asyncio.sleep(5)  # Simulate slow processing
            mock_process.side_effect = slow_process
            
            start_response = await client.post(
                "/api/v1/generate",
                json=generation_data,
                headers=auth_headers
            )
            
            assert start_response.status_code == 202
            job_id = start_response.json()["job_id"]
            
            # Try to cancel immediately
            cancel_response = await client.delete(
                f"/api/v1/generate/{job_id}",
                headers=auth_headers
            )
            
            # Should succeed if job is still pending/processing
            if cancel_response.status_code == 200:
                assert cancel_response.json()["message"] == "Generation cancelled"
                
                # Check status is cancelled
                status_response = await client.get(
                    f"/api/v1/generate/{job_id}",
                    headers=auth_headers
                )
                assert status_response.json()["status"] == "cancelled"
    
    async def test_generation_with_different_providers(
        self, client: AsyncClient, auth_headers: dict, template_factory
    ):
        """Test generation works with different providers."""
        template = await template_factory()
        
        providers = [
            ("openrouter", "anthropic/claude-3.5-sonnet"),
            ("ollama", "llama3:latest")
        ]
        
        for provider, model in providers:
            generation_data = {
                "template_id": str(template.id),
                "provider": provider,
                "model": model,
                "variables": {"topic": f"test-{provider}"},
                "count": 1
            }
            
            # Mock the provider
            with patch(f"app.providers.{provider}.{provider.title()}Provider.generate") as mock_gen:
                mock_gen.return_value = {
                    "content": f"Generated by {provider}",
                    "usage": {"total_tokens": 50}
                }
                
                response = await client.post(
                    "/api/v1/generate",
                    json=generation_data,
                    headers=auth_headers
                )
                
                assert response.status_code == 202
                assert response.json()["provider"] == provider
                assert response.json()["model"] == model