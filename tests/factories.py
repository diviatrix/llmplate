"""
Test factories using factory_boy for generating test data.
"""
from datetime import datetime
from typing import Optional

import factory
from factory import fuzzy
from faker import Faker

from app.models.user import User
from app.models.template import Template
from app.models.generation import Generation, GenerationStatus
from app.auth.password import get_password_hash

fake = Faker()


class UserFactory(factory.Factory):
    """Factory for creating test users."""
    
    class Meta:
        model = User
    
    email = factory.LazyAttribute(lambda _: fake.unique.email())
    full_name = factory.LazyAttribute(lambda _: fake.name())
    hashed_password = factory.LazyAttribute(lambda _: get_password_hash("TestPassword123!"))
    is_active = True
    is_superuser = False
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)
    oauth_provider = None
    oauth_provider_id = None
    
    @factory.post_generation
    def set_password(obj, create, extracted, **kwargs):
        """Allow setting custom password after generation."""
        if extracted:
            obj.hashed_password = get_password_hash(extracted)
    
    class Params:
        # Traits for common variations
        inactive = factory.Trait(is_active=False)
        admin = factory.Trait(is_superuser=True)
        google_user = factory.Trait(
            oauth_provider="google",
            oauth_provider_id=factory.LazyAttribute(lambda _: f"google-{fake.uuid4()}")
        )
        github_user = factory.Trait(
            oauth_provider="github",
            oauth_provider_id=factory.LazyAttribute(lambda _: f"github-{fake.random_int(10000, 99999)}")
        )


class TemplateFactory(factory.Factory):
    """Factory for creating test templates."""
    
    class Meta:
        model = Template
    
    name = factory.LazyAttribute(lambda _: fake.catch_phrase())
    description = factory.LazyAttribute(lambda _: fake.text(max_nb_chars=200))
    category = fuzzy.FuzzyChoice(["education", "content", "research", "business"])
    tags = factory.LazyAttribute(lambda _: fake.words(nb=3))
    
    # Template structure
    system_prompt = factory.LazyAttribute(lambda _: f"You are a helpful assistant for {fake.job()}.")
    user_prompt = "Generate {count} items about {topic}."
    
    # Variables schema
    variables = factory.LazyAttribute(lambda _: {
        "count": {
            "type": "number",
            "description": "Number of items to generate",
            "default": 5,
            "min": 1,
            "max": 20
        },
        "topic": {
            "type": "string",
            "description": "Topic for generation",
            "default": fake.word()
        }
    })
    
    # Output schema
    output_schema = factory.LazyAttribute(lambda _: {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["id", "content"]
        }
    })
    
    # Provider settings
    provider_settings = {
        "recommended_provider": "openrouter",
        "recommended_model": "anthropic/claude-3-sonnet",
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    # Validation settings
    validation_mode = "strict"
    validation_rules = {}
    
    # Metadata
    is_public = True
    created_by = factory.SubFactory(UserFactory)
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)
    
    class Params:
        # Trait for private template
        private = factory.Trait(is_public=False)
        
        # Trait for custom validation
        custom_validation = factory.Trait(
            validation_mode="custom",
            validation_rules={
                "min_length": 10,
                "max_length": 1000,
                "required_fields": ["content"]
            }
        )
        
        # Trait for no validation
        no_validation = factory.Trait(
            validation_mode="none",
            validation_rules={}
        )


class GenerationFactory(factory.Factory):
    """Factory for creating test generation records."""
    
    class Meta:
        model = Generation
    
    # Job information
    job_id = factory.LazyAttribute(lambda _: f"gen_{fake.uuid4()[:8]}")
    user = factory.SubFactory(UserFactory)
    template = factory.SubFactory(TemplateFactory)
    
    # For direct access
    user_id = factory.LazyAttribute(lambda obj: str(obj.user.id) if hasattr(obj.user, 'id') else fake.uuid4())
    template_id = factory.LazyAttribute(lambda obj: str(obj.template.id) if hasattr(obj.template, 'id') else fake.uuid4())
    
    # Generation configuration
    provider = fuzzy.FuzzyChoice(["openrouter", "ollama"])
    model = factory.LazyAttribute(lambda obj: 
        "anthropic/claude-3.5-sonnet" if obj.provider == "openrouter" 
        else "llama3:latest"
    )
    variables = {"count": 5, "topic": "AI trends"}
    count = 5
    
    # Status tracking
    status = factory.LazyAttribute(lambda _: GenerationStatus.COMPLETED)
    progress = 100
    error_message = None
    
    # Results
    results = factory.LazyAttribute(lambda _: [
        {"id": f"item-{i}", "content": fake.sentence()}
        for i in range(5)
    ])
    prompt_rendered = factory.LazyAttribute(lambda obj: f"Generate {obj.variables['count']} items about {obj.variables['topic']}.")
    
    # Cost tracking
    total_tokens = fuzzy.FuzzyInteger(100, 1000)
    prompt_tokens = fuzzy.FuzzyInteger(50, 200)
    completion_tokens = factory.LazyAttribute(lambda obj: obj.total_tokens - obj.prompt_tokens)
    cost = factory.LazyAttribute(lambda obj: obj.total_tokens * 0.00001)
    
    # Timestamps
    created_at = factory.LazyFunction(datetime.utcnow)
    started_at = factory.LazyFunction(datetime.utcnow)
    completed_at = factory.LazyFunction(datetime.utcnow)
    
    # Metadata
    metadata = {}
    
    class Params:
        # Trait for failed generation
        failed = factory.Trait(
            status=factory.LazyAttribute(lambda _: GenerationStatus.FAILED),
            progress=0,
            results=[],
            error_message="Model API error: Rate limit exceeded",
            completed_at=factory.LazyFunction(datetime.utcnow)
        )
        
        # Trait for pending generation
        pending = factory.Trait(
            status=factory.LazyAttribute(lambda _: GenerationStatus.PENDING),
            progress=0,
            results=[],
            error_message=None,
            total_tokens=0,
            prompt_tokens=0,
            completion_tokens=0,
            cost=0,
            started_at=None,
            completed_at=None
        )
        
        # Trait for processing generation
        processing = factory.Trait(
            status=factory.LazyAttribute(lambda _: GenerationStatus.PROCESSING),
            progress=50,
            results=[],
            error_message=None,
            total_tokens=0,
            prompt_tokens=0,
            completion_tokens=0,
            cost=0,
            started_at=factory.LazyFunction(datetime.utcnow),
            completed_at=None
        )
        
        # Trait for cancelled generation
        cancelled = factory.Trait(
            status=factory.LazyAttribute(lambda _: GenerationStatus.CANCELLED),
            progress=25,
            results=[],
            error_message="Cancelled by user",
            completed_at=factory.LazyFunction(datetime.utcnow)
        )