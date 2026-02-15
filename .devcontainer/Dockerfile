FROM mcr.microsoft.com/devcontainers/python:3.14

# Install AWS Lambda Runtime Interface Client
RUN pip install --upgrade pip && \
    pip install aws-lambda-runtime-interface-client

# Install development tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    zip \
    && rm -rf /var/lib/apt/lists/*

# Install AWS Lambda Runtime Emulator (SAM CLI will use this)
RUN pip install aws-sam-cli

# Install Python development tools
RUN pip install \
    black \
    pylint \
    pytest \
    pytest-cov \
    pytest-mock \
    ruff \
    mypy \
    boto3 \
    python-dotenv

USER vscode
