# Single-stage build optimized for Render's free tier memory limits
FROM python:3.10-slim-bullseye

WORKDIR /app

# Prevent interactive prompts and set memory-efficient compilation
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    MAKEFLAGS="-j1" \
    MAX_JOBS=1

# Install system dependencies in one layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    pkg-config \
    libopenblas-dev \
    liblapack-dev \
    libboost-python-dev \
    libx11-dev \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libjpeg-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Try to install pre-built dlib wheel, fallback to system-toolchain build if needed
RUN pip install --no-cache-dir --prefer-binary dlib==19.24.2 || \
    (echo "Pre-built wheel failed, compiling with system toolchain..." && \
     pip install --no-cache-dir --no-build-isolation dlib==19.24.2)

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories
RUN mkdir -p logs student_images /tmp/student_images

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)" || exit 1

EXPOSE 8000

CMD exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1
