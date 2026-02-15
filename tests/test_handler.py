"""
Comprehensive unit tests for the Lambda handler.
Tests cover all code paths for 100% coverage.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from src.handler import (
    error_response,
    get_required_env_var,
    is_valid_email,
    is_valid_message,
    is_valid_name,
    is_valid_phone,
    lambda_handler,
    sanitize_input,
    success_response,
)


@pytest.fixture
def lambda_context():
    """Mock Lambda context."""
    context = MagicMock()
    context.function_name = "contact-form-handler"
    context.function_version = "$LATEST"
    context.invoked_function_arn = (
        "arn:aws:lambda:us-east-1:123456789012:function:contact-form-handler"
    )
    context.memory_limit_in_mb = 128
    context.aws_request_id = "test-request-id-12345"
    return context


class TestSanitizeInput:
    """Test input sanitization."""

    def test_sanitize_empty_string(self):
        """Test sanitization of empty string."""
        assert sanitize_input("") == ""

    def test_sanitize_none_value(self):
        """Test sanitization of None value."""
        assert sanitize_input(None) == ""

    def test_sanitize_html_tags(self):
        """Test removal of HTML tags."""
        input_str = "<script>alert('xss')</script>Hello"
        result = sanitize_input(input_str)
        assert "<script>" not in result
        assert "Hello" in result

    def test_sanitize_javascript_protocol(self):
        """Test removal of javascript: protocol."""
        input_str = "javascript:alert('xss')"
        result = sanitize_input(input_str)
        assert "javascript:" not in result

    def test_sanitize_event_handlers(self):
        """Test removal of event handler attributes."""
        input_str = "test onclick=alert('xss')"
        result = sanitize_input(input_str)
        assert "onclick=" not in result

    def test_sanitize_html_entities(self):
        """Test HTML entity encoding."""
        input_str = "<div onmouseover=\"alert('xss')\">test</div>"
        result = sanitize_input(input_str)
        assert "&lt;" in result
        assert "&gt;" in result
        assert "&quot;" in result

    def test_sanitize_ampersand(self):
        """Test ampersand encoding."""
        input_str = "Bread & Breakfast"
        result = sanitize_input(input_str)
        assert "&amp;" in result

    def test_sanitize_whitespace_trimming(self):
        """Test whitespace trimming."""
        input_str = "  hello world  "
        result = sanitize_input(input_str)
        assert result == "hello world"

    def test_sanitize_normal_text(self):
        """Test that normal text is preserved."""
        input_str = "John Doe"
        result = sanitize_input(input_str)
        assert result == "John Doe"


class TestGetRequiredEnvVar:
    """Test environment variable retrieval."""

    def test_get_required_env_var_success(self):
        """Test getting an existing environment variable."""
        result = get_required_env_var("AWS_REGION")
        assert result == "us-east-1"

    def test_get_required_env_var_missing(self):
        """Test getting a missing environment variable raises ValueError."""
        with pytest.raises(ValueError, match="MISSING_VAR environment variable"):
            get_required_env_var("MISSING_VAR")

    def test_get_required_env_var_empty_string(self):
        """Test that empty string env var is treated as missing."""
        import os

        os.environ["EMPTY_VAR"] = ""
        with pytest.raises(ValueError, match="EMPTY_VAR environment variable"):
            get_required_env_var("EMPTY_VAR")


class TestIsValidEmail:
    """Test email validation."""

    def test_valid_email(self):
        """Test valid email address."""
        assert is_valid_email("john@example.com") is True

    def test_valid_email_with_subdomain(self):
        """Test valid email with subdomain."""
        assert is_valid_email("john@mail.example.co.uk") is True

    def test_invalid_email_no_at_sign(self):
        """Test invalid email without @ sign."""
        assert is_valid_email("johnexample.com") is False

    def test_invalid_email_no_domain(self):
        """Test invalid email without domain."""
        assert is_valid_email("john@") is False

    def test_invalid_email_no_local_part(self):
        """Test invalid email without local part."""
        assert is_valid_email("@example.com") is False

    def test_invalid_email_no_extension(self):
        """Test invalid email without extension."""
        assert is_valid_email("john@example") is False

    def test_invalid_email_with_space(self):
        """Test invalid email with space."""
        assert is_valid_email("john @example.com") is False

    def test_invalid_email_multiple_at_signs(self):
        """Test invalid email with multiple @ signs."""
        assert is_valid_email("john@exam@ple.com") is False

    def test_invalid_email_too_long(self):
        """Test invalid email exceeding max length."""
        long_email = "a" * 255 + "@example.com"
        assert is_valid_email(long_email) is False

    def test_invalid_email_local_part_too_long(self):
        """Test invalid email with local part exceeding max length."""
        long_local = "a" * 65 + "@example.com"
        assert is_valid_email(long_local) is False

    def test_valid_email_case_insensitive(self):
        """Test that email validation is case insensitive."""
        assert is_valid_email("JOHN@EXAMPLE.COM") is True

    def test_empty_email(self):
        """Test empty email."""
        assert is_valid_email("") is False

    def test_email_with_injection_attempt(self):
        """Test email with HTML injection attempt."""
        assert is_valid_email("<script>@example.com") is False


class TestIsValidName:
    """Test name validation."""

    def test_valid_name(self):
        """Test valid name."""
        assert is_valid_name("John Doe") is True

    def test_valid_name_with_hyphen(self):
        """Test valid name with hyphen."""
        assert is_valid_name("Mary-Jane Smith") is True

    def test_valid_name_with_apostrophe(self):
        """Test valid name with apostrophe."""
        assert is_valid_name("O'Brien") is True

    def test_valid_single_word_name(self):
        """Test valid single word name."""
        assert is_valid_name("Madonna") is True

    def test_invalid_name_too_short(self):
        """Test invalid name that's too short."""
        assert is_valid_name("J") is False

    def test_invalid_name_too_long(self):
        """Test invalid name that's too long."""
        long_name = "A" * 101
        assert is_valid_name(long_name) is False

    def test_invalid_name_with_numbers(self):
        """Test invalid name with numbers."""
        assert is_valid_name("John123") is False

    def test_invalid_name_with_special_chars(self):
        """Test invalid name with special characters."""
        assert is_valid_name("John@Doe") is False

    def test_invalid_name_empty(self):
        """Test empty name."""
        assert is_valid_name("") is False

    def test_invalid_name_only_spaces(self):
        """Test name with only spaces."""
        assert is_valid_name("   ") is False

    def test_invalid_name_with_html(self):
        """Test name with HTML injection."""
        assert is_valid_name("<script>John</script>") is False


