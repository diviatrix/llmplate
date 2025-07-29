"""
Unit tests for health check endpoint.
Following TDD - writing tests first.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.unit
class TestHealthCheck:
    """Test health check endpoint."""
    
    async def test_health_check_returns_200(self, client: AsyncClient):
        """Health check endpoint should return 200 OK."""
        response = await client.get("/health")
        assert response.status_code == 200
    
    async def test_health_check_returns_correct_data(self, client: AsyncClient):
        """Health check should return app status and version."""
        response = await client.get("/health")
        data = response.json()
        
        assert "status" in data
        assert data["status"] == "healthy"
        assert "version" in data
        assert "environment" in data
        assert "timestamp" in data
    
    async def test_health_check_includes_database_status(self, client: AsyncClient):
        """Health check should include database connection status."""
        response = await client.get("/health")
        data = response.json()
        
        assert "database" in data
        assert data["database"]["connected"] is True
        assert "response_time_ms" in data["database"]
    
    async def test_health_check_handles_database_error(self, client: AsyncClient, mocker):
        """Health check should handle database connection errors gracefully."""
        # Mock database ping to raise an exception
        mocker.patch(
            "app.database.check_database_health",
            side_effect=Exception("Connection failed")
        )
        
        response = await client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "degraded"
        assert data["database"]["connected"] is False
        assert "error" in data["database"]