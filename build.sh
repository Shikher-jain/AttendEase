#!/usr/bin/env bash
# exit on error
set -o errexit

# Install system dependencies for OpenCV / TensorFlow
echo "Installing system dependencies..."
apt-get update
apt-get install -y \
    build-essential \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgl1-mesa-glx \
    libglib2.0-0

# Upgrade pip and install newer cmake via pip (system cmake is too old)
pip install --upgrade pip
pip install cmake>=3.18

# Install remaining dependencies
echo "Installing remaining dependencies..."
pip install -r requirements.txt

# Create necessary directories
mkdir -p logs
mkdir -p /tmp/student_images

echo "Build completed successfully!"
