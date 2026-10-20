# ==============================================================================
# OMNI SUPER PLATFORM — DOCKER PRODUCTION CONTAINER
# 24/7 Continuous Cloud Operation (Telegram Bot + Media Processing)
# ==============================================================================

FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies for media and fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    ca-certificates \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . /app/

# Ensure workspace directory exists
RUN mkdir -p /app/omnibot/temp_workspace

# Expose port for optional webhook / healthcheck
EXPOSE 8000

# Run OmniSuperBot
CMD ["python", "omnibot/bot.py"]
