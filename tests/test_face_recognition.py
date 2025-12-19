"""
Tests for the face recognition service.
"""
import pytest
import sys
import os
import numpy as np
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.face_recognition_service import FaceRecognitionService


class TestFaceRecognitionService:
    """Tests for FaceRecognitionService class."""
    
    @pytest.fixture
    def service(self):
        """Create a face recognition service instance."""
        return FaceRecognitionService(model="hog", tolerance=0.6)
    
    def test_initialization(self, service):
        """Test service initialization."""
        assert service.model == "hog"
        assert service.tolerance == 0.6
        assert len(service.known_face_encodings) == 0
        assert len(service.known_face_names) == 0
    
    def test_detect_faces_invalid_path(self, service):
        """Test face detection with invalid file path."""
        with pytest.raises((FileNotFoundError, ValueError)):
            service.detect_faces("nonexistent_file.jpg")
    
    def test_encode_face_invalid_path(self, service):
        """Test face encoding with invalid file path."""
        with pytest.raises((FileNotFoundError, ValueError)):
            service.encode_face("nonexistent_file.jpg")
    
    def test_add_known_face_invalid_path(self, service):
        """Test adding known face with invalid path."""
        result = service.add_known_face("Test Person", "nonexistent_file.jpg")
        assert result == False
    
    def test_clear_known_faces(self, service):
        """Test clearing known faces."""
        # Add some dummy data
        service.known_face_encodings = [np.array([1, 2, 3])]
        service.known_face_names = ["Test"]
        
        service.clear_known_faces()
        
        assert len(service.known_face_encodings) == 0
        assert len(service.known_face_names) == 0
    
    def test_save_and_load_encodings(self, service, tmp_path):
        """Test saving and loading face encodings."""
        # Add some dummy data
        service.known_face_encodings = [np.array([1, 2, 3])]
        service.known_face_names = ["Test Person"]
        
        # Save encodings
        encodings_file = tmp_path / "test_encodings.pkl"
        result = service.save_encodings(str(encodings_file))
        assert result == True
        assert encodings_file.exists()
        
        # Create new service and load encodings
        new_service = FaceRecognitionService()
        result = new_service.load_encodings(str(encodings_file))
        assert result == True
        assert len(new_service.known_face_names) == 1
        assert new_service.known_face_names[0] == "Test Person"
    
    def test_load_encodings_nonexistent_file(self, service):
        """Test loading encodings from nonexistent file."""
        result = service.load_encodings("nonexistent_file.pkl")
        assert result == False
    
    def test_recognize_from_camera_empty_frame(self, service):
        """Test camera recognition with empty known faces."""
        # Create a dummy frame (black image)
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        results = service.recognize_from_camera(frame)
        # Should return empty list or results with "Unknown"
        assert isinstance(results, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
