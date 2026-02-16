# AWS SES Contact Form Handler

An AWS Lambda function for processing contact form submissions using Python 3.14 and AWS SES (Simple Email Service).

[![CI](https://github.com/chrispivonka/aws-ses-contact-form-handler/actions/workflows/ci.yml/badge.svg)](https://github.com/chrispivonka/aws-ses-contact-form-handler/actions/workflows/ci.yml)
[![Deploy](https://github.com/chrispivonka/aws-ses-contact-form-handler/actions/workflows/deploy.yml/badge.svg)](https://github.com/chrispivonka/aws-ses-contact-form-handler/actions/workflows/deploy.yml)
[![Release](https://github.com/chrispivonka/aws-ses-contact-form-handler/actions/workflows/release.yml/badge.svg)](https://github.com/chrispivonka/aws-ses-contact-form-handler/actions/workflows/release.yml)

## Setup

### Prerequisites

- Python 3.14
- Docker (for SAM local development)
- AWS CLI configured with appropriate credentials
- Make (optional but recommended)

### Installation

```bash
# Clone the repository
git clone git@github.com:chrispivonka/aws-ses-contact-form-handler.git
cd aws-ses-contact-form-handler

# Set up development environment
make install

# Optional: Set up pre-commit hooks
make setup
```

### Using Dev Container

This project includes a `.devcontainer` configuration for VS Code:

1. Open the workspace in VS Code
2. It will prompt to reopen in the dev container
3. Click "Reopen in Container"
4. Once initialized, run `make install`

## Development

### Running Tests

```bash
# Run all tests with coverage
make test

# Generate detailed coverage report
make coverage

# Run tests with specific pattern
pytest tests/test_*.py -v
```

### Code Quality

```bash
# Check code formatting
make format-check

# Auto-format code
make format

# Run linting checks
make lint

# Type checking with mypy
make type-check

# Security checks
make security
```

### Local Development

```bash
# Build SAM application
make build

# Run Lambda locally with API Gateway
make local

# Test with curl
curl -X POST http://localhost:3000/contact \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "555-123-4567",
    "message": "Hello, this is a test message"
  }'
```

## Configuration

### Environment Variables

Create a `.env` file from the example and update with your values:

```bash
cp .env.example .env
```

## API Documentation

### Request

```
POST /contact
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "555-123-4567",      # Optional
  "message": "Your message here"
}
```

### Response - Success (200)

```json
{
  "success": true,
  "message": "Thank you! Your message has been sent."
}
```

### Response - Error

```json
{
  "success": false,
  "message": "Invalid email"
}
```

**Required Secrets:**
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `SAM_S3_BUCKET`
- `RECIPIENT_EMAIL`

## Deployment

### Manual Deployment

```bash
# Deploy with guided setup
make deploy

# Deploy with parameters
sam deploy \
  --stack-name contact-form-handler \
  --s3-bucket your-sam-bucket \
  --parameter-overrides RecipientEmailParameter=admin@example.com
```

### Automatic Deployment

Merge to `main` branch - GitHub Actions will automatically run the following workflow chain:

1. **CI** - Runs in parallel on all branches:
   - Lint (YAML, JSON, black, ruff format/imports)
   - Test (pytest with 100% code coverage)
   - Code Quality (pylint 10.0/10, mypy strict mode)
   - Security (bandit, ruff security checks, CodeQL analysis)

2. **Deploy** - Only runs on main after CI passes:
   - Builds SAM application
   - Deploys Lambda functions to AWS with CloudFormation

3. **Release** - Only runs on main after Deploy passes:
   - Creates semantic version tags
   - Generates changelog
   - Creates GitHub releases

If any step fails, the pipeline stops and subsequent steps don't run.

### Manual Deployment Trigger

You can manually trigger the Deploy workflow from the GitHub Actions tab without running the full CI pipeline.

## License

MIT License - See LICENSE file for details