class TestIsValidPhone:
    """Test phone number validation."""

    def test_valid_phone_us_format(self):
        """Test valid US phone number."""
        assert is_valid_phone("(555) 123-4567") is True

    def test_valid_phone_international_format(self):
        """Test valid international phone number."""
        assert is_valid_phone("+1-555-123-4567") is True

    def test_valid_phone_simple_format(self):
        """Test valid simple phone number."""
        assert is_valid_phone("5551234567") is True

    def test_valid_phone_optional_empty(self):
        """Test that empty phone is valid (optional field)."""
        assert is_valid_phone("") is True

    def test_valid_phone_optional_none(self):
        """Test that None phone is valid (optional field)."""
        assert is_valid_phone(None) is True

    def test_valid_phone_spaces(self):
        """Test valid phone with spaces."""
        assert is_valid_phone("555 123 4567") is True

    def test_invalid_phone_too_few_digits(self):
        """Test invalid phone with too few digits."""
        assert is_valid_phone("12345") is False

    def test_invalid_phone_too_many_digits(self):
        """Test invalid phone with too many digits."""
        assert is_valid_phone("123456789012345678") is False

    def test_invalid_phone_with_letters(self):
        """Test invalid phone with letters."""
        assert is_valid_phone("555-CALL-NOW") is False

    def test_invalid_phone_with_special_chars(self):
        """Test invalid phone with invalid special characters."""
        assert is_valid_phone("555@123#4567") is False

    def test_valid_phone_with_extension(self):
        """Test valid phone format variations."""
        assert is_valid_phone("+44 20 7946 0958") is True


