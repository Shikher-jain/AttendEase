from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from .database import SessionLocal, Student, Attendance
from .logger import logger
from .config import (
    UPLOAD_DIR, ALLOWED_EXTENSIONS, MAX_FILE_SIZE, ALLOWED_ORIGINS,
    HAAR_CASCADE_PATH, FACE_DETECTION_METHOD, FACE_RECOGNITION_TOLERANCE,
    FACE_EMBEDDING_MODEL, FACE_DETECTION_CONFIDENCE,
    STORAGE_TYPE, CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET
)
import sys
import os
from pathlib import Path

# Add parent directory to path to import shared modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.face_recognition_service import FaceRecognitionService
from shared.live_video_service import LiveVideoService, LiveRecognitionSession
from shared.image_storage_service import ImageStorageService
import cv2
import numpy as np
import base64
from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel

app = FastAPI(
    title="Student Attendance System",
    description="Face recognition-based attendance system with robust error handling",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Validate Haar Cascade file exists
if not os.path.exists(HAAR_CASCADE_PATH):
    logger.error(f"Haar Cascade file not found at: {HAAR_CASCADE_PATH}")
    logger.warning("Face detection will not work without Haar Cascade file!")
else:
    logger.info(f"Haar Cascade file found at: {HAAR_CASCADE_PATH}")

# Initialize face recognition service with Mediapipe + DeepFace stack
face_service = FaceRecognitionService(
    tolerance=FACE_RECOGNITION_TOLERANCE,
    haar_cascade_path=HAAR_CASCADE_PATH,
    detection_method=FACE_DETECTION_METHOD,
    embedding_model=FACE_EMBEDDING_MODEL,
    min_detection_confidence=FACE_DETECTION_CONFIDENCE,
)
ENCODINGS_FILE = "face_encodings.pkl"

# Initialize image storage service
cloudinary_config = None
if STORAGE_TYPE == "cloudinary" and CLOUDINARY_CLOUD_NAME:
    cloudinary_config = {
        "cloud_name": CLOUDINARY_CLOUD_NAME,
        "api_key": CLOUDINARY_API_KEY,
        "api_secret": CLOUDINARY_API_SECRET
    }

image_storage = ImageStorageService(
    storage_type=STORAGE_TYPE,
    upload_dir=UPLOAD_DIR,
    cloudinary_config=cloudinary_config
)

# Initialize live video service
live_video_service = LiveVideoService(face_service)
active_sessions: Dict[str, LiveRecognitionSession] = {}

# Create necessary directories
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs("logs", exist_ok=True)

# Load existing face encodings
if os.path.exists(ENCODINGS_FILE):
    success = face_service.load_encodings(ENCODINGS_FILE)
    if success:
        logger.info(f"Loaded existing face encodings: {len(face_service.known_face_names)} faces")
        logger.info(f"Known faces: {', '.join(face_service.known_face_names)}")
    else:
        logger.error("Failed to load face encodings")
else:
    logger.warning(f"No existing face encodings file found at {ENCODINGS_FILE}")
    logger.info("Register students to create face encodings")

# Pydantic models for request/response
class LiveRegistrationRequest(BaseModel):
    name: str

class LiveAttendanceResponse(BaseModel):
    student_name: str
    confidence: float
    timestamp: str

def get_db():
    """Database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("Starting Student Attendance System API")
    logger.info(f"Upload directory: {UPLOAD_DIR}")
    logger.info(f"Encodings file: {ENCODINGS_FILE}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Student Attendance System API")

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unexpected errors."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."}
    )

@app.post("/register/")
async def register_student(
    name: str = Form(...), 
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Register a new student with their photo.
    
    Args:
        name: Student name
        file: Student photo file
        db: Database session
        
    Returns:
        Student information including ID and name
        
    Raises:
        HTTPException: If validation fails or registration errors occur
    """
    try:
        logger.info(f"Attempting to register student: {name}")
        
        # Validate name
        if not name or len(name.strip()) == 0:
            logger.warning("Registration attempt with empty name")
            raise HTTPException(status_code=400, detail="Student name cannot be empty")
        
        if len(name) > 100:
            logger.warning(f"Registration attempt with name too long: {len(name)} characters")
            raise HTTPException(status_code=400, detail="Student name too long (max 100 characters)")
        
        # Check if student already exists
        existing_student = db.query(Student).filter(Student.name == name).first()
        if existing_student:
            logger.warning(f"Student with name '{name}' already exists")
            raise HTTPException(status_code=409, detail=f"Student '{name}' already registered")
        
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            logger.warning(f"Invalid file extension: {file_ext}")
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Read file and check size
        file_content = await file.read()
        if len(file_content) > MAX_FILE_SIZE:
            logger.warning(f"File too large: {len(file_content)} bytes")
            raise HTTPException(
                status_code=413, 
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        # Save image using storage service
        image_filename = f"{name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_ext}"
        success, image_path = image_storage.save_image(file_content, name, image_filename)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save image")
        
        logger.info(f"Saved image to {image_path}")
        
        # Download image temporarily for face processing (handles both local and URL)
        temp_image_path = image_storage.download_image_temp(image_path)
        if not temp_image_path:
            image_storage.delete_image(image_path)
            raise HTTPException(status_code=500, detail="Failed to process image")
        
        # Detect and encode face using Mediapipe + optional Haar Cascade fallback
        try:
            faces = face_service.detect_faces(temp_image_path, method=FACE_DETECTION_METHOD, haar_cascade_path=HAAR_CASCADE_PATH)
            if not faces:
                image_storage.delete_image(image_path)
                if temp_image_path.startswith("/tmp") or "temp" in temp_image_path:
                    os.remove(temp_image_path)
                logger.warning(f"No face detected in uploaded image for {name}")
                raise HTTPException(status_code=400, detail="No face detected in the image")
            
            if len(faces) > 1:
                image_storage.delete_image(image_path)
                if temp_image_path.startswith("/tmp") or "temp" in temp_image_path:
                    os.remove(temp_image_path)
                logger.warning(f"Multiple faces detected in uploaded image for {name}")
                raise HTTPException(status_code=400, detail="Multiple faces detected. Please upload an image with only one face")
            
            # Add face to recognition system
            success = face_service.add_known_face(name, temp_image_path)
            if not success:
                image_storage.delete_image(image_path)
                if temp_image_path.startswith("/tmp") or "temp" in temp_image_path:
                    os.remove(temp_image_path)
                raise HTTPException(status_code=500, detail="Failed to process face encoding")
            
            # Save updated encodings
            face_service.save_encodings(ENCODINGS_FILE)
            
            # Clean up temp file if it was downloaded
            if temp_image_path != image_path and (temp_image_path.startswith("/tmp") or "temp" in temp_image_path):
                try:
                    os.remove(temp_image_path)
                except:
                    pass
            
        except HTTPException:
            raise
        except Exception as e:
            image_storage.delete_image(image_path)
            if temp_image_path and temp_image_path != image_path:
                try:
                    os.remove(temp_image_path)
                except:
                    pass
            logger.error(f"Face processing error for {name}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to process face in image")
        
        # Save to database
        try:
            student = Student(name=name, image_path=image_path)
            db.add(student)
            db.commit()
            db.refresh(student)
            logger.info(f"Successfully registered student: {name} (ID: {student.id})")
            return {
                "id": student.id, 
                "name": student.name,
                "image_path": student.image_path,
                "status": "success"
            }
        except IntegrityError as e:
            db.rollback()
            image_storage.delete_image(image_path)
            logger.error(f"Database integrity error for {name}: {str(e)}")
            raise HTTPException(status_code=409, detail="Student already registered")
        except SQLAlchemyError as e:
            db.rollback()
            image_storage.delete_image(image_path)
            logger.error(f"Database error for {name}: {str(e)}")
            raise HTTPException(status_code=500, detail="Database error occurred")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@app.get("/students/")
async def list_students(db: Session = Depends(get_db)):
    """
    Get list of all registered students.
    
    Args:
        db: Database session
        
    Returns:
        List of students with their information
    """
    try:
        logger.info("Fetching all students")
        students = db.query(Student).all()
        logger.info(f"Retrieved {len(students)} students")
        return [
            {
                "id": s.id, 
                "name": s.name, 
                "image_path": s.image_path,
                "registered_at": s.id  # Can add timestamp field to model later
            } 
            for s in students
        ]
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching students: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve students")
    except Exception as e:
        logger.error(f"Unexpected error while fetching students: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@app.post("/attendance/")
async def mark_attendance(student_id: int, db: Session = Depends(get_db)):
    """
    Mark attendance for a student.
    
    Args:
        student_id: ID of the student
        db: Database session
        
    Returns:
        Attendance record information
    """
    try:
        logger.info(f"Marking attendance for student ID: {student_id}")
        
        # Verify student exists
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            logger.warning(f"Attempted to mark attendance for non-existent student ID: {student_id}")
            raise HTTPException(status_code=404, detail=f"Student with ID {student_id} not found")
        
        # Create attendance record
        attendance = Attendance(student_id=student_id, timestamp=datetime.utcnow())
        db.add(attendance)
        db.commit()
        db.refresh(attendance)
        
        logger.info(f"Successfully marked attendance for {student.name} (ID: {student_id})")
        return {
            "status": "success",
            "attendance_id": attendance.id,
            "student_id": student_id,
            "student_name": student.name,
            "timestamp": attendance.timestamp.isoformat()
        }
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error while marking attendance: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to mark attendance")
    except Exception as e:
        logger.error(f"Unexpected error while marking attendance: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@app.post("/attendance/recognize/")
async def mark_attendance_by_face(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Mark attendance by recognizing face from uploaded image.
    
    Args:
        file: Image file containing student face
        db: Database session
        
    Returns:
        Recognition results and attendance information
    """
    temp_path = None
    try:
        logger.info("Processing face recognition for attendance")
        
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Invalid file type")
        
        # Save temporary file
        temp_path = f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_ext}"
        file_content = await file.read()
        
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large")
        
        with open(temp_path, "wb") as buffer:
            buffer.write(file_content)
        
        # Recognize faces
        results = face_service.recognize_face(temp_path)
        
        if not results:
            logger.warning("No faces detected in uploaded image")
            raise HTTPException(status_code=400, detail="No faces detected in image")
        
        # Process recognized faces
        attendance_records = []
        for result in results:
            if result["name"] != "Unknown" and result["confidence"] > 0.5:
                # Find student by name
                student = db.query(Student).filter(Student.name == result["name"]).first()
                if student:
                    # Mark attendance
                    attendance = Attendance(student_id=student.id, timestamp=datetime.utcnow())
                    db.add(attendance)
                    db.commit()
                    db.refresh(attendance)
                    
                    attendance_records.append({
                        "student_id": student.id,
                        "student_name": student.name,
                        "confidence": result["confidence"],
                        "attendance_id": attendance.id,
                        "timestamp": attendance.timestamp.isoformat()
                    })
                    logger.info(f"Marked attendance for {student.name} via face recognition (confidence: {result['confidence']:.2f})")
        
        if not attendance_records:
            logger.warning("No recognized faces matched registered students")
            return {
                "status": "no_match",
                "message": "No registered students recognized in the image",
                "detected_faces": len(results)
            }
        
        return {
            "status": "success",
            "attendance_records": attendance_records,
            "total_recognized": len(attendance_records)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error during face recognition attendance: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process face recognition")
    finally:
        # Clean up temporary file
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                logger.warning(f"Failed to remove temporary file {temp_path}: {str(e)}")

@app.get("/attendance/")
async def get_attendance(
    student_id: Optional[int] = None,
    date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get attendance records with optional filtering.
    
    Args:
        student_id: Optional student ID to filter by
        date: Optional date to filter by (YYYY-MM-DD format)
        db: Database session
        
    Returns:
        List of attendance records
    """
    try:
        logger.info(f"Fetching attendance records (student_id={student_id}, date={date})")
        
        query = db.query(Attendance)
        
        # Filter by student
        if student_id is not None:
            student = db.query(Student).filter(Student.id == student_id).first()
            if not student:
                raise HTTPException(status_code=404, detail=f"Student with ID {student_id} not found")
            query = query.filter(Attendance.student_id == student_id)
        
        # Filter by date
        if date:
            try:
                date_obj = datetime.strptime(date, "%Y-%m-%d")
                query = query.filter(
                    Attendance.timestamp >= date_obj,
                    Attendance.timestamp < date_obj.replace(hour=23, minute=59, second=59)
                )
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        records = query.all()
        
        # Get student names
        student_names = {s.id: s.name for s in db.query(Student).all()}
        
        result = [
            {
                "id": r.id, 
                "student_id": r.student_id,
                "student_name": student_names.get(r.student_id, "Unknown"),
                "timestamp": r.timestamp.isoformat()
            } 
            for r in records
        ]
        
        logger.info(f"Retrieved {len(result)} attendance records")
        return result
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching attendance: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve attendance records")
    except Exception as e:
        logger.error(f"Unexpected error while fetching attendance: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0"
    }

@app.get("/diagnostics")
async def diagnostics():
    """
    Diagnostic endpoint to check face recognition service status.
    
    Returns detailed information about:
    - Haar Cascade file status
    - Known face encodings count
    - Detection method configuration
    - Face recognition model settings
    """
    try:
        haar_cascade_exists = os.path.exists(HAAR_CASCADE_PATH) if HAAR_CASCADE_PATH else False
        haar_cascade_valid = False
        
        if haar_cascade_exists:
            try:
                test_cascade = cv2.CascadeClassifier(HAAR_CASCADE_PATH)
                haar_cascade_valid = not test_cascade.empty()
            except:
                haar_cascade_valid = False
        
        return {
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
            "face_service": {
                "detection_method": face_service.detection_method,
                "model": face_service.model,
                "tolerance": face_service.tolerance,
                "known_faces_count": len(face_service.known_face_names),
                "known_faces": face_service.known_face_names,
                "encodings_file_exists": os.path.exists(ENCODINGS_FILE)
            },
            "haar_cascade": {
                "path": HAAR_CASCADE_PATH,
                "exists": haar_cascade_exists,
                "valid": haar_cascade_valid,
                "configured_method": FACE_DETECTION_METHOD
            },
            "storage": {
                "type": STORAGE_TYPE,
                "upload_dir": UPLOAD_DIR,
                "upload_dir_exists": os.path.exists(UPLOAD_DIR)
            },
            "warnings": []
        }
    except Exception as e:
        logger.error(f"Error in diagnostics endpoint: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# ========== LIVE VIDEO ENDPOINTS ==========

@app.post("/live/camera/start")
async def start_live_camera(camera_index: int = 0):
    """
    Start the live camera for video streaming.
    
    Args:
        camera_index: Camera device index (default: 0)
        
    Returns:
        Status of camera start
    """
    try:
        logger.info(f"Starting live camera {camera_index}")
        
        if live_video_service.is_active:
            return {
                "status": "already_active",
                "message": "Camera is already active"
            }
        
        success = live_video_service.start_camera(camera_index)
        
        if success:
            logger.info("Live camera started successfully")
            return {
                "status": "success",
                "message": "Camera started successfully",
                "camera_index": camera_index
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to start camera")
    
    except Exception as e:
        logger.error(f"Error starting live camera: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start camera: {str(e)}")

@app.post("/live/camera/stop")
async def stop_live_camera():
    """Stop the live camera."""
    try:
        logger.info("Stopping live camera")
        live_video_service.stop_camera()
        
        # Clear all active sessions
        active_sessions.clear()
        
        return {
            "status": "success",
            "message": "Camera stopped successfully"
        }
    except Exception as e:
        logger.error(f"Error stopping camera: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to stop camera: {str(e)}")

@app.get("/live/camera/status")
async def get_camera_status():
    """Get the current camera status."""
    return {
        "is_active": live_video_service.is_active,
        "active_sessions": len(active_sessions)
    }

@app.get("/live/face/status")
async def get_face_detection_status():
    """
    Check if face is currently detected in the camera frame.
    Returns face detection status and count.
    """
    try:
        if not live_video_service.is_active:
            return {
                "face_detected": False,
                "face_count": 0,
                "message": "Camera is not active"
            }
        
        # Capture current frame
        frame = live_video_service.read_frame()
        if frame is None:
            return {
                "face_detected": False,
                "face_count": 0,
                "message": "No frame available"
            }
        
        face_locations = face_service.detect_faces_in_frame(frame)
        face_count = len(face_locations)
        
        return {
            "face_detected": face_count > 0,
            "face_count": face_count,
            "message": "Face detected" if face_count == 1 else f"{face_count} faces detected" if face_count > 1 else "No face detected"
        }
    except Exception as e:
        logger.error(f"Error checking face detection: {str(e)}")
        return {
            "face_detected": False,
            "face_count": 0,
            "message": f"Error: {str(e)}"
        }

@app.get("/live/video/stream")
async def live_video_stream():
    """
    Stream live video with face recognition overlay.
    Returns MJPEG stream.
    """
    try:
        if not live_video_service.is_active:
            raise HTTPException(status_code=400, detail="Camera is not active. Please start camera first.")
        
        logger.info("Starting live video stream")
        return StreamingResponse(
            live_video_service.generate_video_stream(),
            media_type="multipart/x-mixed-replace; boundary=frame"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error streaming video: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to stream video")

@app.get("/live/frame/capture")
async def capture_current_frame():
    """
    Capture and return the current frame with recognition results.
    
    Returns:
        Current frame as base64 and recognition results
    """
    try:
        if not live_video_service.is_active:
            raise HTTPException(status_code=400, detail="Camera is not active")
        
        result = live_video_service.capture_and_recognize()
        
        if result is None or not result["success"]:
            raise HTTPException(status_code=500, detail="Failed to capture frame")
        
        # Convert frame to base64
        frame_base64 = live_video_service.frame_to_base64(result["frame"])
        
        return {
            "status": "success",
            "frame": frame_base64,
            "results": result["results"],
            "face_count": result["face_count"],
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error capturing frame: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to capture frame")

@app.post("/live/register")
async def live_register_student(
    name: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Register a student using live camera capture.
    Captures a frame with a single face and registers the student.
    
    Args:
        name: Student name
        db: Database session
        
    Returns:
        Registration result
    """
    try:
        logger.info(f"Starting live registration for: {name}")
        
        # Validate name
        if not name or len(name.strip()) == 0:
            raise HTTPException(status_code=400, detail="Student name cannot be empty")
        
        if len(name) > 100:
            raise HTTPException(status_code=400, detail="Student name too long")
        
        # Check if camera is active
        if not live_video_service.is_active:
            raise HTTPException(
                status_code=400,
                detail="Camera is not active. Please start camera first using /live/camera/start"
            )
        
        # Check if student already exists
        existing = db.query(Student).filter(Student.name == name).first()
        if existing:
            raise HTTPException(status_code=409, detail=f"Student '{name}' already registered")
        
        # Capture a good frame for registration
        logger.info("Capturing frame for registration...")
        capture_result = live_video_service.capture_for_registration(max_attempts=30)
        
        if capture_result is None or not capture_result.get("success"):
            raise HTTPException(
                status_code=400,
                detail="Could not capture a suitable frame. Please ensure your face is clearly visible and you are the only person in frame."
            )
        
        # Save the captured frame using storage service
        image_filename = f"{name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        
        # Encode frame to bytes
        ret, buffer = cv2.imencode('.jpg', capture_result["frame"])
        if not ret:
            raise HTTPException(status_code=500, detail="Failed to encode image")
        
        image_bytes = buffer.tobytes()
        success, image_path = image_storage.save_image(image_bytes, name, image_filename)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save image")
        
        logger.info(f"Saved registration image to {image_path}")
        
        # Download image temporarily for face processing
        temp_image_path = image_storage.download_image_temp(image_path)
        if not temp_image_path:
            image_storage.delete_image(image_path)
            raise HTTPException(status_code=500, detail="Failed to process image")
        
        # Add face to recognition system
        success = face_service.add_known_face(name, temp_image_path)
        if not success:
            image_storage.delete_image(image_path)
            if temp_image_path != image_path:
                try:
                    os.remove(temp_image_path)
                except:
                    pass
            raise HTTPException(status_code=500, detail="Failed to process face encoding")
        
        # Save updated encodings
        face_service.save_encodings(ENCODINGS_FILE)
        
        # Clean up temp file
        if temp_image_path != image_path and (temp_image_path.startswith("/tmp") or "temp" in temp_image_path):
            try:
                os.remove(temp_image_path)
            except:
                pass
        
        # Save to database
        try:
            student = Student(name=name, image_path=image_path)
            db.add(student)
            db.commit()
            db.refresh(student)
            
            logger.info(f"Successfully registered student via live camera: {name} (ID: {student.id})")
            return {
                "status": "success",
                "id": student.id,
                "name": student.name,
                "image_path": student.image_path,
                "message": "Student registered successfully using live camera"
            }   
        except IntegrityError:
            db.rollback()
            image_storage.delete_image(image_path)
            raise HTTPException(status_code=409, detail="Student already registered")
        except SQLAlchemyError as e:
            db.rollback()
            image_storage.delete_image(image_path)
            logger.error(f"Database error: {str(e)}")
            raise HTTPException(status_code=500, detail="Database error occurred")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during live registration: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@app.post("/live/attendance/session/start")
async def start_attendance_session(session_id: str = "default"):
    """
    Start a live attendance recognition session.
    
    Args:
        session_id: Unique identifier for the session
        
    Returns:
        Session information
    """
    try:
        if not live_video_service.is_active:
            raise HTTPException(status_code=400, detail="Camera is not active")
        
        if session_id in active_sessions:
            return {
                "status": "already_active",
                "message": "Session already exists",
                "session_id": session_id
            }
        
        session = LiveRecognitionSession(live_video_service)
        active_sessions[session_id] = session
        
        logger.info(f"Started live attendance session: {session_id}")
        return {
            "status": "success",
            "session_id": session_id,
            "message": "Attendance session started"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start session")

@app.get("/live/attendance/session/status")
async def get_session_status(session_id: str = "default"):
    """
    Get the current status of an attendance session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Session status and recognized students
    """
    try:
        if session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = active_sessions[session_id]
        status = session.process_frame()
        
        return {
            "status": "success",
            "session_id": session_id,
            **status
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get session status")

@app.post("/live/attendance/session/confirm")
async def confirm_attendance_session(
    session_id: str = "default",
    min_recognitions: int = 3,
    db: Session = Depends(get_db)
):
    """
    Confirm and mark attendance for recognized students in the session.
    
    Args:
        session_id: Session identifier
        min_recognitions: Minimum number of recognitions required
        db: Database session
        
    Returns:
        Marked attendance records
    """
    try:
        if session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = active_sessions[session_id]
        confirmed_students = session.get_confirmed_students(min_recognitions)
        
        if not confirmed_students:
            return {
                "status": "no_students",
                "message": "No students with sufficient recognitions",
                "marked_attendance": []
            }
        
        marked_attendance = []
        
        for student_data in confirmed_students:
            # Find student in database
            student = db.query(Student).filter(Student.name == student_data["name"]).first()
            
            if student:
                # Mark attendance
                attendance = Attendance(student_id=student.id, timestamp=datetime.utcnow())
                db.add(attendance)
                db.commit()
                db.refresh(attendance)
                
                marked_attendance.append({
                    "student_id": student.id,
                    "student_name": student.name,
                    "confidence": student_data["confidence"],
                    "recognition_count": student_data["recognition_count"],
                    "attendance_id": attendance.id,
                    "timestamp": attendance.timestamp.isoformat()
                })
                
                logger.info(f"Marked attendance via live session for {student.name}")
        
        # Reset session after marking attendance
        session.reset()
        
        return {
            "status": "success",
            "marked_attendance": marked_attendance,
            "total_marked": len(marked_attendance)
        }
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Error confirming attendance: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to confirm attendance")

@app.post("/live/attendance/session/stop")
async def stop_attendance_session(session_id: str = "default"):
    """
    Stop and remove an attendance session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Session summary
    """
    try:
        if session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = active_sessions[session_id]
        summary = {
            "recognized_count": len(session.recognized_students),
            "recognized_students": list(session.recognized_students.values())
        }
        
        del active_sessions[session_id]
        
        logger.info(f"Stopped live attendance session: {session_id}")
        return {
            "status": "success",
            "message": "Session stopped",
            "summary": summary
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to stop session")

@app.post("/live/attendance/quick")
async def quick_live_attendance(db: Session = Depends(get_db)):
    """
    Quick live attendance marking - capture current frame and mark attendance.
    
    Args:
        db: Database session
        
    Returns:
        Marked attendance for recognized students
    """
    try:
        if not live_video_service.is_active:
            raise HTTPException(status_code=400, detail="Camera is not active")
        
        # Capture and recognize
        result = live_video_service.capture_and_recognize()
        
        if not result or not result["success"]:
            raise HTTPException(status_code=500, detail="Failed to capture frame")
        
        marked_attendance = []
        
        for face_result in result["results"]:
            name = face_result["name"]
            confidence = face_result["confidence"]
            
            if name != "Unknown" and confidence > 0.5:
                # Find student
                student = db.query(Student).filter(Student.name == name).first()
                
                if student:
                    # Mark attendance
                    attendance = Attendance(student_id=student.id, timestamp=datetime.utcnow())
                    db.add(attendance)
                    db.commit()
                    db.refresh(attendance)
                    
                    marked_attendance.append({
                        "student_id": student.id,
                        "student_name": student.name,
                        "confidence": confidence,
                        "attendance_id": attendance.id,
                        "timestamp": attendance.timestamp.isoformat()
                    })
                    
                    logger.info(f"Quick attendance marked for {student.name}")
        
        if not marked_attendance:
            return {
                "status": "no_match",
                "message": "No registered students recognized",
                "detected_faces": result["face_count"]
            }
        
        return {
            "status": "success",
            "marked_attendance": marked_attendance,
            "total_marked": len(marked_attendance)
        }
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Error in quick attendance: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to mark attendance")
