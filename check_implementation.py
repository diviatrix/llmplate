#!/usr/bin/env python3
"""Quick check of implementation without running full tests."""
import sys

try:
    # Test imports
    from app.models.generation import Generation, GenerationStatus
    print("✓ Generation model imports successfully")
    
    from app.generation.service import generation_service
    print("✓ Generation service imports successfully")
    
    from app.api.generation import router
    print("✓ Generation API router imports successfully")
    
    from tests.factories import GenerationFactory
    print("✓ GenerationFactory imports successfully")
    
    # Check model structure
    gen = Generation(
        job_id="test_123",
        user_id="user_456",
        template_id="tmpl_789",
        provider="openrouter",
        model="test-model",
        status=GenerationStatus.PENDING
    )
    print("✓ Generation model instantiates correctly")
    
    # Check enums
    print(f"✓ GenerationStatus values: {[s.value for s in GenerationStatus]}")
    
    print("\n✅ All imports and basic checks passed!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    sys.exit(1)