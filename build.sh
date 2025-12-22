#!/usr/bin/env bash
# exit on error
set -o errexit

# Install system dependencies for dlib
echo "Installing system dependencies..."
apt-get update
apt-get install -y \
    build-essential \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev

# Upgrade pip and install newer cmake via pip (system cmake is too old)
pip install --upgrade pip
pip install cmake>=3.18

# Install dlib first (with specific version that has wheels)
echo "Installing dlib..."
pip install dlib==19.24.2 --verbose

# Install remaining dependencies
echo "Installing remaining dependencies..."
pip install -r requirements.txt

# Create necessary directories
mkdir -p logs
mkdir -p /tmp/student_images

echo "Build completed successfully!"
