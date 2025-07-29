"""
Provider API endpoints.
"""
from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel

from app.providers.factory import ProviderFactory
from app.providers.base import ModelInfo
from app.auth.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/providers", tags=["providers"])


class ProviderInfo(BaseModel):
    """Provider information."""
    id: str
    name: str
    available: bool
    models_count: Optional[int] = None


class ProviderTestRequest(BaseModel):
    """Request for testing provider connection."""
    provider: str


class ProviderTestResponse(BaseModel):
    """Response from provider test."""
    success: bool
    message: str
    response_time_ms: Optional[float] = None
    error: Optional[str] = None


@router.get("", response_model=List[ProviderInfo])
async def list_providers():
    """List all available LLM providers."""
    providers = ProviderFactory.get_all_providers()
    provider_list = []
    
    for provider_id, provider in providers.items():
        # Quick connection check
        connection_info = await provider.check_connection()
        
        provider_info = ProviderInfo(
            id=provider.id,
            name=provider.name,
            available=connection_info.get("available", False)
        )
        
        # Add models count if available
        if "models_count" in connection_info:
            provider_info.models_count = connection_info["models_count"]
        
        provider_list.append(provider_info)
    
    return provider_list


@router.get("/models", response_model=List[ModelInfo])
async def list_models(
    provider: Optional[str] = Query(None, description="Filter by provider"),
    free: Optional[bool] = Query(None, description="Filter free/paid models"),
    online: Optional[bool] = Query(None, description="Filter by online capability")
):
    """List all available models from all providers."""
    all_models = []
    
    # Get providers to query
    if provider:
        provider_instance = ProviderFactory.get_provider(provider)
        if not provider_instance:
            raise HTTPException(status_code=404, detail=f"Provider {provider} not found")
        providers = {provider: provider_instance}
    else:
        providers = ProviderFactory.get_all_providers()
    
    # Collect models from each provider
    for provider_id, provider_instance in providers.items():
        try:
            models = await provider_instance.list_models()
            all_models.extend(models)
        except Exception as e:
            print(f"Error fetching models from {provider_id}: {e}")
            continue
    
    # Apply filters
    if free is not None:
        if free:
            all_models = [
                m for m in all_models 
                if m.pricing["input"] == 0 and m.pricing["output"] == 0
            ]
        else:
            all_models = [
                m for m in all_models 
                if m.pricing["input"] > 0 or m.pricing["output"] > 0
            ]
    
    if online is not None:
        all_models = [
            m for m in all_models 
            if m.capabilities.get("online", False) == online
        ]
    
    return all_models


@router.get("/models/{model_id:path}", response_model=ModelInfo)
async def get_model_details(model_id: str):
    """Get detailed information about a specific model."""
    # Try each provider to find the model
    providers = ProviderFactory.get_all_providers()
    
    for provider_id, provider in providers.items():
        model_info = await provider.get_model_info(model_id)
        if model_info:
            return model_info
    
    raise HTTPException(status_code=404, detail=f"Model {model_id} not found")


@router.post("/test", response_model=ProviderTestResponse)
async def test_provider_connection(
    request: ProviderTestRequest,
    current_user: User = Depends(get_current_user)
):
    """Test connection to a specific provider (requires authentication)."""
    provider = ProviderFactory.get_provider(request.provider)
    
    if not provider:
        raise HTTPException(
            status_code=404, 
            detail=f"Provider {request.provider} not found"
        )
    
    # Test connection
    connection_info = await provider.check_connection()
    
    if connection_info.get("available", False):
        return ProviderTestResponse(
            success=True,
            message=f"Successfully connected to {provider.name}",
            response_time_ms=connection_info.get("response_time_ms")
        )
    else:
        return ProviderTestResponse(
            success=False,
            message=f"Failed to connect to {provider.name}",
            error=connection_info.get("error", "Unknown error")
        )