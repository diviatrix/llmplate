"""
Template API endpoints.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field

from app.auth.dependencies import get_current_user, get_optional_current_user
from app.models.user import User
from app.models.template import Template
from app.templates.service import TemplateService

router = APIRouter(prefix="/templates", tags=["templates"])

# Initialize service
template_service = TemplateService()


# Pydantic models
class TemplateCreate(BaseModel):
    """Template creation request."""
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=1000)
    category: str = Field(..., pattern="^(education|content|research|business|other)$")
    tags: List[str] = Field(default_factory=list, max_items=10)
    system_prompt: str
    user_prompt: str
    variables: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    output_schema: Optional[Dict[str, Any]] = None
    provider_settings: Dict[str, Any] = Field(default_factory=dict)
    validation_mode: str = Field(default="strict", pattern="^(strict|custom|none)$")
    validation_rules: Dict[str, Any] = Field(default_factory=dict)
    is_public: bool = Field(default=True)


class TemplateUpdate(BaseModel):
    """Template update request."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1, max_length=1000)
    category: Optional[str] = Field(None, pattern="^(education|content|research|business|other)$")
    tags: Optional[List[str]] = Field(None, max_items=10)
    system_prompt: Optional[str] = None
    user_prompt: Optional[str] = None
    variables: Optional[Dict[str, Dict[str, Any]]] = None
    output_schema: Optional[Dict[str, Any]] = None
    provider_settings: Optional[Dict[str, Any]] = None
    validation_mode: Optional[str] = Field(None, pattern="^(strict|custom|none)$")
    validation_rules: Optional[Dict[str, Any]] = None
    is_public: Optional[bool] = None


class TemplateResponse(BaseModel):
    """Template response model."""
    id: str
    name: str
    description: str
    category: str
    tags: List[str]
    system_prompt: str
    user_prompt: str
    variables: Dict[str, Dict[str, Any]]
    output_schema: Optional[Dict[str, Any]]
    provider_settings: Dict[str, Any]
    validation_mode: str
    validation_rules: Dict[str, Any]
    is_public: bool
    created_by: Optional[str]
    created_at: str
    updated_at: str


class TemplateValidationRequest(BaseModel):
    """Template validation request."""
    system_prompt: str
    user_prompt: str
    variables: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    output_schema: Optional[Dict[str, Any]] = None


class TemplateValidationResponse(BaseModel):
    """Template validation response."""
    valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class TemplatePreviewRequest(BaseModel):
    """Template preview request."""
    template_id: Optional[str] = None
    template: Optional[Dict[str, Any]] = None
    variables: Dict[str, Any] = Field(default_factory=dict)
    template_variables: Optional[Dict[str, Any]] = None


class TemplatePreviewResponse(BaseModel):
    """Template preview response."""
    system_prompt: str
    user_prompt: str


@router.post("", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_data: TemplateCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new template."""
    try:
        template = await template_service.create_template(
            template_data.dict(),
            current_user
        )
        return TemplateResponse(**template.dict_public())
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=List[TemplateResponse])
async def list_templates(
    category: Optional[str] = Query(None, pattern="^(education|content|research|business|other)$"),
    tag: Optional[str] = Query(None),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """List templates (public for anonymous, public + own for authenticated)."""
    templates = await template_service.list_templates(
        category=category,
        tag=tag,
        user=current_user
    )
    
    return [TemplateResponse(**t.dict_public()) for t in templates]


@router.get("/examples", response_model=List[Dict[str, Any]])
async def list_example_templates():
    """List built-in example templates."""
    return template_service.list_example_templates()


@router.post("/examples/{example_id}/import", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def import_example_template(
    example_id: str,
    current_user: User = Depends(get_current_user)
):
    """Import an example template as user's template."""
    template = await template_service.import_example_template(example_id, current_user)
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Example template {example_id} not found"
        )
    
    return TemplateResponse(**template.dict_public())


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: str,
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Get template by ID."""
    template = await template_service.get_template(template_id)
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Check access rights
    if not template.is_public:
        if not current_user or str(template.created_by.id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to private template"
            )
    
    return TemplateResponse(**template.dict_public())


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: str,
    update_data: TemplateUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update template (owner only)."""
    try:
        # Filter out None values
        update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
        
        template = await template_service.update_template(
            template_id,
            update_dict,
            current_user
        )
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        return TemplateResponse(**template.dict_public())
        
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete template (owner only)."""
    try:
        success = await template_service.delete_template(template_id, current_user)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
            
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.post("/validate", response_model=TemplateValidationResponse)
async def validate_template(template_data: TemplateValidationRequest):
    """Validate template structure without creating it."""
    result = template_service.validate_template_data(template_data.dict())
    return TemplateValidationResponse(**result)


@router.post("/preview", response_model=TemplatePreviewResponse)
async def preview_template(
    preview_data: TemplatePreviewRequest,
    current_user: User = Depends(get_current_user)
):
    """Preview template rendering with variables."""
    # Get template data
    if preview_data.template_id:
        # Load template from database
        template = await template_service.get_template(preview_data.template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        # Check access
        if not template.is_public and str(template.created_by.id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to private template"
            )
        
        template_dict = {
            "system_prompt": template.system_prompt,
            "user_prompt": template.user_prompt,
            "variables": template.variables
        }
    elif preview_data.template:
        template_dict = preview_data.template
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either template_id or template must be provided"
        )
    
    # Preview rendering
    try:
        rendered = template_service.preview_template(
            template_dict,
            preview_data.variables,
            preview_data.template_variables
        )
        return TemplatePreviewResponse(**rendered)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Template rendering error: {str(e)}"
        )