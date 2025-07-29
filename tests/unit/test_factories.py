"""
Tests for factory_boy factories to ensure they generate valid data.
"""
import pytest
from tests.factories import UserFactory, TemplateFactory, GenerationFactory


@pytest.mark.unit
class TestUserFactory:
    """Test UserFactory generates valid users."""
    
    def test_create_basic_user(self):
        """Should create a basic user with all required fields."""
        user = UserFactory.build()
        
        assert user.email
        assert "@" in user.email
        assert user.full_name
        assert user.hashed_password
        assert user.is_active is True
        assert user.is_superuser is False
        assert user.created_at
        assert user.oauth_provider is None
    
    def test_create_inactive_user(self):
        """Should create inactive user with trait."""
        user = UserFactory.build(inactive=True)
        
        assert user.is_active is False
        assert user.is_superuser is False
    
    def test_create_admin_user(self):
        """Should create admin user with trait."""
        user = UserFactory.build(admin=True)
        
        assert user.is_superuser is True
        assert user.is_active is True
    
    def test_create_google_user(self):
        """Should create Google OAuth user."""
        user = UserFactory.build(google_user=True)
        
        assert user.oauth_provider == "google"
        assert user.oauth_provider_id.startswith("google-")
        assert user.is_active is True
    
    def test_create_github_user(self):
        """Should create GitHub OAuth user."""
        user = UserFactory.build(github_user=True)
        
        assert user.oauth_provider == "github"
        assert user.oauth_provider_id.startswith("github-")
        assert user.is_active is True
    
    def test_set_custom_password(self):
        """Should allow setting custom password."""
        custom_password = "CustomPassword123!"
        user = UserFactory.build(set_password=custom_password)
        
        # Verify password is hashed (not plaintext)
        assert user.hashed_password != custom_password
        assert len(user.hashed_password) > 20  # Hashed passwords are long
    
    def test_create_multiple_users_unique_emails(self):
        """Should create multiple users with unique emails."""
        users = UserFactory.build_batch(5)
        
        emails = [user.email for user in users]
        assert len(emails) == len(set(emails))  # All emails unique


@pytest.mark.unit
class TestTemplateFactory:
    """Test TemplateFactory generates valid templates."""
    
    def test_create_basic_template(self):
        """Should create a basic template with all required fields."""
        template = TemplateFactory.build()
        
        assert template.name
        assert template.description
        assert template.category in ["education", "content", "research", "business"]
        assert template.tags
        assert len(template.tags) == 3
        assert template.system_prompt
        assert template.user_prompt
        assert template.variables
        assert template.output_schema
        assert template.provider_settings
        assert template.validation_mode == "strict"
        assert template.is_public is True
    
    def test_create_private_template(self):
        """Should create private template with trait."""
        template = TemplateFactory.build(private=True)
        
        assert template.is_public is False
    
    def test_create_custom_validation_template(self):
        """Should create template with custom validation."""
        template = TemplateFactory.build(custom_validation=True)
        
        assert template.validation_mode == "custom"
        assert "min_length" in template.validation_rules
        assert "max_length" in template.validation_rules
        assert template.validation_rules["min_length"] == 10
    
    def test_create_no_validation_template(self):
        """Should create template with no validation."""
        template = TemplateFactory.build(no_validation=True)
        
        assert template.validation_mode == "none"
        assert template.validation_rules == {}
    
    def test_variables_schema_structure(self):
        """Should create valid variables schema."""
        template = TemplateFactory.build()
        
        assert "count" in template.variables
        assert "topic" in template.variables
        
        count_var = template.variables["count"]
        assert count_var["type"] == "number"
        assert "default" in count_var
        assert "min" in count_var
        assert "max" in count_var
        
        topic_var = template.variables["topic"]
        assert topic_var["type"] == "string"
        assert "default" in topic_var


@pytest.mark.unit
class TestGenerationFactory:
    """Test GenerationFactory generates valid generation records."""
    
    def test_create_basic_generation(self):
        """Should create a basic completed generation."""
        generation = GenerationFactory.build()
        
        assert generation.user
        assert generation.template
        assert generation.provider in ["openrouter", "ollama"]
        assert generation.model
        assert generation.variables_used
        assert generation.prompt_rendered
        assert generation.status == "completed"
        assert generation.result
        assert generation.error is None
        assert generation.tokens_used > 0
        assert generation.generation_time_ms > 0
        assert generation.cost > 0
        assert generation.created_at
        assert generation.completed_at
    
    def test_model_matches_provider(self):
        """Should set appropriate model for provider."""
        openrouter_gen = GenerationFactory.build(provider="openrouter")
        assert "anthropic/claude" in openrouter_gen.model or "openai/gpt" in openrouter_gen.model
        
        ollama_gen = GenerationFactory.build(provider="ollama")
        assert "llama" in ollama_gen.model or "mistral" in ollama_gen.model
    
    def test_create_failed_generation(self):
        """Should create failed generation with trait."""
        generation = GenerationFactory.build(failed=True)
        
        assert generation.status == "failed"
        assert generation.result is None
        assert generation.error
        assert "error" in generation.error.lower()
        assert generation.completed_at
    
    def test_create_pending_generation(self):
        """Should create pending generation with trait."""
        generation = GenerationFactory.build(pending=True)
        
        assert generation.status == "pending"
        assert generation.result is None
        assert generation.error is None
        assert generation.tokens_used == 0
        assert generation.generation_time_ms == 0
        assert generation.cost == 0
        assert generation.completed_at is None
    
    def test_create_processing_generation(self):
        """Should create processing generation with trait."""
        generation = GenerationFactory.build(processing=True)
        
        assert generation.status == "processing"
        assert generation.result is None
        assert generation.error is None
        assert generation.tokens_used == 0
        assert generation.generation_time_ms == 0
        assert generation.cost == 0
        assert generation.completed_at is None
    
    def test_result_structure(self):
        """Should create valid result structure."""
        generation = GenerationFactory.build()
        
        assert isinstance(generation.result, list)
        assert len(generation.result) > 0
        
        item = generation.result[0]
        assert "id" in item
        assert "content" in item
        assert item["id"].startswith("item-")
    
    def test_create_multiple_generations_unique_data(self):
        """Should create multiple generations with unique data."""
        generations = GenerationFactory.build_batch(3)
        
        # Each should have different prompt content
        prompts = [gen.prompt_rendered for gen in generations]
        assert len(set(prompts)) == len(prompts)  # All unique