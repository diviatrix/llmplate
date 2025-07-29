"""
Authentication API endpoints.
"""
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr, Field, validator
import re

from app.auth.password import get_password_hash, verify_password
from app.auth.jwt import create_access_token
from app.auth.oauth import get_google_oauth, get_github_oauth
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.config import get_settings

router = APIRouter(prefix="/auth", tags=["authentication"])

# Pydantic models for requests/responses
class UserRegister(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1)
    
    @validator("password")
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v


class UserResponse(BaseModel):
    """User response model."""
    id: str
    email: str
    full_name: str
    is_active: bool
    created_at: str
    oauth_provider: Optional[str] = None


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class OAuthResponse(BaseModel):
    """OAuth response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    """Register a new user with email and password."""
    # Check if user already exists
    existing_user = await User.find_one(User.email == user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Create new user
    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=get_password_hash(user_data.password),
        is_active=True
    )
    await user.insert()
    
    return UserResponse(**user.dict_public())


@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login with email and password."""
    # Find user by email
    user = await User.find_one(User.email == form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Verify password
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    # Create access token
    settings = get_settings()
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.access_token_expire_minutes * 60
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return UserResponse(**current_user.dict_public())


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(current_user: User = Depends(get_current_user)):
    """Refresh access token."""
    settings = get_settings()
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": current_user.email}, expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.access_token_expire_minutes * 60
    )


# OAuth endpoints
@router.get("/oauth/google")
async def google_oauth_redirect(request: Request):
    """Redirect to Google OAuth."""
    google = get_google_oauth()
    redirect_uri = str(request.url_for("google_oauth_callback"))
    auth_url = google.get_authorization_url(redirect_uri)
    return RedirectResponse(url=auth_url, status_code=307)


@router.get("/oauth/google/callback", response_model=OAuthResponse)
async def google_oauth_callback(request: Request, code: Optional[str] = None, error: Optional[str] = None):
    """Handle Google OAuth callback."""
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth error: {error}"
        )
    
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code not provided"
        )
    
    try:
        google = get_google_oauth()
        redirect_uri = str(request.url_for("google_oauth_callback"))
        
        # Exchange code for token
        token_data = await google.exchange_code_for_token(code, redirect_uri)
        access_token = token_data["access_token"]
        
        # Get user info
        user_info = await google.get_user_info(access_token)
        
        # Find or create user
        user = await User.find_one(User.email == user_info["email"])
        if not user:
            user = User(
                email=user_info["email"],
                full_name=user_info.get("name", ""),
                hashed_password="",  # OAuth users don't have passwords
                is_active=True,
                oauth_provider="google",
                oauth_provider_id=user_info["id"]
            )
            await user.insert()
        else:
            # Update OAuth info if needed
            if not user.oauth_provider:
                user.oauth_provider = "google"
                user.oauth_provider_id = user_info["id"]
                await user.save()
        
        # Create JWT token
        settings = get_settings()
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        jwt_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        
        return OAuthResponse(
            access_token=jwt_token,
            expires_in=settings.access_token_expire_minutes * 60,
            user=UserResponse(**user.dict_public())
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth authentication failed: {str(e)}"
        )


@router.get("/oauth/github")
async def github_oauth_redirect(request: Request):
    """Redirect to GitHub OAuth."""
    github = get_github_oauth()
    redirect_uri = str(request.url_for("github_oauth_callback"))
    auth_url = github.get_authorization_url(redirect_uri)
    return RedirectResponse(url=auth_url, status_code=307)


@router.get("/oauth/github/callback", response_model=OAuthResponse)
async def github_oauth_callback(request: Request, code: Optional[str] = None, error: Optional[str] = None):
    """Handle GitHub OAuth callback."""
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth error: {error}"
        )
    
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code not provided"
        )
    
    try:
        github = get_github_oauth()
        redirect_uri = str(request.url_for("github_oauth_callback"))
        
        # Exchange code for token
        token_data = await github.exchange_code_for_token(code, redirect_uri)
        access_token = token_data["access_token"]
        
        # Get user info
        user_info = await github.get_user_info(access_token)
        
        # GitHub might not provide email
        email = user_info.get("email")
        if not email:
            email = f"{user_info['login']}@users.noreply.github.com"
        
        # Find or create user
        user = await User.find_one(User.email == email)
        if not user:
            user = User(
                email=email,
                full_name=user_info.get("name", user_info["login"]),
                hashed_password="",  # OAuth users don't have passwords
                is_active=True,
                oauth_provider="github",
                oauth_provider_id=str(user_info["id"])
            )
            await user.insert()
        else:
            # Update OAuth info if needed
            if not user.oauth_provider:
                user.oauth_provider = "github"
                user.oauth_provider_id = str(user_info["id"])
                await user.save()
        
        # Create JWT token
        settings = get_settings()
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        jwt_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        
        return OAuthResponse(
            access_token=jwt_token,
            expires_in=settings.access_token_expire_minutes * 60,
            user=UserResponse(**user.dict_public())
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth authentication failed: {str(e)}"
        )