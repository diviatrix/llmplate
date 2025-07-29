"""
Unit tests for OAuth authentication endpoints.
Following TDD - writing tests first.
"""
import pytest
from httpx import AsyncClient
from urllib.parse import urlparse, parse_qs


@pytest.mark.unit
class TestOAuthGoogle:
    """Test Google OAuth endpoints."""
    
    async def test_google_oauth_redirect(self, client: AsyncClient):
        """Should redirect to Google OAuth with correct parameters."""
        response = await client.get("/auth/oauth/google", follow_redirects=False)
        
        assert response.status_code == 307  # Temporary redirect
        location = response.headers["location"]
        
        # Parse redirect URL
        parsed = urlparse(location)
        assert "accounts.google.com" in parsed.netloc
        assert "/o/oauth2/v2/auth" in parsed.path
        
        # Check query parameters
        params = parse_qs(parsed.query)
        assert "client_id" in params
        assert "redirect_uri" in params
        assert "response_type" in params
        assert params["response_type"][0] == "code"
        assert "scope" in params
        assert "email" in params["scope"][0]
        assert "profile" in params["scope"][0]
    
    async def test_google_oauth_callback_success(self, client: AsyncClient, mocker):
        """Should handle Google OAuth callback successfully."""
        # Mock Google token exchange
        mock_token_response = {
            "access_token": "mock-google-access-token",
            "token_type": "Bearer",
            "id_token": "mock-id-token"
        }
        
        # Mock Google user info
        mock_user_info = {
            "email": "googleuser@gmail.com",
            "name": "Google User",
            "email_verified": True,
            "sub": "google-user-id-123"
        }
        
        mocker.patch("app.auth.oauth.exchange_google_code", return_value=mock_token_response)
        mocker.patch("app.auth.oauth.get_google_user_info", return_value=mock_user_info)
        
        response = await client.get("/auth/oauth/google/callback?code=mock-auth-code")
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == mock_user_info["email"]
        assert data["user"]["full_name"] == mock_user_info["name"]
    
    async def test_google_oauth_callback_no_code_fails(self, client: AsyncClient):
        """Should fail when no authorization code provided."""
        response = await client.get("/auth/oauth/google/callback")
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "code" in data["detail"].lower()
    
    async def test_google_oauth_callback_invalid_code_fails(self, client: AsyncClient, mocker):
        """Should fail with invalid authorization code."""
        mocker.patch("app.auth.oauth.exchange_google_code", side_effect=Exception("Invalid code"))
        
        response = await client.get("/auth/oauth/google/callback?code=invalid-code")
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "failed" in data["detail"].lower()


@pytest.mark.unit
class TestOAuthGitHub:
    """Test GitHub OAuth endpoints."""
    
    async def test_github_oauth_redirect(self, client: AsyncClient):
        """Should redirect to GitHub OAuth with correct parameters."""
        response = await client.get("/auth/oauth/github", follow_redirects=False)
        
        assert response.status_code == 307  # Temporary redirect
        location = response.headers["location"]
        
        # Parse redirect URL
        parsed = urlparse(location)
        assert "github.com" in parsed.netloc
        assert "/login/oauth/authorize" in parsed.path
        
        # Check query parameters
        params = parse_qs(parsed.query)
        assert "client_id" in params
        assert "redirect_uri" in params
        assert "scope" in params
        assert "user:email" in params["scope"][0]
    
    async def test_github_oauth_callback_success(self, client: AsyncClient, mocker):
        """Should handle GitHub OAuth callback successfully."""
        # Mock GitHub token exchange
        mock_token_response = {
            "access_token": "gho_mockGitHubAccessToken123",
            "token_type": "bearer",
            "scope": "user:email"
        }
        
        # Mock GitHub user info
        mock_user_info = {
            "login": "githubuser",
            "email": "githubuser@example.com",
            "name": "GitHub User",
            "id": 12345
        }
        
        mocker.patch("app.auth.oauth.exchange_github_code", return_value=mock_token_response)
        mocker.patch("app.auth.oauth.get_github_user_info", return_value=mock_user_info)
        
        response = await client.get("/auth/oauth/github/callback?code=mock-auth-code")
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == mock_user_info["email"]
        assert data["user"]["full_name"] == mock_user_info["name"]
    
    async def test_github_oauth_callback_no_email_creates_placeholder(self, client: AsyncClient, mocker):
        """Should create placeholder email if GitHub doesn't provide one."""
        # Mock GitHub token exchange
        mock_token_response = {
            "access_token": "gho_mockGitHubAccessToken123",
            "token_type": "bearer"
        }
        
        # Mock GitHub user info without email
        mock_user_info = {
            "login": "githubuser",
            "email": None,  # No email provided
            "name": "GitHub User",
            "id": 12345
        }
        
        mocker.patch("app.auth.oauth.exchange_github_code", return_value=mock_token_response)
        mocker.patch("app.auth.oauth.get_github_user_info", return_value=mock_user_info)
        
        response = await client.get("/auth/oauth/github/callback?code=mock-auth-code")
        
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert data["user"]["email"] == "githubuser@users.noreply.github.com"
    
    async def test_github_oauth_callback_error_parameter_fails(self, client: AsyncClient):
        """Should fail when GitHub returns an error."""
        response = await client.get("/auth/oauth/github/callback?error=access_denied&error_description=User%20denied%20access")
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "access_denied" in data["detail"]