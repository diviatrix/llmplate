#!/bin/bash

# Run tests with coverage
echo "Running tests with coverage..."
python -m pytest tests/unit/test_health.py -v --cov=app --cov-report=term-missing

# Check if tests passed
if [ $? -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Tests failed!"
    exit 1
fi