class TestIsValidMessage:
    """Test message validation."""

    def test_valid_message(self):
        """Test valid message."""
        assert is_valid_message("This is a test message") is True

    def test_valid_message_minimum_length(self):
        """Test message at minimum length (5 chars)."""
        assert is_valid_message("Hello") is True

    def test_invalid_message_too_short(self):
        """Test message that's too short."""
        assert is_valid_message("Hi") is False

    def test_invalid_message_empty(self):
        """Test empty message."""
        assert is_valid_message("") is False

    def test_valid_message_maximum_length(self):
        """Test message at maximum length."""
        long_message = "A" * 5000
        assert is_valid_message(long_message) is True

    def test_invalid_message_too_long(self):
        """Test message exceeding maximum length."""
        long_message = "A" * 5001
        assert is_valid_message(long_message) is False

    def test_valid_message_with_newlines(self):
        """Test message with newlines."""
        message = "Line 1\nLine 2\nLine 3"
        assert is_valid_message(message) is True

    def test_valid_message_with_special_chars(self):
        """Test message with special characters."""
        message = "Hello! How are you? I'm fine, thanks!"
        assert is_valid_message(message) is True

    def test_invalid_message_only_spaces(self):
        """Test message with only spaces."""
        assert is_valid_message("     ") is False


class TestErrorResponse:
    """Test error response generation."""

    def test_error_response_400(self):
        """Test error response with 400 status."""
        response = error_response(400, "Invalid input")
        assert response["statusCode"] == 400
        assert response["headers"]["Content-Type"] == "application/json"
        assert response["headers"]["Access-Control-Allow-Origin"] == "*"
        body = json.loads(response["body"])
        assert body["success"] is False
        assert body["message"] == "Invalid input"

    def test_error_response_500(self):
        """Test error response with 500 status."""
        response = error_response(500, "Server error")
        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert body["success"] is False


class TestSuccessResponse:
    """Test success response generation."""

    def test_success_response(self):
        """Test success response."""
        response = success_response("Operation successful")
        assert response["statusCode"] == 200
        assert response["headers"]["Content-Type"] == "application/json"
        assert response["headers"]["Access-Control-Allow-Origin"] == "*"
        body = json.loads(response["body"])
        assert body["success"] is True
        assert body["message"] == "Operation successful"


