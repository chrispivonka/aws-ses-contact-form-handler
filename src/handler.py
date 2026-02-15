import json
import logging
import os
import re
from typing import Any

import boto3
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_required_env_var(name: str) -> str:
    """Fetch a required environment variable or raise a clear error."""
    value = os.getenv(name)
    if not value:
        raise ValueError(f"{name} environment variable is required but not set")
    return value


ses_client = None


def sanitize_input(input_str: str) -> str:
    """
    Sanitize input to prevent HTML/script injection.

    Args:
        input_str: Raw input string

    Returns:
        Sanitized string
    """
    if not input_str:
        return ""

    # Remove script blocks first to avoid leaving injected content
    sanitized = re.sub(
        r"<\s*script[^>]*>.*?<\s*/\s*script\s*>",
        "",
        input_str,
        flags=re.IGNORECASE | re.DOTALL,
    )

    # Remove script-like patterns next
    sanitized = re.sub(r"javascript:", "", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"on\w+\s*=", "", sanitized, flags=re.IGNORECASE)

    # HTML encode special characters
    sanitized = sanitized.replace("&", "&amp;")
    sanitized = sanitized.replace("<", "&lt;")
    sanitized = sanitized.replace(">", "&gt;")
    sanitized = sanitized.replace('"', "&quot;")
    return sanitized.strip()


def is_valid_email(email: str) -> bool:
    """
    Validate email format.

    Args:
        email: Email address to validate

    Returns:
        True if valid, False otherwise
    """
    email = sanitize_input(email).strip().lower()

    # Basic email regex per RFC 5322 (simplified)
    email_regex = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
    if not re.match(email_regex, email):
        return False

    # RFC 5321 length constraints
    if len(email) > 254:
        return False
    if len(email.split("@")[0]) > 64:
        return False

    if "&lt;" in email or "&gt;" in email:
        return False

    return True


def is_valid_name(name: str) -> bool:
    """
    Validate name format.

    Args:
        name: Name to validate

    Returns:
        True if valid, False otherwise
    """
    cleaned = name.strip() if name else ""

    if not cleaned or len(cleaned) < 2:
        return False
    if len(cleaned) > 100:
        return False

    # Allow letters, spaces, hyphens, apostrophes
    name_regex = r"^[a-zA-Z\s\-\']+$"
    return bool(re.match(name_regex, cleaned))


def is_valid_phone(phone: str) -> bool:
    """
    Validate phone number (optional field).

    Args:
        phone: Phone number to validate

    Returns:
        True if valid or empty, False otherwise
    """
    if not phone or phone.strip() == "":
        return True  # Optional field

    cleaned = sanitize_input(phone).strip()

    # Allow various phone formats with digits, spaces, hyphens, plus, parentheses
    phone_regex = r"^[\d\s\-\(\)\+]+$"
    if not re.match(phone_regex, cleaned):
        return False

    # Check digit count (E.164 allows 1-15 digits, with some flexibility)
    digits_only = re.sub(r"\D", "", cleaned)
    if len(digits_only) < 7 or len(digits_only) > 15:
        return False

    return True


def is_valid_message(message: str) -> bool:
    """
    Validate message length and content.

    Args:
        message: Message to validate

    Returns:
        True if valid, False otherwise
    """
    cleaned = sanitize_input(message).strip()

    if not cleaned or len(cleaned) < 5:
        return False
    if len(cleaned) > 5000:
        return False

    return True


def error_response(status_code: int, message: str) -> dict[str, Any]:
    """
    Return error response with CORS headers.

    Args:
        status_code: HTTP status code
        message: Error message

    Returns:
        HTTP response dictionary
    """
    return {
        "statusCode": status_code,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Content-Type": "application/json",
        },
        "body": json.dumps({"success": False, "message": message}),
    }


def success_response(message: str) -> dict[str, Any]:
    """
    Return success response with CORS headers.

    Args:
        message: Success message

    Returns:
        HTTP response dictionary
    """
    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Content-Type": "application/json",
        },
        "body": json.dumps({"success": True, "message": message}),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Main Lambda handler for contact form submissions.

    Args:
        event: Lambda event containing HTTP request data
        context: Lambda context object

    Returns:
        HTTP response dictionary
    """
    request_id = context.aws_request_id
    logger.info("Processing contact form request", extra={"requestId": request_id})

    # Handle CORS preflight
    if event.get("httpMethod") == "OPTIONS":
        logger.debug("Handling CORS preflight request")
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type",
            },
        }

    try:
        # Parse request body
        body_str = event.get("body", "{}")
        try:
            body = json.loads(body_str)
        except json.JSONDecodeError as e:
            logger.warning(
                "Invalid JSON in request body",
                extra={"requestId": request_id, "error": str(e)},
            )
            return error_response(400, "Invalid JSON format")

        if not isinstance(body, dict):
            logger.warning(
                "Request body is not a JSON object", extra={"requestId": request_id}
            )
            return error_response(400, "Request body must be a JSON object")

        # Extract and sanitize inputs
        name = sanitize_input(body.get("name", ""))
        email = sanitize_input(body.get("email", ""))
        phone = sanitize_input(body.get("phone", ""))
        message = sanitize_input(body.get("message", ""))

        # Validate inputs
        if not name or not is_valid_name(name):
            logger.warning(
                "Invalid name provided",
                extra={
                    "requestId": request_id,
                    "namePreview": name[:20] if name else "",
                },
            )
            return error_response(400, "Invalid name")

        if not email or not is_valid_email(email):
            logger.warning(
                "Invalid email provided",
                extra={"requestId": request_id, "email": email[:20] if email else ""},
            )
            return error_response(400, "Invalid email")

        if phone and not is_valid_phone(phone):
            logger.warning(
                "Invalid phone number provided", extra={"requestId": request_id}
            )
            return error_response(400, "Invalid phone number")

        if not message or not is_valid_message(message):
            logger.warning(
                "Invalid message provided",
                extra={
                    "requestId": request_id,
                    "messageLength": len(message) if message else 0,
                },
            )
            return error_response(400, "Invalid message (5-5000 characters)")

        logger.info(
            "Validation passed", extra={"requestId": request_id, "email": email}
        )

        aws_region = get_required_env_var("AWS_REGION")
        recipient_email = get_required_env_var("RECIPIENT_EMAIL")

        global ses_client
        if ses_client is None:
            ses_client = boto3.client("ses", region_name=aws_region)

        # Prepare email body
        email_body = f"""
Name: {name}
Email: {email}
Phone: {phone if phone else 'Not provided'}

Message:
{message}
        """

        # Send email via SES
        try:
            ses_client.send_email(
                Source=recipient_email,
                Destination={"ToAddresses": [recipient_email]},
                Message={
                    "Subject": {"Data": f"New Contact Form Submission from {name}"},
                    "Body": {"Text": {"Data": email_body}},
                },
            )
            logger.info(
                "Email sent successfully",
                extra={"requestId": request_id, "email": email},
            )
            return success_response("Thank you! Your message has been sent.")

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            logger.error(
                f"SES error: {error_code}",
                extra={
                    "requestId": request_id,
                    "error": error_code,
                    "errorMessage": e.response["Error"]["Message"],
                },
            )
            if error_code == "MessageRejected":
                return error_response(400, "Email address is not verified in SES")
            return error_response(500, "Failed to send email")

    except Exception as e:
        logger.error(
            f"Unexpected error processing request: {str(e)}",
            extra={"requestId": request_id},
            exc_info=True,
        )
        return error_response(500, "An unexpected error occurred")
