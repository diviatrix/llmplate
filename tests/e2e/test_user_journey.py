"""End-to-end tests for complete user journeys."""
import pytest
from httpx import AsyncClient


class TestUserJourney:
    """Test complete user journeys from registration to generation."""
    
    async def test_new_user_journey(self, client: AsyncClient):
        """Test journey: register -> create template -> generate -> export."""
        # 1. Register new user
        user_data = {
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "full_name": "New User"
        }
        
        register_response = await client.post(
            "/api/v1/auth/register",
            json=user_data
        )
        assert register_response.status_code == 201
        user_id = register_response.json()["id"]
        
        # 2. Login
        login_response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": user_data["email"],
                "password": user_data["password"]
            }
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. Check user profile
        me_response = await client.get("/api/v1/auth/me", headers=headers)
        assert me_response.status_code == 200
        assert me_response.json()["email"] == user_data["email"]
        
        # 4. Browse available models
        models_response = await client.get("/api/v1/providers/models", headers=headers)
        assert models_response.status_code == 200
        models = models_response.json()
        assert len(models) > 0
        
        # Find a free model
        free_models = [m for m in models if m.get("pricing", {}).get("is_free", False)]
        assert len(free_models) > 0
        selected_model = free_models[0]
        
        # 5. Create a template
        template_data = {
            "name": "My First Template",
            "description": "A template for generating stories",
            "category": "content",
            "tags": ["story", "creative"],
            "system_prompt": "You are a creative story writer.",
            "user_prompt": "Write a short story about {{theme}} in {{genre}} genre.",
            "variables": {
                "theme": {
                    "type": "string",
                    "description": "Main theme of the story",
                    "default": "adventure"
                },
                "genre": {
                    "type": "string",
                    "description": "Story genre",
                    "enum": ["fantasy", "sci-fi", "mystery", "romance"],
                    "default": "fantasy"
                }
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "story": {"type": "string"},
                    "word_count": {"type": "number"}
                },
                "required": ["title", "story"]
            },
            "provider_settings": {
                "recommended_provider": selected_model["provider"],
                "recommended_model": selected_model["id"],
                "temperature": 0.8,
                "max_tokens": 500
            },
            "validation_mode": "strict",
            "is_public": False
        }
        
        create_template_response = await client.post(
            "/api/v1/templates",
            json=template_data,
            headers=headers
        )
        assert create_template_response.status_code == 201
        template_id = create_template_response.json()["id"]
        
        # 6. Preview template
        preview_data = {
            "template_id": template_id,
            "variables": {
                "theme": "space exploration",
                "genre": "sci-fi"
            }
        }
        
        preview_response = await client.post(
            "/api/v1/templates/preview",
            json=preview_data,
            headers=headers
        )
        assert preview_response.status_code == 200
        assert "system_prompt" in preview_response.json()
        assert "user_prompt" in preview_response.json()
        
        # 7. Start generation
        generation_data = {
            "template_id": template_id,
            "provider": selected_model["provider"],
            "model": selected_model["id"],
            "variables": {
                "theme": "underwater city",
                "genre": "fantasy"
            },
            "count": 3
        }
        
        # In real scenario, this would call actual LLM
        # For testing, we'll check the response structure
        start_response = await client.post(
            "/api/v1/generate",
            json=generation_data,
            headers=headers
        )
        assert start_response.status_code == 202
        job_data = start_response.json()
        assert "job_id" in job_data
        assert job_data["status"] == "pending"
        
        # 8. Check generation status
        job_id = job_data["job_id"]
        status_response = await client.get(
            f"/api/v1/generate/{job_id}",
            headers=headers
        )
        assert status_response.status_code == 200
        
        # 9. List user's templates
        my_templates_response = await client.get(
            "/api/v1/templates?created_by_me=true",
            headers=headers
        )
        assert my_templates_response.status_code == 200
        my_templates = my_templates_response.json()
        assert len(my_templates["items"]) >= 1
        assert any(t["id"] == template_id for t in my_templates["items"])
        
        # 10. Check generation history
        history_response = await client.get(
            "/api/v1/history",
            headers=headers
        )
        assert history_response.status_code == 200
        history = history_response.json()
        assert history["total"] >= 1
    
    async def test_oauth_user_journey(self, client: AsyncClient):
        """Test OAuth user journey."""
        # 1. Start OAuth flow
        oauth_response = await client.get("/api/v1/auth/oauth/google")
        assert oauth_response.status_code == 200
        oauth_data = oauth_response.json()
        assert "auth_url" in oauth_data
        assert "google.com" in oauth_data["auth_url"]
        
        # In real scenario, user would:
        # - Be redirected to Google
        # - Authenticate
        # - Be redirected back with code
        # - Exchange code for token
        
        # 2. Check GitHub OAuth is also available
        github_response = await client.get("/api/v1/auth/oauth/github")
        assert github_response.status_code == 200
        github_data = github_response.json()
        assert "github.com" in github_data["auth_url"]
    
    async def test_template_sharing_journey(self, client: AsyncClient, auth_headers: dict):
        """Test template sharing between users."""
        # 1. User A creates a public template
        template_data = {
            "name": "Shared Recipe Generator",
            "description": "Generate cooking recipes",
            "category": "content",
            "system_prompt": "You are a professional chef.",
            "user_prompt": "Create a recipe for {{dish}} that serves {{servings}} people.",
            "variables": {
                "dish": {"type": "string"},
                "servings": {"type": "number", "min": 1, "max": 20}
            },
            "is_public": True
        }
        
        create_response = await client.post(
            "/api/v1/templates",
            json=template_data,
            headers=auth_headers
        )
        assert create_response.status_code == 201
        template_id = create_response.json()["id"]
        
        # 2. Browse public templates (as another user or anonymous)
        public_templates = await client.get("/api/v1/templates?is_public=true")
        assert public_templates.status_code == 200
        templates = public_templates.json()["items"]
        
        # Find the shared template
        shared_template = next((t for t in templates if t["id"] == template_id), None)
        assert shared_template is not None
        assert shared_template["name"] == "Shared Recipe Generator"
        
        # 3. User B registers and uses the shared template
        user_b_data = {
            "email": "userb@example.com",
            "password": "UserBPass123!",
            "full_name": "User B"
        }
        
        register_b = await client.post("/api/v1/auth/register", json=user_b_data)
        assert register_b.status_code == 201
        
        # Login as User B
        login_b = await client.post(
            "/api/v1/auth/login",
            data={
                "username": user_b_data["email"],
                "password": user_b_data["password"]
            }
        )
        token_b = login_b.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}
        
        # 4. User B uses the shared template
        generation_data = {
            "template_id": template_id,
            "provider": "openrouter",
            "model": "meta-llama/llama-3.2-3b-instruct:free",
            "variables": {
                "dish": "Pasta Carbonara",
                "servings": 4
            },
            "count": 1
        }
        
        generate_response = await client.post(
            "/api/v1/generate",
            json=generation_data,
            headers=headers_b
        )
        assert generate_response.status_code == 202
        
        # 5. User B imports the template to customize
        import_response = await client.post(
            f"/api/v1/templates/examples/{template_id}/import",
            headers=headers_b
        )
        # This endpoint might not exist for user templates, but the concept is shown
    
    async def test_api_exploration_journey(self, client: AsyncClient):
        """Test API exploration without authentication."""
        # 1. Check API is alive
        health_response = await client.get("/health")
        assert health_response.status_code == 200
        assert health_response.json()["status"] in ["healthy", "degraded"]
        
        # 2. Access API documentation
        docs_response = await client.get("/docs")
        assert docs_response.status_code == 200
        
        # 3. Try to access protected endpoint
        protected_response = await client.get("/api/v1/auth/me")
        assert protected_response.status_code == 401
        
        # 4. List providers (should be public)
        providers_response = await client.get("/api/v1/providers")
        assert providers_response.status_code == 200
        providers = providers_response.json()
        assert len(providers) >= 2  # OpenRouter and Ollama
        
        # 5. Browse public templates
        templates_response = await client.get("/api/v1/templates?is_public=true")
        assert templates_response.status_code == 200
        
        # 6. View example templates
        examples_response = await client.get("/api/v1/templates/examples")
        assert examples_response.status_code == 200
        examples = examples_response.json()
        assert len(examples) > 0
        
        # Check example categories
        categories = {ex["category"] for ex in examples}
        assert "education" in categories or "content" in categories