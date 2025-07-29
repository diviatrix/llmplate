"""
Unit tests for authentication endpoints.
Following TDD - writing tests first.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.unit
class TestUserRegistration:
    """Test user registration endpoint."""
    
    async def test_register_new_user_success(self, client: AsyncClient):
        """Should successfully register a new user."""
        user_data = {
            "email": "test@example.com",
            "password": "SecurePassword123!",
            "full_name": "Test User"
        }
        
        response = await client.post("/auth/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["full_name"] == user_data["full_name"]
        assert "id" in data
        assert "password" not in data  # Password should not be returned
        assert "created_at" in data
    
    async def test_register_duplicate_email_fails(self, client: AsyncClient):
        """Should fail when registering with existing email."""
        user_data = {
            "email": "existing@example.com",
            "password": "SecurePassword123!",
            "full_name": "Test User"
        }
        
        # First registration should succeed
        await client.post("/auth/register", json=user_data)
        
        # Second registration with same email should fail
        response = await client.post("/auth/register", json=user_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "already exists" in data["detail"].lower()
    
    async def test_register_invalid_email_fails(self, client: AsyncClient):
        """Should fail with invalid email format."""
        user_data = {
            "email": "not-an-email",
            "password": "SecurePassword123!",
            "full_name": "Test User"
        }
        
        response = await client.post("/auth/register", json=user_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert any("email" in error["loc"] for error in data["detail"])
    
    async def test_register_weak_password_fails(self, client: AsyncClient):
        """Should fail with weak password."""
        user_data = {
            "email": "test@example.com",
            "password": "weak",
            "full_name": "Test User"
        }
        
        response = await client.post("/auth/register", json=user_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert any("password" in str(error["loc"]) for error in data["detail"])


@pytest.mark.unit
class TestUserLogin:
    """Test user login endpoint."""
    
    async def test_login_valid_credentials_success(self, client: AsyncClient, test_user):
        """Should successfully login with valid credentials."""
        login_data = {
            "username": test_user.email,  # OAuth2 spec uses 'username'
            "password": "TestPassword123!"
        }
        
        response = await client.post("/auth/login", data=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
    
    async def test_login_invalid_email_fails(self, client: AsyncClient):
        """Should fail with non-existent email."""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "SomePassword123!"
        }
        
        response = await client.post("/auth/login", data=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "incorrect" in data["detail"].lower()
    
    async def test_login_wrong_password_fails(self, client: AsyncClient, test_user):
        """Should fail with wrong password."""
        login_data = {
            "username": test_user.email,
            "password": "WrongPassword123!"
        }
        
        response = await client.post("/auth/login", data=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "incorrect" in data["detail"].lower()
    
    async def test_login_inactive_user_fails(self, client: AsyncClient, inactive_user):
        """Should fail when user is inactive."""
        login_data = {
            "username": inactive_user.email,
            "password": "TestPassword123!"
        }
        
        response = await client.post("/auth/login", data=login_data)
        
        assert response.status_code == 403
        data = response.json()
        assert "detail" in data
        assert "inactive" in data["detail"].lower()


@pytest.mark.unit
class TestCurrentUser:
    """Test current user endpoint."""
    
    async def test_get_current_user_success(self, client: AsyncClient, auth_headers):
        """Should return current user data with valid token."""
        response = await client.get("/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "full_name" in data
        assert "id" in data
        assert "password" not in data
    
    async def test_get_current_user_no_token_fails(self, client: AsyncClient):
        """Should fail without authentication token."""
        response = await client.get("/auth/me")
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "not authenticated" in data["detail"].lower()
    
    async def test_get_current_user_invalid_token_fails(self, client: AsyncClient):
        """Should fail with invalid token."""
        headers = {"Authorization": "Bearer invalid-token"}
        response = await client.get("/auth/me", headers=headers)
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "not validate" in data["detail"].lower()


@pytest.mark.unit
class TestTokenRefresh:
    """Test token refresh endpoint."""
    
    async def test_refresh_token_success(self, client: AsyncClient, auth_headers):
        """Should successfully refresh access token."""
        response = await client.post("/auth/refresh", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
    
    async def test_refresh_expired_token_fails(self, client: AsyncClient, expired_token_headers):
        """Should fail with expired token."""
        response = await client.post("/auth/refresh", headers=expired_token_headers)
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "expired" in data["detail"].lower()