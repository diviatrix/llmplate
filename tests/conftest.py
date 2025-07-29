"""
Pytest configuration and shared fixtures.
"""
import asyncio
import os
from datetime import datetime, timedelta
from typing import AsyncGenerator, Generator

import pytest
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient
from jose import jwt

from app.main import app
from app.config import get_settings
from app.database import get_database


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings():
    """Override settings for testing."""
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["MONGODB_DB_NAME"] = "llm_template_test"
    os.environ["SECRET_KEY"] = "test-secret-key"
    return get_settings()


@pytest.fixture
async def test_db(test_settings):
    """Create a test database connection."""
    client = AsyncIOMotorClient(test_settings.mongodb_url)
    db = client[test_settings.mongodb_db_name]
    
    yield db
    
    # Cleanup: drop test database
    await client.drop_database(test_settings.mongodb_db_name)
    client.close()


@pytest.fixture
async def client(test_db) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client for the FastAPI app."""
    async def override_get_database():
        return test_db
    
    app.dependency_overrides[get_database] = override_get_database
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


# Auth test fixtures
@pytest.fixture
async def test_user(test_db):
    """Create a test user."""
    from app.models.user import User
    from app.auth.password import get_password_hash
    
    user = User(
        email="testuser@example.com",
        full_name="Test User",
        hashed_password=get_password_hash("TestPassword123!"),
        is_active=True,
        created_at=datetime.utcnow()
    )
    await user.insert()
    
    yield user
    
    # Cleanup
    await user.delete()


@pytest.fixture
async def inactive_user(test_db):
    """Create an inactive test user."""
    from app.models.user import User
    from app.auth.password import get_password_hash
    
    user = User(
        email="inactive@example.com",
        full_name="Inactive User",
        hashed_password=get_password_hash("TestPassword123!"),
        is_active=False,
        created_at=datetime.utcnow()
    )
    await user.insert()
    
    yield user
    
    # Cleanup
    await user.delete()


@pytest.fixture
def auth_headers(test_user, test_settings):
    """Create authorization headers with valid token."""
    from app.auth.jwt import create_access_token
    
    token = create_access_token(
        data={"sub": test_user.email},
        expires_delta=timedelta(minutes=30)
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def expired_token_headers(test_user, test_settings):
    """Create authorization headers with expired token."""
    payload = {
        "sub": test_user.email,
        "exp": datetime.utcnow() - timedelta(hours=1)
    }
    token = jwt.encode(payload, test_settings.secret_key, algorithm=test_settings.algorithm)
    return {"Authorization": f"Bearer {token}"}


# Template test fixtures
@pytest.fixture
async def test_template(test_db, test_user):
    """Create a test template."""
    from app.models.template import Template
    
    template = Template(
        name="Test Template",
        description="Template for testing",
        category="education",
        tags=["test", "quiz"],
        system_prompt="You are a helpful assistant.",
        user_prompt="Generate {{count}} questions about {{topic}}.",
        variables={
            "count": {
                "type": "number",
                "description": "Number of questions",
                "default": 5,
                "min": 1,
                "max": 20
            },
            "topic": {
                "type": "string",
                "description": "Topic for questions",
                "default": "general"
            }
        },
        output_schema={
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "answer": {"type": "string"}
                }
            }
        },
        provider_settings={
            "recommended_provider": "openrouter",
            "recommended_model": "anthropic/claude-3.5-sonnet",
            "temperature": 0.7
        },
        validation_mode="strict",
        is_public=True,
        created_by=test_user
    )
    await template.insert()
    
    yield template
    
    # Cleanup
    await template.delete()


@pytest.fixture
async def other_user_template(test_db):
    """Create a template owned by another user."""
    from app.models.user import User
    from app.models.template import Template
    from app.auth.password import get_password_hash
    
    # Create another user
    other_user = User(
        email="otheruser@example.com",
        full_name="Other User",
        hashed_password=get_password_hash("Password123!"),
        is_active=True
    )
    await other_user.insert()
    
    # Create template owned by other user
    template = Template(
        name="Other User Template",
        description="Template owned by another user",
        category="content",
        tags=["other"],
        system_prompt="System prompt",
        user_prompt="User prompt {{var}}.",
        variables={"var": {"type": "string", "default": "value"}},
        is_public=False,
        created_by=other_user
    )
    await template.insert()
    
    yield template
    
    # Cleanup
    await template.delete()
    await other_user.delete()