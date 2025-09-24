# Use official Python 3.12 slim image based on Debian Bookworm
FROM python:3.12.11-slim-bookworm

# Install UV (ultra-fast Python package installer) from Astral.sh
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Disable creation of .pyc/.pyo files
ENV PYTHONDONTWRITEBYTECODE=1
# Ensure Python output is sent straight to terminal without buffering
ENV PYTHONUNBUFFERED=1

# ======================
# SYSTEM DEPENDENCIES
# ======================
# Install required system packages:
# - curl: for downloading files
# - gettext: for Django translation utilities  
# - ffmpeg: for audio/video processing (needed for ElevenLabs)
RUN apt-get update &&     apt-get install -y --no-install-recommends     curl     gettext     ffmpeg &&     rm -rf /var/lib/apt/lists/*

# Set working directory inside container
WORKDIR /app

# ======================
# DEPENDENCY INSTALLATION
# ======================
# Copy dependency specification files first for better layer caching
COPY pyproject.toml ./

# Install Python dependencies using UV:
# --locked: ensures exact versions from lockfile are used
ENV UV_HTTP_TIMEOUT=300
RUN uv sync --no-dev

# ======================
# ElevenLabs Configuration
# ======================
# No need to download models - ElevenLabs is cloud-based

# ======================
# APPLICATION CODE
# ======================
# Copy the rest of the application code
# Note: This is done after dependency installation for better caching
COPY . .

# Making the file executable
RUN chmod +x entrypoint.sh

# ======================
# RUNTIME CONFIGURATION
# ======================
# Expose the port Django runs on
EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
