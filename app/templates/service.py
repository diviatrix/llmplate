"""
Template service for business logic.
"""
import json
import os
from typing import List, Optional, Dict, Any
from pathlib import Path

from app.models.template import Template
from app.models.user import User
from app.templates.validator import TemplateValidator
from app.templates.renderer import TemplateRenderer


class TemplateService:
    """Service for template operations."""
    
    def __init__(self):
        self.validator = TemplateValidator()
        self.renderer = TemplateRenderer()
        
        # Path to example templates
        self.examples_path = Path(__file__).parent.parent.parent / "templates" / "examples"
    
    async def create_template(
        self, 
        template_data: Dict[str, Any], 
        user: User
    ) -> Template:
        """Create a new template."""
        # Validate template
        is_valid, errors, warnings = self.validator.validate_template(template_data)
        if not is_valid:
            raise ValueError(f"Invalid template: {'; '.join(errors)}")
        
        # Create template
        template = Template(
            **template_data,
            created_by=user
        )
        await template.insert()
        
        return template
    
    async def list_templates(
        self,
        category: Optional[str] = None,
        tag: Optional[str] = None,
        is_public: Optional[bool] = None,
        user: Optional[User] = None
    ) -> List[Template]:
        """List templates with filters."""
        # Build query
        query_conditions = []
        
        if category:
            query_conditions.append(Template.category == category)
        
        if tag:
            query_conditions.append(Template.tags.in_([tag]))
        
        if is_public is not None:
            query_conditions.append(Template.is_public == is_public)
        
        if user:
            # Show user's templates and public templates
            query_conditions.append(
                (Template.created_by.id == user.id) | (Template.is_public == True)
            )
        else:
            # Only show public templates for anonymous users
            query_conditions.append(Template.is_public == True)
        
        # Execute query
        if query_conditions:
            templates = await Template.find(*query_conditions).to_list()
        else:
            templates = await Template.find_all().to_list()
        
        return templates
    
    async def get_template(self, template_id: str) -> Optional[Template]:
        """Get template by ID."""
        try:
            return await Template.get(template_id)
        except:
            return None
    
    async def update_template(
        self, 
        template_id: str, 
        update_data: Dict[str, Any],
        user: User
    ) -> Optional[Template]:
        """Update template if user owns it."""
        template = await self.get_template(template_id)
        if not template:
            return None
        
        # Check ownership
        if str(template.created_by.id) != str(user.id):
            raise PermissionError("Cannot update template you don't own")
        
        # Validate if template structure changed
        if any(key in update_data for key in ["system_prompt", "user_prompt", "variables", "output_schema"]):
            # Merge update data with existing template
            template_dict = template.dict()
            template_dict.update(update_data)
            
            is_valid, errors, warnings = self.validator.validate_template(template_dict)
            if not is_valid:
                raise ValueError(f"Invalid template update: {'; '.join(errors)}")
        
        # Update template
        for key, value in update_data.items():
            if hasattr(template, key):
                setattr(template, key, value)
        
        await template.save()
        return template
    
    async def delete_template(self, template_id: str, user: User) -> bool:
        """Delete template if user owns it."""
        template = await self.get_template(template_id)
        if not template:
            return False
        
        # Check ownership
        if str(template.created_by.id) != str(user.id):
            raise PermissionError("Cannot delete template you don't own")
        
        await template.delete()
        return True
    
    def validate_template_data(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate template data and return validation result."""
        is_valid, errors, warnings = self.validator.validate_template(template_data)
        
        return {
            "valid": is_valid,
            "errors": errors,
            "warnings": warnings
        }
    
    def preview_template(
        self,
        template: Dict[str, Any],
        variables: Dict[str, Any],
        variable_definitions: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """Preview rendered template with variables."""
        # Use variable definitions from template if not provided
        if variable_definitions is None and "variables" in template:
            variable_definitions = template["variables"]
        
        # Render prompts
        rendered = {}
        
        if "system_prompt" in template:
            rendered["system_prompt"] = self.renderer.render_prompt(
                template["system_prompt"],
                variables,
                variable_definitions
            )
        
        if "user_prompt" in template:
            rendered["user_prompt"] = self.renderer.render_prompt(
                template["user_prompt"],
                variables,
                variable_definitions
            )
        
        return rendered
    
    def list_example_templates(self) -> List[Dict[str, Any]]:
        """List available example templates."""
        examples = []
        
        if not self.examples_path.exists():
            return examples
        
        for file_path in self.examples_path.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    template_data = json.load(f)
                    template_data["id"] = file_path.stem
                    examples.append(template_data)
            except:
                continue
        
        return examples
    
    def get_example_template(self, example_id: str) -> Optional[Dict[str, Any]]:
        """Get example template by ID."""
        file_path = self.examples_path / f"{example_id}.json"
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
                template_data["id"] = example_id
                return template_data
        except:
            return None
    
    async def import_example_template(
        self, 
        example_id: str, 
        user: User
    ) -> Optional[Template]:
        """Import an example template as user's template."""
        example_data = self.get_example_template(example_id)
        if not example_data:
            return None
        
        # Remove example-specific fields
        example_data.pop("id", None)
        
        # Create as user's template
        return await self.create_template(example_data, user)