# Modem-Daemon Production Dockerfile
# Hardware-aware container for SIM900 modem management

FROM python:3.12-slim as builder

# Set build arguments
ARG BUILD_DATE
ARG VERSION
ARG VCS_REF

# Set labels
LABEL maintainer="GeminiVoiceConnect Team"
LABEL org.label-schema.build-date=$BUILD_DATE
LABEL org.label-schema.name="GeminiVoiceConnect Modem-Daemon"
LABEL org.label-schema.description="Revolutionary AI Call Center Agent - SIM900 Modem Management"
LABEL org.label-schema.version=$VERSION
LABEL org.label-schema.vcs-ref=$VCS_REF
LABEL org.label-schema.schema-version="1.0"

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    libasound2-dev \
    libportaudio2 \
    libportaudiocpp0 \
    portaudio19-dev \
    libffi-dev \
    libssl-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.12-slim as production

# Install runtime dependencies for hardware access
RUN apt-get update && apt-get install -y \
    libasound2 \
    libportaudio2 \
    libportaudiocpp0 \
    libffi8 \
    libssl3 \
    udev \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security (but with hardware access)
RUN groupadd -r gemini && useradd -r -g gemini -d /app -s /bin/bash gemini

# Add user to dialout group for serial port access
RUN usermod -a -G dialout gemini

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/temp /app/audio && \
    chown -R gemini:gemini /app

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONHASHSEED=random
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Audio environment variables
ENV PULSE_RUNTIME_PATH=/tmp/pulse
ENV ALSA_CARD=0

# Security hardening (while maintaining hardware access)
RUN chmod -R 755 /app && \
    chmod -R 700 /app/logs /app/data /app/temp /app/audio

# Create udev rules for modem access
RUN echo 'SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", MODE="0666", GROUP="dialout"' > /etc/udev/rules.d/99-modem.rules

# Switch to non-root user
USER gemini

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Expose port
EXPOSE 8002

# Default command
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "1"]