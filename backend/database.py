"""
Database models and configuration for the attendance system.
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from .config import DATABASE_URL
from .logger import logger
import datetime

try:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Verify connections before using them
        pool_size=10,  # Connection pool size
        max_overflow=20,  # Maximum overflow connections
        echo=False  # Set to True for SQL query logging
    )
    logger.info(f"Database engine created successfully: {DATABASE_URL}")
except Exception as e:
    logger.error(f"Failed to create database engine: {str(e)}")
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Student(Base):
    """Student model for storing student information."""
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    image_path = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationship to attendance records
    attendances = relationship("Attendance", back_populates="student")
    
    def __repr__(self):
        return f"<Student(id={self.id}, name='{self.name}')>"


class Attendance(Base):
    """Attendance model for storing attendance records."""
    __tablename__ = "attendance"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    
    # Relationship to student
    student = relationship("Student", back_populates="attendances")
    
    def __repr__(self):
        return f"<Attendance(id={self.id}, student_id={self.student_id}, timestamp={self.timestamp})>"


def init_db():
    """Initialize the database by creating all tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {str(e)}")
        raise


# Create tables on import
init_db()