class TestLambdaHandler:
    """Test Lambda handler integration."""

    @patch("src.handler.SES_CLIENT")
    def test_handler_cors_preflight(self, mock_ses, lambda_context):
        """Test CORS preflight request handling."""
        event = {"httpMethod": "OPTIONS"}
        response = lambda_handler(event, lambda_context)
        assert response["statusCode"] == 200
        assert response["headers"]["Access-Control-Allow-Methods"] == "POST, OPTIONS"
        assert response["headers"]["Access-Control-Allow-Headers"] == "Content-Type"

    @patch("src.handler.SES_CLIENT")
    def test_handler_success(self, mock_ses, lambda_context):
        """Test successful form submission."""
        mock_ses.send_email.return_value = {"MessageId": "test-id"}
        event = {
            "httpMethod": "POST",
            "body": json.dumps(
                {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "phone": "555-123-4567",
                    "message": "This is a test message",
                }
            ),
        }
        response = lambda_handler(event, lambda_context)
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["success"] is True
        mock_ses.send_email.assert_called_once()

    @patch("src.handler.SES_CLIENT")
    def test_handler_success_without_phone(self, mock_ses, lambda_context):
        """Test successful submission without optional phone."""
        mock_ses.send_email.return_value = {"MessageId": "test-id"}
        event = {
            "httpMethod": "POST",
            "body": json.dumps(
                {
                    "name": "Jane Doe",
                    "email": "jane@example.com",
                    "message": "Test without phone",
                }
            ),
        }
        response = lambda_handler(event, lambda_context)
        assert response["statusCode"] == 200
        mock_ses.send_email.assert_called_once()

    @patch("src.handler.SES_CLIENT")
    def test_handler_invalid_json(self, mock_ses, lambda_context):
        """Test handler with invalid JSON."""
        event = {"httpMethod": "POST", "body": "invalid json {"}
        response = lambda_handler(event, lambda_context)
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["success"] is False
        assert "JSON" in body["message"]
        mock_ses.send_email.assert_not_called()

    @patch("src.handler.SES_CLIENT")
    def test_handler_non_dict_body(self, mock_ses, lambda_context):
        """Test handler with non-dict JSON body."""
        event = {"httpMethod": "POST", "body": json.dumps(["not", "a", "dict"])}
        response = lambda_handler(event, lambda_context)
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "JSON object" in body["message"]

    @patch("src.handler.SES_CLIENT")
    def test_handler_missing_body(self, mock_ses, lambda_context):
        """Test handler with missing body."""
        event = {"httpMethod": "POST"}
        response = lambda_handler(event, lambda_context)
        assert response["statusCode"] == 400
        mock_ses.send_email.assert_not_called()

    @patch("src.handler.SES_CLIENT")
    def test_handler_empty_body(self, mock_ses, lambda_context):
        """Test handler with empty body."""
        event = {"httpMethod": "POST", "body": json.dumps({})}
        response = lambda_handler(event, lambda_context)
        assert response["statusCode"] == 400

    @patch("src.handler.SES_CLIENT")
    def test_handler_invalid_name(self, mock_ses, lambda_context):
        """Test handler with invalid name."""
        event = {
            "httpMethod": "POST",
            "body": json.dumps(
                {"name": "J", "email": "john@example.com", "message": "Test message"}
            ),
        }
        response = lambda_handler(event, lambda_context)
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "name" in body["message"].lower()
        mock_ses.send_email.assert_not_called()

    @patch("src.handler.SES_CLIENT")
    def test_handler_invalid_email(self, mock_ses, lambda_context):
        """Test handler with invalid email."""
        event = {
            "httpMethod": "POST",
            "body": json.dumps(
                {
                    "name": "John Doe",
                    "email": "invalid-email",
                    "message": "Test message",
                }
            ),
        }
        response = lambda_handler(event, lambda_context)
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "email" in body["message"].lower()
        mock_ses.send_email.assert_not_called()

    @patch("src.handler.SES_CLIENT")
    def test_handler_invalid_phone(self, mock_ses, lambda_context):
        """Test handler with invalid phone."""
        event = {
            "httpMethod": "POST",
            "body": json.dumps(
                {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "phone": "123",
                    "message": "Test message",
                }
            ),
        }
        response = lambda_handler(event, lambda_context)
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "phone" in body["message"].lower()

    @patch("src.handler.SES_CLIENT")
    def test_handler_invalid_message(self, mock_ses, lambda_context):
        """Test handler with invalid message."""
        event = {
            "httpMethod": "POST",
            "body": json.dumps(
                {"name": "John Doe", "email": "john@example.com", "message": "Hi"}
            ),
        }
        response = lambda_handler(event, lambda_context)
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "message" in body["message"].lower()

    @patch("src.handler.SES_CLIENT")
    def test_handler_ses_message_rejected(self, mock_ses, lambda_context):
        """Test handler when SES rejects message."""
        error_response_data = {
            "Error": {
                "Code": "MessageRejected",
                "Message": "Email address not verified",
            }
        }
        mock_ses.send_email.side_effect = ClientError(error_response_data, "SendEmail")
        event = {
            "httpMethod": "POST",
            "body": json.dumps(
                {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "message": "Test message",
                }
            ),
        }
        response = lambda_handler(event, lambda_context)
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "verified" in body["message"].lower()

    @patch("src.handler.SES_CLIENT")
    def test_handler_ses_other_error(self, mock_ses, lambda_context):
        """Test handler when SES returns other error."""
        error_response_data = {
            "Error": {
                "Code": "ServiceUnavailable",
                "Message": "Service is temporarily unavailable",
            }
        }
        mock_ses.send_email.side_effect = ClientError(error_response_data, "SendEmail")
        event = {
            "httpMethod": "POST",
            "body": json.dumps(
                {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "message": "Test message",
                }
            ),
        }
        response = lambda_handler(event, lambda_context)
        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert body["success"] is False

    @patch("src.handler.SES_CLIENT")
    def test_handler_unexpected_exception(self, mock_ses, lambda_context):
        """Test handler with unexpected exception."""
        mock_ses.send_email.side_effect = Exception("Unexpected error")
        event = {
            "httpMethod": "POST",
            "body": json.dumps(
                {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "message": "Test message",
                }
            ),
        }
        response = lambda_handler(event, lambda_context)
        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert body["success"] is False
        assert "unexpected" in body["message"].lower()

    @patch("src.handler.SES_CLIENT")
    @patch("src.handler.get_required_env_var")
    def test_handler_missing_env_var(self, mock_get_env, mock_ses, lambda_context):
        """Test handler when required environment variable is missing."""
        mock_get_env.side_effect = ValueError(
            "AWS_REGION environment variable is required but not set"
        )
        event = {
            "httpMethod": "POST",
            "body": json.dumps(
                {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "message": "Test message",
                }
            ),
        }
        response = lambda_handler(event, lambda_context)
        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert body["success"] is False

    @patch("src.handler.SES_CLIENT")
    def test_handler_html_injection_in_name(self, mock_ses, lambda_context):
        """Test handler sanitizes HTML injection in name."""
        mock_ses.send_email.return_value = {"MessageId": "test-id"}
        event = {
            "httpMethod": "POST",
            "body": json.dumps(
                {
                    "name": "<script>alert('xss')</script>John",
                    "email": "john@example.com",
                    "message": "Test message",
                }
            ),
        }
        response = lambda_handler(event, lambda_context)
        assert response["statusCode"] == 200
        # Verify the call was made with sanitized data
        call_args = mock_ses.send_email.call_args
        email_body = call_args[1]["Message"]["Body"]["Text"]["Data"]
        assert "<script>" not in email_body

    @patch("src.handler.SES_CLIENT")
    def test_handler_calls_ses_with_correct_data(self, mock_ses, lambda_context):
        """Test that handler calls SES with correct data."""
        mock_ses.send_email.return_value = {"MessageId": "test-id"}
        event = {
            "httpMethod": "POST",
            "body": json.dumps(
                {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "phone": "555-1234",
                    "message": "Test message",
                }
            ),
        }
        with patch.dict("os.environ", {"RECIPIENT_EMAIL": "admin@example.com"}):
            response = lambda_handler(event, lambda_context)

        assert response["statusCode"] == 200
        # Verify SES was called with correct parameters
        mock_ses.send_email.assert_called_once()
        call_kwargs = mock_ses.send_email.call_args[1]
        assert call_kwargs["Destination"]["ToAddresses"][0] == "admin@example.com"
        assert "John Doe" in call_kwargs["Message"]["Subject"]["Data"]
        assert "john@example.com" in call_kwargs["Message"]["Body"]["Text"]["Data"]

    @patch("boto3.client")
    def test_handler_initializes_ses_client(self, mock_boto_client, lambda_context):
        """Test that handler initializes SES client when None."""
        import src.handler

        # Reset the global ses_client to None
        src.handler.SES_CLIENT = None

        mock_ses = MagicMock()
        mock_ses.send_email.return_value = {"MessageId": "test-id"}
        mock_boto_client.return_value = mock_ses

        event = {
            "httpMethod": "POST",
            "body": json.dumps(
                {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "message": "Test message for SES client init",
                }
            ),
        }
        response = lambda_handler(event, lambda_context)

        assert response["statusCode"] == 200
        # Verify boto3.client was called to create SES client
        mock_boto_client.assert_called_once_with("ses", region_name="us-east-1")
        # Verify the client was used to send email
        mock_ses.send_email.assert_called_once()
