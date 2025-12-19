"""
Tests for database models and operations.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database import Base, Student, Attendance

# Test database
TEST_DATABASE_URL = "sqlite:///./test_db.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


class TestStudentModel:
    """Tests for Student model."""
    
    def test_create_student(self, db_session):
        """Test creating a student."""
        student = Student(name="John Doe", image_path="/path/to/image.jpg")
        db_session.add(student)
        db_session.commit()
        
        assert student.id is not None
        assert student.name == "John Doe"
        assert student.image_path == "/path/to/image.jpg"
        assert student.created_at is not None
    
    def test_student_unique_name(self, db_session):
        """Test that student names must be unique."""
        student1 = Student(name="John Doe", image_path="/path1.jpg")
        student2 = Student(name="John Doe", image_path="/path2.jpg")
        
        db_session.add(student1)
        db_session.commit()
        
        db_session.add(student2)
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()
    
    def test_query_student_by_name(self, db_session):
        """Test querying student by name."""
        student = Student(name="Jane Doe", image_path="/path.jpg")
        db_session.add(student)
        db_session.commit()
        
        found = db_session.query(Student).filter(Student.name == "Jane Doe").first()
        assert found is not None
        assert found.name == "Jane Doe"
    
    def test_student_repr(self, db_session):
        """Test student string representation."""
        student = Student(name="Test Student", image_path="/path.jpg")
        db_session.add(student)
        db_session.commit()
        
        repr_str = repr(student)
        assert "Student" in repr_str
        assert "Test Student" in repr_str


class TestAttendanceModel:
    """Tests for Attendance model."""
    
    def test_create_attendance(self, db_session):
        """Test creating an attendance record."""
        # First create a student
        student = Student(name="John Doe", image_path="/path.jpg")
        db_session.add(student)
        db_session.commit()
        
        # Create attendance
        attendance = Attendance(student_id=student.id)
        db_session.add(attendance)
        db_session.commit()
        
        assert attendance.id is not None
        assert attendance.student_id == student.id
        assert attendance.timestamp is not None
    
    def test_attendance_relationship(self, db_session):
        """Test attendance-student relationship."""
        # Create student
        student = Student(name="John Doe", image_path="/path.jpg")
        db_session.add(student)
        db_session.commit()
        
        # Create attendance
        attendance = Attendance(student_id=student.id)
        db_session.add(attendance)
        db_session.commit()
        
        # Test relationship
        assert attendance.student.name == "John Doe"
        assert len(student.attendances) == 1
        assert student.attendances[0].id == attendance.id
    
    def test_query_attendance_by_student(self, db_session):
        """Test querying attendance records for a student."""
        # Create student
        student = Student(name="John Doe", image_path="/path.jpg")
        db_session.add(student)
        db_session.commit()
        
        # Create multiple attendance records
        for _ in range(3):
            attendance = Attendance(student_id=student.id)
            db_session.add(attendance)
        db_session.commit()
        
        # Query
        records = db_session.query(Attendance).filter(Attendance.student_id == student.id).all()
        assert len(records) == 3
    
    def test_attendance_repr(self, db_session):
        """Test attendance string representation."""
        student = Student(name="Test Student", image_path="/path.jpg")
        db_session.add(student)
        db_session.commit()
        
        attendance = Attendance(student_id=student.id)
        db_session.add(attendance)
        db_session.commit()
        
        repr_str = repr(attendance)
        assert "Attendance" in repr_str
        assert str(student.id) in repr_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
