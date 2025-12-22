# Use full Python 3.10 image (not slim, for better compatibility)
FROM python:3.10

# Set working directory
WORKDIR /app

# Install system dependencies for dlib and OpenCV
RUN apt-get update && apt-get install -y \
    build-essential \
    libopenblas-dev \
    liblapack-dev \
    libx11-6 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install newer cmake
RUN pip install --upgrade pip
RUN pip install cmake>=3.18

# Install dlib first (compile from source with all dependencies available)
RUN pip install dlib==19.24.2

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
