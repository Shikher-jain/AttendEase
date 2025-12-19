"""
Configuration management for the attendance system.
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./attendance.db")

# Upload configuration
UPLOAD_DIR = os.getenv("UPLOAD_DIR", str(BASE_DIR / "student_images"))
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Face recognition configuration
FACE_RECOGNITION_MODEL = "hog"  # 'hog' or 'cnn'
FACE_RECOGNITION_TOLERANCE = 0.6  # Lower is more strict
MIN_FACE_SIZE = (30, 30)  # Minimum face size for detection

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", str(BASE_DIR / "logs" / "app.log"))

# API configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# CORS configuration
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
