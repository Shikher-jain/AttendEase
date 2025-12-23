"""
Live video streaming and face recognition service.
Handles real-time video processing for attendance and registration.
"""
import cv2
import numpy as np
from typing import Generator, Optional, Dict, List
import logging
from datetime import datetime
import base64

logger = logging.getLogger("attendance_app.live_video")


class LiveVideoService:
    """Service for live video streaming and real-time face recognition."""
    
    def __init__(self, face_service):
        """
        Initialize live video service.
        
        Args:
            face_service: FaceRecognitionService instance for recognition
        """
        self.face_service = face_service
        self.camera = None
        self.is_active = False
        logger.info("Initialized LiveVideoService")
    
    def start_camera(self, camera_index: int = 0) -> bool:
        """
        Start the camera for live video.
        
        Args:
            camera_index: Camera device index (default: 0)
            
        Returns:
            True if camera started successfully, False otherwise
        """
        try:
            self.camera = cv2.VideoCapture(camera_index)
            
            if not self.camera.isOpened():
                logger.error(f"Failed to open camera {camera_index}")
                return False
            
            # Set camera properties for better performance
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            # Ensure camera outputs 8-bit BGR format
            self.camera.set(cv2.CAP_PROP_FORMAT, -1)  # Auto format
            self.camera.set(cv2.CAP_PROP_CONVERT_RGB, 0)  # Keep as BGR
            
            # Test read a frame to verify camera works
            ret, test_frame = self.camera.read()
            if not ret or test_frame is None:
                logger.error("Camera opened but cannot read frames")
                self.camera.release()
                return False
            
            logger.info(f"Camera test frame: shape={test_frame.shape}, dtype={test_frame.dtype}")
            
            self.is_active = True
            logger.info(f"Camera {camera_index} started successfully")
            return True
        except Exception as e:
            logger.error(f"Error starting camera: {str(e)}")
            return False
    
    def stop_camera(self):
        """Stop the camera and release resources."""
        if self.camera is not None:
            self.camera.release()
            self.camera = None
            self.is_active = False
            logger.info("Camera stopped")
    
    def read_frame(self) -> Optional[np.ndarray]:
        """
        Read a single frame from the camera.
        
        Returns:
            Frame as numpy array, or None if failed
        """
        if self.camera is None or not self.is_active:
            return None
        
        ret, frame = self.camera.read()
        if not ret or frame is None:
            logger.warning("Failed to read frame from camera")
            return None
        
        # Validate frame is numpy array
        if not isinstance(frame, np.ndarray):
            logger.error("Frame is not a numpy array")
            return None
        
        # Ensure frame has 3 channels (BGR)
        if len(frame.shape) != 3 or frame.shape[2] != 3:
            logger.error(f"Invalid frame shape: {frame.shape}, expected (H, W, 3)")
            return None
        
        # Ensure frame is contiguous in memory
        if not frame.flags['C_CONTIGUOUS']:
            frame = np.ascontiguousarray(frame)
        
        # Ensure frame is in correct format (8-bit BGR)
        if frame.dtype != np.uint8:
            logger.warning(f"Frame dtype is {frame.dtype}, converting to uint8")
            # Normalize to 0-255 range if needed
            if frame.max() <= 1.0:
                frame = (frame * 255).astype(np.uint8)
            else:
                frame = np.clip(frame, 0, 255).astype(np.uint8)
        
        # Final validation
        if frame.dtype != np.uint8:
            logger.error(f"Failed to convert frame to uint8, dtype is {frame.dtype}")
            return None
        
        # Ensure values are in valid range
        if frame.min() < 0 or frame.max() > 255:
            logger.warning(f"Frame values out of range: min={frame.min()}, max={frame.max()}, clipping...")
            frame = np.clip(frame, 0, 255).astype(np.uint8)
        
        return frame
    
    def process_frame_for_recognition(self, frame: np.ndarray, draw_boxes: bool = True) -> Dict:
        """
        Process a frame for face recognition.
        
        Args:
            frame: Video frame as numpy array
            draw_boxes: Whether to draw bounding boxes on faces
            
        Returns:
            Dictionary with recognition results and processed frame
        """
        try:
            # Recognize faces in the frame
            results = self.face_service.recognize_from_camera(frame)
            
            # Draw bounding boxes and labels if requested
            if draw_boxes:
                for result in results:
                    top, right, bottom, left = result["location"]
                    name = result["name"]
                    confidence = result["confidence"]
                    
                    # Choose color based on recognition
                    if name == "Unknown":
                        color = (0, 0, 255)  # Red for unknown
                    else:
                        color = (0, 255, 0)  # Green for recognized
                    
                    # Draw rectangle around face
                    cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                    
                    # Draw label background
                    cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
                    
                    # Draw text
                    font = cv2.FONT_HERSHEY_DUPLEX
                    label = f"{name}"
                    if name != "Unknown":
                        label += f" ({confidence:.2f})"
                    cv2.putText(frame, label, (left + 6, bottom - 6), font, 0.5, (255, 255, 255), 1)
            
            return {
                "success": True,
                "frame": frame,
                "results": results,
                "face_count": len(results)
            }
        except Exception as e:
            logger.error(f"Error processing frame: {str(e)}")
            return {
                "success": False,
                "frame": frame,
                "results": [],
                "face_count": 0,
                "error": str(e)
            }
    
    def generate_video_stream(self) -> Generator[bytes, None, None]:
        """
        Generate video stream for web streaming (MJPEG format).
        
        Yields:
            JPEG frame bytes in multipart format
        """
        while self.is_active:
            frame = self.read_frame()
            if frame is None:
                break
            
            # Process frame for recognition
            processed = self.process_frame_for_recognition(frame)
            
            if processed["success"]:
                # Encode frame as JPEG
                ret, buffer = cv2.imencode('.jpg', processed["frame"])
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    
    def capture_and_recognize(self) -> Optional[Dict]:
        """
        Capture a frame and perform recognition.
        
        Returns:
            Recognition results or None if failed
        """
        frame = self.read_frame()
        if frame is None:
            return None
        
        return self.process_frame_for_recognition(frame)
    
    def capture_for_registration(self, max_attempts: int = 30) -> Optional[Dict]:
        """
        Capture a good quality frame for registration.
        Waits for a clear, single face.
        
        Args:
            max_attempts: Maximum frames to check
            
        Returns:
            Dictionary with frame and face location, or None
        """
        for attempt in range(max_attempts):
            frame = self.read_frame()
            if frame is None:
                continue
            
            # Detect faces
            try:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                import face_recognition
                face_locations = face_recognition.face_locations(rgb_frame)
                
                # We want exactly one face
                if len(face_locations) == 1:
                    logger.info(f"Good registration frame captured on attempt {attempt + 1}")
                    return {
                        "success": True,
                        "frame": frame,
                        "face_location": face_locations[0],
                        "message": "Single face detected"
                    }
            except Exception as e:
                logger.error(f"Error detecting face: {str(e)}")
                continue
        
        logger.warning("Failed to capture good registration frame")
        return None
    
    def frame_to_base64(self, frame: np.ndarray) -> str:
        """
        Convert frame to base64 string for transmission.
        
        Args:
            frame: Video frame as numpy array
            
        Returns:
            Base64 encoded string
        """
        ret, buffer = cv2.imencode('.jpg', frame)
        if ret:
            jpg_as_text = base64.b64encode(buffer).decode('utf-8')
            return jpg_as_text
        return ""
    
    def __del__(self):
        """Cleanup on deletion."""
        self.stop_camera()


