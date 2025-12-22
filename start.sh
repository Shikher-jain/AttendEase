#!/bin/bash
# Quick start script for AttendEase Student Attendance System

echo "========================================"
echo "  AttendEase - Student Attendance System"
echo "========================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "[1/6] 📦 Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ ERROR: Failed to create virtual environment"
        exit 1
    fi
    echo "✅ Virtual environment created successfully!"
else
    echo "[1/6] ✓ Virtual environment found"
fi
echo ""

# Activate virtual environment
echo "[2/6] 🔧 Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "❌ ERROR: Failed to activate virtual environment"
    exit 1
fi
echo ""

# Install/Update dependencies
echo "[3/6] 📥 Installing/Updating dependencies..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
if [ $? -ne 0 ]; then
    echo "❌ ERROR: Failed to install dependencies"
    exit 1
fi
echo "✅ Dependencies installed successfully!"
echo ""

# Create necessary directories
echo "[4/6] 📁 Creating necessary directories..."
mkdir -p logs
mkdir -p student_images
mkdir -p backend/__pycache__
mkdir -p shared/__pycache__
echo "✅ Directories ready!"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  WARNING: .env file not found!"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "Please configure .env file if needed"
    echo ""
fi

# Start backend in background
echo "[5/6] 🔨 Starting backend server..."
echo "Backend will run on http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo ""

# Wait for backend to start
echo "⏳ Waiting for backend to initialize..."
sleep 5
echo ""

# Choose frontend
echo "[6/6] 🎨 Starting frontend..."
echo "Frontend will open at http://localhost:8501"
echo ""
echo "========================================"
echo "  Both services are starting..."
echo "  Press Ctrl+C to stop both servers"
echo "========================================"
echo ""

# Ask which frontend to start
echo "Choose frontend:"
echo "1) Standard Frontend"
echo "2) Live Recognition Frontend"
read -p "Enter choice [1-2]: " choice

case $choice in
    2)
        streamlit run frontend/app_live.py
        ;;
    *)
        streamlit run frontend/app.py
        ;;
esac

# Cleanup on exit
trap "kill $BACKEND_PID" EXIT
