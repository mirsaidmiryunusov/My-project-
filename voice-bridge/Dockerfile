# Voice-Bridge Dockerfile - GPU-Accelerated Audio Processing & Advanced NLU Core
# Multi-stage build optimized for production deployment with GPU support

# Stage 1: Base image with CUDA support
FROM nvidia/cuda:12.1-devel-ubuntu22.04 as base

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV CUDA_VISIBLE_DEVICES=0

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.12 \
    python3.12-dev \
    python3.12-venv \
    python3-pip \
    build-essential \
    cmake \
    git \
    curl \
    wget \
    ffmpeg \
    libsndfile1 \
    libasound2-dev \
    portaudio19-dev \
    libportaudio2 \
    libportaudiocpp0 \
    libffi-dev \
    libssl-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Python package managers
RUN python3.12 -m pip install --upgrade pip setuptools wheel

# Stage 2: Python dependencies
FROM base as dependencies

# Create virtual environment
RUN python3.12 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements first for better caching
COPY requirements.txt /tmp/requirements.txt

# Install Python dependencies with GPU support
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
RUN pip install --no-cache-dir cupy-cuda12x
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Install additional ML and audio processing libraries
RUN pip install --no-cache-dir \
    tensorrt \
    onnxruntime-gpu \
    nvidia-ml-py3 \
    pynvml

# Download spaCy models
RUN python -m spacy download en_core_web_sm
RUN python -m spacy download es_core_news_sm || true
RUN python -m spacy download fr_core_news_sm || true
RUN python -m spacy download de_core_news_sm || true

# Stage 3: Application
FROM base as application

# Copy virtual environment from dependencies stage
COPY --from=dependencies /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create application user for security
RUN groupadd -r voicebridge && useradd -r -g voicebridge voicebridge

# Create application directories
RUN mkdir -p /app /app/logs /app/temp /app/models /app/cache
RUN chown -R voicebridge:voicebridge /app

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=voicebridge:voicebridge . /app/

# Create necessary directories with proper permissions
RUN mkdir -p /tmp/voice-bridge/audio && \
    chown -R voicebridge:voicebridge /tmp/voice-bridge

# Install additional system packages for audio processing
RUN apt-get update && apt-get install -y \
    alsa-utils \
    pulseaudio \
    && rm -rf /var/lib/apt/lists/*

# Configure audio system
RUN echo "pcm.!default { type pulse }" > /etc/asound.conf && \
    echo "ctl.!default { type pulse }" >> /etc/asound.conf

# Set up GPU access permissions
RUN usermod -a -G audio,video voicebridge

# Create startup script
RUN cat > /app/start.sh << 'EOF'
#!/bin/bash
set -e

# Check GPU availability
if command -v nvidia-smi &> /dev/null; then
    echo "GPU Status:"
    nvidia-smi --query-gpu=name,memory.total,memory.used,utilization.gpu --format=csv,noheader,nounits
else
    echo "Warning: nvidia-smi not available, GPU features may be disabled"
fi

# Check CUDA availability
python3 -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
python3 -c "import cupy; print(f'CuPy available: True')" 2>/dev/null || echo "CuPy not available"

# Start the application
exec python3 main.py
EOF

RUN chmod +x /app/start.sh && chown voicebridge:voicebridge /app/start.sh

# Health check script
RUN cat > /app/healthcheck.py << 'EOF'
#!/usr/bin/env python3
import sys
import asyncio
import aiohttp

async def health_check():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:8000/health', timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('status') in ['healthy', 'degraded']:
                        print("Health check passed")
                        return 0
                print(f"Health check failed: {response.status}")
                return 1
    except Exception as e:
        print(f"Health check error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(health_check()))
EOF

RUN chmod +x /app/healthcheck.py && chown voicebridge:voicebridge /app/healthcheck.py

# Switch to application user
USER voicebridge

# Expose ports
EXPOSE 8000 9090

# Set up environment variables
ENV PYTHONPATH=/app
ENV CUDA_CACHE_PATH=/app/cache/cuda
ENV TRANSFORMERS_CACHE=/app/cache/transformers
ENV HF_HOME=/app/cache/huggingface

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python3 /app/healthcheck.py

# Default command
CMD ["/app/start.sh"]

# Labels for metadata
LABEL maintainer="GeminiVoiceConnect Team"
LABEL version="1.0.0"
LABEL description="GPU-Accelerated Voice-Bridge for AI Call Center Agent"
LABEL gpu.required="true"
LABEL gpu.memory="2GB"
LABEL gpu.compute.capability="7.0+"