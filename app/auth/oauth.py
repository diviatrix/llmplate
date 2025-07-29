"""
OAuth providers integration (Google, GitHub).
"""
from typing import Dict, Any, Optional
import httpx
from urllib.parse import urlencode

from app.config import get_settings


class OAuthProvider:
    """Base OAuth provider class."""
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
    
    def get_authorization_url(self, redirect_uri: str, state: str = None) -> str:
        """Get OAuth authorization URL."""
        raise NotImplementedError
    
    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for access token."""
        raise NotImplementedError
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information using access token."""
        raise NotImplementedError


class GoogleOAuth(OAuthProvider):
    """Google OAuth provider."""
    
    AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
    
    def get_authorization_url(self, redirect_uri: str, state: str = None) -> str:
        """Get Google OAuth authorization URL."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline"
        }
        if state:
            params["state"] = state
        
        return f"{self.AUTHORIZATION_URL}?{urlencode(params)}"
    
    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange Google authorization code for access token."""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(self.TOKEN_URL, data=data)
            response.raise_for_status()
            return response.json()
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get Google user information."""
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(self.USERINFO_URL, headers=headers)
            response.raise_for_status()
            return response.json()


class GitHubOAuth(OAuthProvider):
    """GitHub OAuth provider."""
    
    AUTHORIZATION_URL = "https://github.com/login/oauth/authorize"
    TOKEN_URL = "https://github.com/login/oauth/access_token"
    USERINFO_URL = "https://api.github.com/user"
    
    def get_authorization_url(self, redirect_uri: str, state: str = None) -> str:
        """Get GitHub OAuth authorization URL."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": "user:email",
        }
        if state:
            params["state"] = state
        
        return f"{self.AUTHORIZATION_URL}?{urlencode(params)}"
    
    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange GitHub authorization code for access token."""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": redirect_uri
        }
        
        headers = {"Accept": "application/json"}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(self.TOKEN_URL, data=data, headers=headers)
            response.raise_for_status()
            return response.json()
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get GitHub user information."""
        headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(self.USERINFO_URL, headers=headers)
            response.raise_for_status()
            user_data = response.json()
            
            # GitHub might not provide email in the main endpoint
            if not user_data.get("email"):
                # Try to get primary email
                email_response = await client.get(
                    "https://api.github.com/user/emails", 
                    headers=headers
                )
                if email_response.status_code == 200:
                    emails = email_response.json()
                    primary_email = next((e for e in emails if e.get("primary")), None)
                    if primary_email:
                        user_data["email"] = primary_email["email"]
                    else:
                        # Fallback to noreply email
                        user_data["email"] = f"{user_data['login']}@users.noreply.github.com"
                else:
                    # Fallback to noreply email
                    user_data["email"] = f"{user_data['login']}@users.noreply.github.com"
            
            return user_data


# OAuth provider instances
def get_google_oauth() -> GoogleOAuth:
    """Get Google OAuth provider instance."""
    settings = get_settings()
    return GoogleOAuth(settings.google_client_id, settings.google_client_secret)


def get_github_oauth() -> GitHubOAuth:
    """Get GitHub OAuth provider instance."""
    settings = get_settings()
    return GitHubOAuth(settings.github_client_id, settings.github_client_secret)


# Helper functions for tests
async def exchange_google_code(code: str, redirect_uri: str) -> Dict[str, Any]:
    """Helper function for exchanging Google code (used in mocking)."""
    provider = get_google_oauth()
    return await provider.exchange_code_for_token(code, redirect_uri)


async def get_google_user_info(access_token: str) -> Dict[str, Any]:
    """Helper function for getting Google user info (used in mocking)."""
    provider = get_google_oauth()
    return await provider.get_user_info(access_token)


async def exchange_github_code(code: str, redirect_uri: str) -> Dict[str, Any]:
    """Helper function for exchanging GitHub code (used in mocking)."""
    provider = get_github_oauth()
    return await provider.exchange_code_for_token(code, redirect_uri)


async def get_github_user_info(access_token: str) -> Dict[str, Any]:
    """Helper function for getting GitHub user info (used in mocking)."""
    provider = get_github_oauth()
    return await provider.get_user_info(access_token)