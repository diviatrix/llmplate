#!/usr/bin/env python3
"""
Quick test script to verify auth implementation works.
Run this after installing dependencies.
"""
import asyncio
import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

async def test_basic_functionality():
    """Test basic auth functionality without full test suite."""
    try:
        # Test password hashing
        from app.auth.password import get_password_hash, verify_password
        
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed), "Password verification failed"
        print("✅ Password hashing works")
        
        # Test JWT tokens
        from app.auth.jwt import create_access_token, get_user_email_from_token
        from datetime import timedelta
        
        test_email = "test@example.com"
        token = create_access_token(
            data={"sub": test_email}, 
            expires_delta=timedelta(minutes=30)
        )
        extracted_email = get_user_email_from_token(token)
        assert extracted_email == test_email, "JWT token extraction failed"
        print("✅ JWT tokens work")
        
        # Test OAuth providers (without actual API calls)
        from app.auth.oauth import get_google_oauth, get_github_oauth
        
        # This will work even without real credentials
        google = get_google_oauth()
        github = get_github_oauth()
        
        # Test URL generation (should not fail)
        google_url = google.get_authorization_url("http://localhost/callback")
        github_url = github.get_authorization_url("http://localhost/callback")
        
        assert "accounts.google.com" in google_url, "Google OAuth URL invalid"
        assert "github.com" in github_url, "GitHub OAuth URL invalid"
        print("✅ OAuth providers work")
        
        # Test models (without database)
        from app.models.user import User
        from app.models.template import Template
        from app.models.generation import Generation
        from datetime import datetime
        
        # Create model instances (not saved to DB)
        user = User(
            email="test@example.com",
            full_name="Test User",
            hashed_password=hashed,
            is_active=True
        )
        
        user_dict = user.dict_public()
        assert "email" in user_dict, "User dict_public failed"
        assert "hashed_password" not in user_dict, "Password leaked in public dict"
        print("✅ Models work")
        
        print("\n🎉 All basic functionality tests passed!")
        print("Ready to run full test suite with: pytest tests/unit/test_auth.py -v")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    # Set required environment variables for testing
    os.environ["SECRET_KEY"] = "test-secret-key-for-development-only"
    os.environ["ENVIRONMENT"] = "testing"
    
    success = asyncio.run(test_basic_functionality())
    sys.exit(0 if success else 1)