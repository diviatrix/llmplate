"""Unit tests for generation endpoints."""
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from app.models.generation import GenerationStatus


class TestGenerationEndpoints:
    """Test generation API endpoints."""

    async def test_start_generation_success(
        self, client: AsyncClient, auth_headers: dict, template_factory, generation_factory
    ):
        """Should successfully start a generation job."""
        template = await template_factory()
        generation_data = {
            "template_id": str(template.id),
            "provider": "openrouter",
            "model": "anthropic/claude-3.5-sonnet",
            "variables": {"topic": "AI", "difficulty": "intermediate"},
            "count": 5
        }
        
        with patch("app.api.generation.generation_service") as mock_service:
            mock_job = await generation_factory(
                template_id=template.id,
                status=GenerationStatus.PENDING,
                job_id="job_123"
            )
            mock_service.start_generation.return_value = mock_job
            
            response = await client.post(
                "/api/v1/generate",
                json=generation_data,
                headers=auth_headers
            )
        
        assert response.status_code == 202
        data = response.json()
        assert data["job_id"] == "job_123"
        assert data["status"] == "pending"
        assert data["template_id"] == str(template.id)
        
    async def test_start_generation_invalid_template(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Should fail with invalid template ID."""
        generation_data = {
            "template_id": "invalid_id",
            "provider": "openrouter",
            "model": "anthropic/claude-3.5-sonnet",
            "variables": {},
            "count": 1
        }
        
        response = await client.post(
            "/api/v1/generate",
            json=generation_data,
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "Template not found" in response.json()["detail"]
        
    async def test_start_generation_validation_error(
        self, client: AsyncClient, auth_headers: dict, template_factory
    ):
        """Should fail when variables don't match template requirements."""
        template = await template_factory(
            variables={
                "topic": {"type": "string", "required": True},
                "count": {"type": "number", "min": 1, "max": 10}
            },
            validation_mode="strict"
        )
        
        generation_data = {
            "template_id": str(template.id),
            "provider": "openrouter",
            "model": "anthropic/claude-3.5-sonnet",
            "variables": {"count": 20},  # Missing topic, count out of range
            "count": 1
        }
        
        response = await client.post(
            "/api/v1/generate",
            json=generation_data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "Validation failed" in response.json()["detail"]
        
    async def test_get_generation_status(
        self, client: AsyncClient, auth_headers: dict, generation_factory
    ):
        """Should return generation job status."""
        generation = await generation_factory(
            job_id="job_123",
            status=GenerationStatus.PROCESSING,
            progress=50
        )
        
        response = await client.get(
            f"/api/v1/generate/{generation.job_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "job_123"
        assert data["status"] == "processing"
        assert data["progress"] == 50
        
    async def test_get_generation_status_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Should return 404 for non-existent job."""
        response = await client.get(
            "/api/v1/generate/non_existent_job",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "Generation job not found" in response.json()["detail"]
        
    async def test_get_generation_result_success(
        self, client: AsyncClient, auth_headers: dict, generation_factory
    ):
        """Should return generation results when completed."""
        results = [
            {"question": "What is AI?", "answer": "AI is..."},
            {"question": "How does ML work?", "answer": "ML works by..."}
        ]
        generation = await generation_factory(
            job_id="job_123",
            status=GenerationStatus.COMPLETED,
            results=results,
            completed_at=datetime.utcnow()
        )
        
        response = await client.get(
            f"/api/v1/generate/{generation.job_id}/result",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "job_123"
        assert data["status"] == "completed"
        assert data["results"] == results
        assert data["completed_at"] is not None
        
    async def test_get_generation_result_not_ready(
        self, client: AsyncClient, auth_headers: dict, generation_factory
    ):
        """Should return 400 if generation is not completed."""
        generation = await generation_factory(
            job_id="job_123",
            status=GenerationStatus.PROCESSING
        )
        
        response = await client.get(
            f"/api/v1/generate/{generation.job_id}/result",
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "Generation not completed" in response.json()["detail"]
        
    async def test_cancel_generation(
        self, client: AsyncClient, auth_headers: dict, generation_factory
    ):
        """Should cancel a pending/processing generation."""
        generation = await generation_factory(
            job_id="job_123",
            status=GenerationStatus.PROCESSING
        )
        
        with patch("app.api.generation.generation_service") as mock_service:
            mock_service.cancel_generation.return_value = True
            
            response = await client.delete(
                f"/api/v1/generate/{generation.job_id}",
                headers=auth_headers
            )
        
        assert response.status_code == 200
        assert response.json()["message"] == "Generation cancelled"
        
    async def test_cancel_completed_generation(
        self, client: AsyncClient, auth_headers: dict, generation_factory
    ):
        """Should not cancel already completed generation."""
        generation = await generation_factory(
            job_id="job_123",
            status=GenerationStatus.COMPLETED
        )
        
        response = await client.delete(
            f"/api/v1/generate/{generation.job_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "Cannot cancel completed generation" in response.json()["detail"]
        
    async def test_get_generation_history(
        self, client: AsyncClient, auth_headers: dict, generation_factory, user_factory
    ):
        """Should return user's generation history."""
        user = await user_factory()
        auth_headers = {"Authorization": f"Bearer {user.id}"}  # Mock token
        
        # Create multiple generations
        generations = []
        for i in range(3):
            gen = await generation_factory(
                user_id=user.id,
                status=GenerationStatus.COMPLETED,
                created_at=datetime.utcnow()
            )
            generations.append(gen)
            
        response = await client.get(
            "/api/v1/history",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total"] == 3
        
    async def test_get_generation_history_with_filters(
        self, client: AsyncClient, auth_headers: dict, generation_factory, template_factory
    ):
        """Should filter generation history."""
        template = await template_factory()
        
        # Create generations with different statuses
        await generation_factory(
            status=GenerationStatus.COMPLETED,
            template_id=template.id
        )
        await generation_factory(
            status=GenerationStatus.FAILED
        )
        await generation_factory(
            status=GenerationStatus.PROCESSING
        )
        
        # Filter by status
        response = await client.get(
            "/api/v1/history?status=completed",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert all(item["status"] == "completed" for item in data["items"])
        
        # Filter by template
        response = await client.get(
            f"/api/v1/history?template_id={template.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert all(item["template_id"] == str(template.id) for item in data["items"])
        
    async def test_export_generation_json(
        self, client: AsyncClient, auth_headers: dict, generation_factory
    ):
        """Should export generation results as JSON."""
        results = [{"data": "test"}]
        generation = await generation_factory(
            job_id="job_123",
            status=GenerationStatus.COMPLETED,
            results=results
        )
        
        response = await client.get(
            f"/api/v1/generate/{generation.job_id}/export?format=json",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        assert response.json() == results
        
    async def test_export_generation_csv(
        self, client: AsyncClient, auth_headers: dict, generation_factory
    ):
        """Should export generation results as CSV."""
        results = [
            {"name": "John", "age": 30},
            {"name": "Jane", "age": 25}
        ]
        generation = await generation_factory(
            job_id="job_123",
            status=GenerationStatus.COMPLETED,
            results=results
        )
        
        response = await client.get(
            f"/api/v1/generate/{generation.job_id}/export?format=csv",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv"
        assert "name,age" in response.text
        assert "John,30" in response.text
        
    async def test_batch_generation(
        self, client: AsyncClient, auth_headers: dict, template_factory
    ):
        """Should start batch generation with multiple templates."""
        templates = []
        for i in range(2):
            template = await template_factory()
            templates.append(str(template.id))
            
        batch_data = {
            "generations": [
                {
                    "template_id": templates[0],
                    "provider": "openrouter",
                    "model": "anthropic/claude-3.5-sonnet",
                    "variables": {"topic": "AI"},
                    "count": 3
                },
                {
                    "template_id": templates[1],
                    "provider": "ollama",
                    "model": "llama2",
                    "variables": {"subject": "Science"},
                    "count": 2
                }
            ]
        }
        
        with patch("app.api.generation.generation_service") as mock_service:
            mock_service.start_batch_generation.return_value = [
                {"job_id": "job_1", "status": "pending"},
                {"job_id": "job_2", "status": "pending"}
            ]
            
            response = await client.post(
                "/api/v1/generate/batch",
                json=batch_data,
                headers=auth_headers
            )
        
        assert response.status_code == 202
        data = response.json()
        assert len(data["jobs"]) == 2
        assert all(job["status"] == "pending" for job in data["jobs"])