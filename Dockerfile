# Multi-stage build for AttendEase Face Recognition System
FROM python:3.10-slim-bullseye as builder

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install build dependencies and system libraries in one layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build essentials for dlib compilation
    build-essential \
    cmake \
    pkg-config \
    # BLAS/LAPACK for numerical operations
    libopenblas-dev \
    liblapack-dev \
    # Boost for dlib Python bindings
    libboost-python-dev \
    libboost-all-dev \
    # X11 and GTK for OpenCV
    libx11-dev \
    libgtk-3-dev \
    # Additional OpenCV runtime dependencies
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    # Image format support
    libjpeg-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install build tools
RUN pip install --upgrade pip setuptools wheel

# Install dlib separately with system CMake (Bullseye has CMake 3.18, compatible with dlib 19.24)
# --no-build-isolation forces use of system cmake instead of pip installing cmake 4.x
RUN pip install --no-cache-dir --no-build-isolation dlib==19.24.2

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Final runtime stage
FROM python:3.10-slim-bullseye

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

WORKDIR /app

# Install only runtime dependencies (much smaller)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libopenblas0 \
    libgomp1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgl1-mesa-glx \
    libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create necessary directories and set permissions
RUN mkdir -p logs student_images /tmp/student_images && \
    chmod -R 755 logs student_images /tmp/student_images

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)" || exit 1

# Expose port
EXPOSE 8000

# Run application with proper signal handling
CMD exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT} --workers 1
