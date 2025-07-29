"""
Main FastAPI application.
"""
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.config import get_settings
from app.database import connect_to_database, close_database_connection, check_database_health
from app.api.auth import router as auth_router
from app.api.providers import router as providers_router
from app.api.templates import router as templates_router
from app.api.generation import router as generation_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application lifespan events."""
    # Startup
    await connect_to_database()
    yield
    # Shutdown
    await close_database_connection()


# Create FastAPI app
app = FastAPI(
    title="LLM Template System",
    description="Backend system for LLM template generation with OpenRouter and Ollama",
    version=__version__,
    lifespan=lifespan
)

# Configure CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(providers_router)
app.include_router(templates_router)
app.include_router(generation_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    # Check database health
    try:
        db_status = await check_database_health()
    except Exception as e:
        db_status = {
            "connected": False,
            "error": str(e)
        }
    
    # Determine overall health status
    status = "healthy" if db_status.get("connected", False) else "degraded"
    
    return {
        "status": status,
        "version": __version__,
        "environment": settings.environment,
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_status
    }