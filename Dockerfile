FROM python:3.9.16-slim-bullseye

LABEL maintainer="JKirkcaldy"
LABEL support="https://github.com/jkirkcaldy/plex-utills"
LABEL discord="https://discord.gg/z3FYhHwHMw"

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ARG TZ=Europe/London
ENV TZ="${TZ}"

# Install system dependencies
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        wget \
        git \
        nginx \
        ffmpeg \
        libsm6 \
        libxext6 \
        nano \
        curl \
        mediainfo \
        && \
    # Clean up
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and set up startup script
COPY ./start.sh .
RUN chmod +x start.sh

# Copy nginx configuration
COPY app/static/dockerfiles/default /etc/nginx/sites-enabled/default
RUN rm -f /etc/nginx/sites-enabled/default.bak

# Copy requirements first for better layer caching
COPY ./requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install git+https://github.com/AnthonyBloomer/tmdbv3api.git

# Copy application files
COPY ./app ./app
COPY ./main.py .
COPY ./version .

# Create necessary directories
RUN mkdir -p /config /logs /films && \
    # Create nginx run directory
    mkdir -p /var/run/nginx && \
    # Set permissions
    chown -R www-data:www-data /var/log/nginx /var/lib/nginx /var/run/nginx

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Expose ports
EXPOSE 80 5000

# Volumes
VOLUME ["/films", "/config", "/logs"]

# Start command
CMD ["/app/start.sh"]