class LiveRecognitionSession:
    """Manages a live recognition session for attendance marking."""
    
    def __init__(self, video_service: LiveVideoService, min_confidence: float = 0.6):
        """
        Initialize a live recognition session.
        
        Args:
            video_service: LiveVideoService instance
            min_confidence: Minimum confidence for recognition
        """
        self.video_service = video_service
        self.min_confidence = min_confidence
        self.recognized_students: Dict[str, Dict] = {}
        self.session_start = datetime.now()
        logger.info("Started live recognition session")
    
    def process_frame(self) -> Dict:
        """
        Process a frame and track recognized students.
        
        Returns:
            Session status and recognized students
        """
        result = self.video_service.capture_and_recognize()
        
        if result and result["success"]:
            for face_result in result["results"]:
                name = face_result["name"]
                confidence = face_result["confidence"]
                
                if name != "Unknown" and confidence >= self.min_confidence:
                    # Add or update recognized student
                    if name not in self.recognized_students:
                        self.recognized_students[name] = {
                            "name": name,
                            "first_seen": datetime.now(),
                            "confidence": confidence,
                            "recognition_count": 1
                        }
                    else:
                        # Update recognition
                        self.recognized_students[name]["recognition_count"] += 1
                        # Update confidence to average
                        old_conf = self.recognized_students[name]["confidence"]
                        count = self.recognized_students[name]["recognition_count"]
                        self.recognized_students[name]["confidence"] = (old_conf * (count - 1) + confidence) / count
        
        return {
            "recognized_count": len(self.recognized_students),
            "recognized_students": list(self.recognized_students.values()),
            "session_duration": (datetime.now() - self.session_start).total_seconds()
        }
    
    def get_confirmed_students(self, min_recognitions: int = 3) -> List[Dict]:
        """
        Get students with confirmed recognition.
        
        Args:
            min_recognitions: Minimum number of recognitions required
            
        Returns:
            List of confirmed students
        """
        confirmed = [
            student for student in self.recognized_students.values()
            if student["recognition_count"] >= min_recognitions
        ]
        return confirmed
    
    def reset(self):
        """Reset the session."""
        self.recognized_students.clear()
        self.session_start = datetime.now()
        logger.info("Recognition session reset")
