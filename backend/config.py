"""
Configuration management for the attendance system.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load local environment variables from .env (if present).
# In production (e.g., Render), environment variables should be provided by the platform.
load_dotenv(dotenv_path=BASE_DIR / ".env", override=False)

# Database configuration
# PostgreSQL only. Prefer setting DATABASE_URL via .env (local) or platform env vars (production).
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres@localhost:5432/attendease")

# Storage configuration
STORAGE_TYPE = os.getenv("STORAGE_TYPE", "local")  # 'local' or 'cloudinary'
UPLOAD_DIR = os.getenv("UPLOAD_DIR", str(BASE_DIR / "student_images"))

# Cloudinary configuration (for cloud storage)
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")

# File upload configuration
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Face recognition configuration
FACE_RECOGNITION_TOLERANCE = float(os.getenv("FACE_RECOGNITION_TOLERANCE", "0.75"))
FACE_EMBEDDING_MODEL = os.getenv("FACE_EMBEDDING_MODEL") or os.getenv("FACE_RECOGNITION_MODEL", "mediapipe-mesh")

# Haar Cascade / detection configuration
HAAR_CASCADE_PATH = str(BASE_DIR / "haarcascade_frontalface_default.xml")
FACE_DETECTION_METHOD = os.getenv("FACE_DETECTION_METHOD", "mediapipe").lower()
if FACE_DETECTION_METHOD == "auto":
	FACE_DETECTION_METHOD = "mediapipe"
if FACE_DETECTION_METHOD not in {"mediapipe", "haar", "both"}:
	FACE_DETECTION_METHOD = "mediapipe"

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", str(BASE_DIR / "logs" / "app.log"))

# API configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# CORS configuration
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
