"""
Database configuration and utilities.
"""
import time
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from beanie import init_beanie

from app.config import get_settings

# Global database client
_client: Optional[AsyncIOMotorClient] = None
_database: Optional[AsyncIOMotorDatabase] = None


async def connect_to_database():
    """Create database connection."""
    global _client, _database
    settings = get_settings()
    
    _client = AsyncIOMotorClient(settings.mongodb_url)
    _database = _client[settings.mongodb_db_name]
    
    # Initialize Beanie with document models
    from app.models.user import User
    from app.models.template import Template
    from app.models.generation import Generation
    
    await init_beanie(database=_database, document_models=[User, Template, Generation])


async def close_database_connection():
    """Close database connection."""
    global _client
    if _client:
        _client.close()
        _client = None


def get_database() -> AsyncIOMotorDatabase:
    """Get database instance."""
    if not _database:
        raise RuntimeError("Database not initialized")
    return _database


async def check_database_health() -> dict:
    """Check database health and response time."""
    if not _client:
        raise RuntimeError("Database client not initialized")
    
    start_time = time.time()
    try:
        # Ping database
        await _client.admin.command("ping")
        response_time = (time.time() - start_time) * 1000  # Convert to ms
        
        return {
            "connected": True,
            "response_time_ms": round(response_time, 2)
        }
    except Exception as e:
        return {
            "connected": False,
            "error": str(e)
        }