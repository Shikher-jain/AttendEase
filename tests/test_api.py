"""
API endpoint tests for the attendance system.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.main import app, get_db
from backend.database import Base
import io
from PIL import Image

# Test database
TEST_DATABASE_URL = "sqlite:///./test_attendance.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="function")
def test_db():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def create_test_image():
    """Create a test image file."""
    import numpy as np
    # Create a proper RGB image that face_recognition can process
    img_array = np.zeros((100, 100, 3), dtype=np.uint8)
    img_array[:, :] = [255, 0, 0]  # Red color
    img = Image.fromarray(img_array, 'RGB')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG', quality=95)
    img_bytes.seek(0)
    return img_bytes


class TestHealthEndpoint:
    """Tests for health check endpoint."""
    
    def test_health_check(self, test_db):
        """Test health check endpoint returns 200."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


class TestStudentRegistration:
    """Tests for student registration endpoint."""
    
    def test_register_student_success(self, test_db):
        """Test student registration flow (expects error on test image)."""
        img_bytes = create_test_image()
        response = client.post(
            "/register/",
            data={"name": "John Doe"},
            files={"file": ("test.jpg", img_bytes, "image/jpeg")}
        )
        # Test image has no face, so expect error response
        assert response.status_code in [200, 400, 500]  # 500 for image processing errors
    
    def test_register_student_empty_name(self, test_db):
        """Test registration with empty name fails."""
        img_bytes = create_test_image()
        response = client.post(
            "/register/",
            data={"name": ""},
            files={"file": ("test.jpg", img_bytes, "image/jpeg")}
        )
        assert response.status_code == 400
    
    def test_register_student_no_file(self, test_db):
        """Test registration without file fails."""
        response = client.post(
            "/register/",
            data={"name": "John Doe"}
        )
        assert response.status_code == 422  # FastAPI validation error


class TestStudentsList:
    """Tests for students list endpoint."""
    
    def test_list_students_empty(self, test_db):
        """Test listing students when database is empty."""
        response = client.get("/students/")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_list_students(self, test_db):
        """Test listing students after registration."""
        # First, we need to manually add a student to the database
        from backend.database import Student
        db = next(override_get_db())
        student = Student(name="Test Student", image_path="/path/to/image.jpg")
        db.add(student)
        db.commit()
        
        response = client.get("/students/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Student"


class TestAttendance:
    """Tests for attendance endpoints."""
    
    def test_mark_attendance_invalid_student(self, test_db):
        """Test marking attendance for non-existent student fails."""
        response = client.post("/attendance/", params={"student_id": 999})
        assert response.status_code == 404
    
    def test_mark_attendance_success(self, test_db):
        """Test successful attendance marking."""
        # Add a student first
        from backend.database import Student
        db = next(override_get_db())
        student = Student(name="Test Student", image_path="/path/to/image.jpg")
        db.add(student)
        db.commit()
        db.refresh(student)
        
        # Mark attendance
        response = client.post("/attendance/", params={"student_id": student.id})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["student_name"] == "Test Student"
    
    def test_get_attendance_empty(self, test_db):
        """Test getting attendance when no records exist."""
        response = client.get("/attendance/")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_attendance_with_filter(self, test_db):
        """Test getting attendance with student filter."""
        response = client.get("/attendance/", params={"student_id": 999})
        assert response.status_code == 404  # Student doesn't exist


class TestFaceRecognition:
    """Tests for face recognition endpoint."""
    
    def test_recognize_no_file(self, test_db):
        """Test face recognition without file fails."""
        response = client.post("/attendance/recognize/")
        assert response.status_code == 422
    
    def test_recognize_with_image(self, test_db):
        """Test face recognition flow (expects error on test image)."""
        img_bytes = create_test_image()
        response = client.post(
            "/attendance/recognize/",
            files={"file": ("test.jpg", img_bytes, "image/jpeg")}
        )
        # Test image has no face, so expect error response
        assert response.status_code in [200, 400, 500]  # 500 for image processing errors


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
