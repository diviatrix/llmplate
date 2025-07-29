"""
Unit tests for template system endpoints.
Following TDD - writing tests first.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.unit
class TestTemplatesCRUD:
    """Test template CRUD operations."""
    
    async def test_create_template(self, client: AsyncClient, auth_headers):
        """Should create a new template."""
        template_data = {
            "name": "Test Quiz Template",
            "description": "Template for generating quiz questions",
            "category": "education",
            "tags": ["quiz", "test", "education"],
            "system_prompt": "You are a quiz question generator.",
            "user_prompt": "Generate {{count}} quiz questions about {{topic}}.",
            "variables": {
                "count": {
                    "type": "number",
                    "description": "Number of questions",
                    "default": 5,
                    "min": 1,
                    "max": 20
                },
                "topic": {
                    "type": "string",
                    "description": "Quiz topic",
                    "default": "general knowledge"
                }
            },
            "output_schema": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "question": {"type": "string"},
                        "answers": {"type": "array", "items": {"type": "string"}},
                        "correct": {"type": "number"}
                    }
                }
            },
            "provider_settings": {
                "recommended_provider": "openrouter",
                "recommended_model": "anthropic/claude-3.5-sonnet",
                "temperature": 0.7,
                "max_tokens": 1000
            },
            "validation_mode": "strict"
        }
        
        response = await client.post(
            "/templates",
            json=template_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == template_data["name"]
        assert data["category"] == template_data["category"]
        assert "id" in data
        assert data["created_by"] is not None
    
    async def test_create_template_unauthorized(self, client: AsyncClient):
        """Should require authentication to create template."""
        template_data = {"name": "Test", "description": "Test"}
        
        response = await client.post("/templates", json=template_data)
        assert response.status_code == 401
    
    async def test_list_templates(self, client: AsyncClient):
        """Should list public templates."""
        response = await client.get("/templates")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Check template structure
        if len(data) > 0:
            template = data[0]
            assert "id" in template
            assert "name" in template
            assert "category" in template
            assert "tags" in template
            assert "is_public" in template
    
    async def test_list_templates_with_filters(self, client: AsyncClient):
        """Should filter templates by category and tags."""
        # Filter by category
        response = await client.get("/templates?category=education")
        assert response.status_code == 200
        templates = response.json()
        for template in templates:
            assert template["category"] == "education"
        
        # Filter by tag
        response = await client.get("/templates?tag=quiz")
        assert response.status_code == 200
        templates = response.json()
        for template in templates:
            assert "quiz" in template["tags"]
    
    async def test_get_template_by_id(self, client: AsyncClient, test_template):
        """Should get template by ID."""
        response = await client.get(f"/templates/{test_template.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_template.id)
        assert data["name"] == test_template.name
        assert "system_prompt" in data
        assert "user_prompt" in data
        assert "variables" in data
    
    async def test_get_template_not_found(self, client: AsyncClient):
        """Should return 404 for non-existent template."""
        response = await client.get("/templates/507f1f77bcf86cd799439011")
        assert response.status_code == 404
    
    async def test_update_template(self, client: AsyncClient, auth_headers, test_template):
        """Should update own template."""
        update_data = {
            "name": "Updated Template Name",
            "description": "Updated description"
        }
        
        response = await client.put(
            f"/templates/{test_template.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
    
    async def test_update_template_forbidden(self, client: AsyncClient, auth_headers, other_user_template):
        """Should not allow updating other user's template."""
        update_data = {"name": "Hacked Name"}
        
        response = await client.put(
            f"/templates/{other_user_template.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 403
    
    async def test_delete_template(self, client: AsyncClient, auth_headers, test_template):
        """Should delete own template."""
        response = await client.delete(
            f"/templates/{test_template.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 204
        
        # Verify deletion
        response = await client.get(f"/templates/{test_template.id}")
        assert response.status_code == 404


@pytest.mark.unit
class TestTemplateValidation:
    """Test template validation functionality."""
    
    async def test_validate_template_structure(self, client: AsyncClient):
        """Should validate template structure."""
        template_data = {
            "system_prompt": "You are a helpful assistant.",
            "user_prompt": "Generate {{count}} items about {{topic}}.",
            "variables": {
                "count": {
                    "type": "number",
                    "default": 5,
                    "min": 1,
                    "max": 10
                },
                "topic": {
                    "type": "string",
                    "default": "science"
                }
            },
            "output_schema": {
                "type": "array",
                "items": {"type": "string"}
            }
        }
        
        response = await client.post(
            "/templates/validate",
            json=template_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert "errors" not in data or len(data["errors"]) == 0
    
    async def test_validate_template_invalid_jinja2(self, client: AsyncClient):
        """Should detect invalid Jinja2 syntax."""
        template_data = {
            "system_prompt": "System prompt",
            "user_prompt": "Invalid {{variable} syntax",  # Missing closing braces
            "variables": {}
        }
        
        response = await client.post(
            "/templates/validate",
            json=template_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert "errors" in data
        assert any("syntax" in error.lower() for error in data["errors"])
    
    async def test_validate_template_undefined_variables(self, client: AsyncClient):
        """Should detect undefined variables in prompts."""
        template_data = {
            "system_prompt": "System prompt",
            "user_prompt": "Generate {{count}} items about {{topic}} in {{language}}.",
            "variables": {
                "count": {"type": "number", "default": 5},
                "topic": {"type": "string", "default": "science"}
                # 'language' is missing
            }
        }
        
        response = await client.post(
            "/templates/validate",
            json=template_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert "warnings" in data
        assert any("language" in warning for warning in data["warnings"])
    
    async def test_validate_json_schema(self, client: AsyncClient):
        """Should validate output JSON schema."""
        template_data = {
            "system_prompt": "System prompt",
            "user_prompt": "Generate data",
            "variables": {},
            "output_schema": {
                "type": "invalid_type",  # Invalid JSON schema type
                "properties": {}
            }
        }
        
        response = await client.post(
            "/templates/validate",
            json=template_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert "errors" in data


@pytest.mark.unit
class TestTemplateRendering:
    """Test template rendering functionality."""
    
    async def test_preview_template_rendering(self, client: AsyncClient, auth_headers):
        """Should preview rendered template with variables."""
        preview_data = {
            "template_id": None,  # Can use inline template
            "template": {
                "system_prompt": "You are a {{role}} assistant.",
                "user_prompt": "Generate {{count}} {{type}} about {{topic}}."
            },
            "variables": {
                "role": "helpful",
                "count": 5,
                "type": "examples",
                "topic": "machine learning"
            }
        }
        
        response = await client.post(
            "/templates/preview",
            json=preview_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["system_prompt"] == "You are a helpful assistant."
        assert data["user_prompt"] == "Generate 5 examples about machine learning."
    
    async def test_preview_with_template_id(self, client: AsyncClient, auth_headers, test_template):
        """Should preview rendering using existing template."""
        preview_data = {
            "template_id": str(test_template.id),
            "variables": {
                "count": 10,
                "topic": "history"
            }
        }
        
        response = await client.post(
            "/templates/preview",
            json=preview_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "10" in data["user_prompt"]
        assert "history" in data["user_prompt"]
    
    async def test_preview_with_missing_variables(self, client: AsyncClient, auth_headers):
        """Should use default values for missing variables."""
        preview_data = {
            "template": {
                "system_prompt": "System",
                "user_prompt": "Generate {{count}} items."
            },
            "variables": {},  # count not provided
            "template_variables": {
                "count": {"type": "number", "default": 5}
            }
        }
        
        response = await client.post(
            "/templates/preview",
            json=preview_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "5" in data["user_prompt"]  # Should use default


@pytest.mark.unit
class TestTemplateExamples:
    """Test built-in template examples."""
    
    async def test_list_example_templates(self, client: AsyncClient):
        """Should list built-in example templates."""
        response = await client.get("/templates/examples")
        
        assert response.status_code == 200
        examples = response.json()
        assert isinstance(examples, list)
        assert len(examples) > 0
        
        # Check for expected examples
        example_names = [e["name"] for e in examples]
        assert any("quiz" in name.lower() for name in example_names)
        assert any("article" in name.lower() for name in example_names)
    
    async def test_import_example_template(self, client: AsyncClient, auth_headers):
        """Should import example template as user's template."""
        # Get examples first
        response = await client.get("/templates/examples")
        examples = response.json()
        example_id = examples[0]["id"]
        
        # Import example
        response = await client.post(
            f"/templates/examples/{example_id}/import",
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["created_by"] is not None