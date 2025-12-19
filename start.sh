#!/bin/bash
# Quick start script for the Student Attendance System

echo "🚀 Starting Student Attendance System..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p student_images

# Start backend in background
echo "🔨 Starting backend server..."
cd ..
uvicorn attendance_app.backend.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd attendance_app

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 5

# Start frontend
echo "🎨 Starting frontend..."
streamlit run frontend/app.py

# Cleanup on exit
trap "kill $BACKEND_PID" EXIT
