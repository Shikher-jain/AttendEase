# Use Debian bullseye base to avoid too-new CMake (dlib 19.x fails with CMake >= 3.27)
FROM python:3.10-slim-bullseye

# Set working directory
WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive

# System dependencies (compile dlib; run opencv wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    libboost-python-dev \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1 \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install build tools
RUN pip install --upgrade pip setuptools wheel

# Install dlib separately with verbose output (helps with debugging)
RUN pip install --no-cache-dir --verbose dlib==19.24.2

# Copy requirements and install remaining dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs /tmp/student_images

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
