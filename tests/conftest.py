"""
Shared pytest configuration and fixtures.
"""

import os
from unittest.mock import MagicMock

import pytest


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables before each test."""
    original_env = os.environ.copy()
    # Set default test environment variables
    os.environ["AWS_REGION"] = "us-east-1"
    os.environ["RECIPIENT_EMAIL"] = "test@example.com"
    os.environ["LOG_LEVEL"] = "INFO"
    yield
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_lambda_context():
    """Create a mock Lambda context for testing."""
    context = MagicMock()
    context.function_name = "contact-form-handler"
    context.function_version = "$LATEST"
    context.invoked_function_arn = (
        "arn:aws:lambda:us-east-1:123456789012:function:contact-form-handler"
    )
    context.memory_limit_in_mb = 128
    context.aws_request_id = "test-request-id-12345"
    context.get_remaining_time_in_millis = MagicMock(return_value=30000)
    return context
