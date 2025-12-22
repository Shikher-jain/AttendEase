"""
Face recognition service using face_recognition library and OpenCV.
"""
import face_recognition
import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional, Dict
import pickle
import logging

logger = logging.getLogger("attendance_app.face_recognition")


class FaceRecognitionService:
    """Service for face detection, encoding, and recognition."""
    
    def __init__(self, model: str = "hog", tolerance: float = 0.6, haar_cascade_path: Optional[str] = None, detection_method: str = "auto"):
        """
        Initialize the face recognition service.
        
        Args:
            model: Face detection model ('hog' or 'cnn')
            tolerance: Face matching tolerance (lower is more strict)
            haar_cascade_path: Path to Haar Cascade XML file for face detection
            detection_method: Detection method ('auto', 'haar', or 'both')
        """
        self.model = model
        self.tolerance = tolerance
        self.haar_cascade_path = haar_cascade_path
        self.detection_method = detection_method
        self.known_face_encodings: List[np.ndarray] = []
        self.known_face_names: List[str] = []
        logger.info(f"Initialized FaceRecognitionService with model={model}, tolerance={tolerance}, detection_method={detection_method}, haar_cascade={haar_cascade_path}")
    
    def detect_faces(self, image_path: str, method: str = "auto", haar_cascade_path: Optional[str] = None) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces in an image using either face_recognition or Haar cascade.
        
        Args:
            image_path: Path to the image file
            method: 'auto' (default, use face_recognition), 'haar' (use Haar cascade), or 'both' (return union of both)
            haar_cascade_path: Path to Haar cascade XML file (required if method is 'haar' or 'both')
        Returns:
            List of face locations as (top, right, bottom, left) tuples
        Raises:
            FileNotFoundError: If image file doesn't exist
            ValueError: If image cannot be loaded
        """
        try:
            if not Path(image_path).exists():
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            results = []
            used_methods = []
            # face_recognition method
            if method in ("auto", "both"):
                image = face_recognition.load_image_file(image_path)
                fr_locations = face_recognition.face_locations(image, model=self.model)
                results.extend(fr_locations)
                used_methods.append("face_recognition")
            # Haar cascade method
            if method in ("haar", "both"):
                if not haar_cascade_path or not Path(haar_cascade_path).exists():
                    raise ValueError("Valid haar_cascade_path must be provided for Haar cascade detection.")
                image_bgr = cv2.imread(image_path)
                if image_bgr is None:
                    raise ValueError(f"Failed to load image: {image_path}")
                gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
                face_cascade = cv2.CascadeClassifier(haar_cascade_path)
                haar_faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
                # Convert (x, y, w, h) to (top, right, bottom, left)
                for (x, y, w, h) in haar_faces:
                    top, right, bottom, left = y, x + w, y + h, x
                    results.append((top, right, bottom, left))
                used_methods.append("haar_cascade")
            logger.info(f"Detected {len(results)} face(s) in {image_path} using {', '.join(used_methods)}")
            return results
        except Exception as e:
            logger.error(f"Error detecting faces in {image_path}: {str(e)}")
            raise ValueError(f"Failed to detect faces: {str(e)}")
    
    def encode_face(self, image_path: str) -> Optional[np.ndarray]:
        """
        Generate face encoding from an image.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Face encoding as numpy array, or None if no face detected
            
        Raises:
            ValueError: If image processing fails
        """
        try:
            if not Path(image_path).exists():
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            # Load image using OpenCV first (handles BGR correctly)
            image_bgr = cv2.imread(image_path)
            if image_bgr is None:
                raise ValueError(f"Failed to load image: {image_path}")
            
            # Convert BGR to RGB for face_recognition library
            image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
            
            # Encode faces
            face_encodings = face_recognition.face_encodings(image_rgb, model=self.model)
            
            if not face_encodings:
                logger.warning(f"No face detected in {image_path}")
                return None
            
            if len(face_encodings) > 1:
                logger.warning(f"Multiple faces detected in {image_path}, using first face")
            
            logger.info(f"Successfully encoded face from {image_path}")
            return face_encodings[0]
        except Exception as e:
            logger.error(f"Error encoding face from {image_path}: {str(e)}")
            raise ValueError(f"Failed to encode face: {str(e)}")
    
    def add_known_face(self, name: str, image_path: str) -> bool:
        """
        Add a known face to the recognition system.
        
        Args:
            name: Name of the person
            image_path: Path to their image
            
        Returns:
            True if successfully added, False otherwise
        """
        try:
            encoding = self.encode_face(image_path)
            if encoding is None:
                return False
            
            self.known_face_encodings.append(encoding)
            self.known_face_names.append(name)
            logger.info(f"Added known face for {name} from {image_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to add known face for {name}: {str(e)}")
            return False
    
    def recognize_face(self, image_path: str) -> List[Dict[str, any]]:
        """
        Recognize faces in an image.
        
        Args:
            image_path: Path to the image to recognize
            
        Returns:
            List of dictionaries with 'name', 'confidence', and 'location' for each face
        """
        try:
            if not Path(image_path).exists():
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            image = face_recognition.load_image_file(image_path)
            face_locations = face_recognition.face_locations(image, model=self.model)
            face_encodings = face_recognition.face_encodings(image, face_locations)
            
            results = []
            for face_encoding, face_location in zip(face_encodings, face_locations):
                matches = face_recognition.compare_faces(
                    self.known_face_encodings, 
                    face_encoding, 
                    tolerance=self.tolerance
                )
                face_distances = face_recognition.face_distance(
                    self.known_face_encodings, 
                    face_encoding
                )
                
                name = "Unknown"
                confidence = 0.0
                
                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        name = self.known_face_names[best_match_index]
                        confidence = 1.0 - face_distances[best_match_index]
                
                results.append({
                    "name": name,
                    "confidence": float(confidence),
                    "location": face_location
                })
                
                logger.info(f"Recognized face: {name} with confidence {confidence:.2f}")
            
            return results
        except Exception as e:
            logger.error(f"Error recognizing faces in {image_path}: {str(e)}")
            raise ValueError(f"Failed to recognize faces: {str(e)}")
    
    def recognize_from_camera(self, frame: np.ndarray) -> List[Dict[str, any]]:
        """
        Recognize faces from a camera frame using configured detection method.
        
        Args:
            frame: OpenCV BGR image frame
            
        Returns:
            List of dictionaries with 'name', 'confidence', and 'location' for each face
        """
        try:
            # Validate frame
            if frame is None or frame.size == 0:
                logger.error("Invalid frame: None or empty")
                return []
            
            # Ensure frame is a numpy array
            if not isinstance(frame, np.ndarray):
                logger.error("Frame is not a numpy array")
                return []
            
            # Make a copy to avoid modifying original frame
            frame = frame.copy()
            
            # Ensure frame has correct shape (height, width, 3)
            if len(frame.shape) != 3 or frame.shape[2] != 3:
                logger.error(f"Invalid frame shape: {frame.shape}, expected (H, W, 3)")
                return []
            
            # Ensure frame is contiguous in memory
            if not frame.flags['C_CONTIGUOUS']:
                frame = np.ascontiguousarray(frame)
            
            # Ensure frame is uint8 (must be done BEFORE cvtColor)
            if frame.dtype != np.uint8:
                logger.warning(f"Frame dtype is {frame.dtype}, converting to uint8")
                # Normalize to 0-255 range if needed
                if frame.max() <= 1.0:
                    frame = (frame * 255).astype(np.uint8)
                else:
                    frame = np.clip(frame, 0, 255).astype(np.uint8)
            
            # Convert BGR to RGB for face_recognition library
            try:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            except cv2.error as e:
                logger.error(f"cvtColor failed: {str(e)}, frame shape: {frame.shape}, dtype: {frame.dtype}")
                return []
            
            # Final validation of RGB frame
            if rgb_frame.dtype != np.uint8:
                logger.error(f"RGB frame dtype is {rgb_frame.dtype}, should be uint8")
                return []
            
            if not rgb_frame.flags['C_CONTIGUOUS']:
                rgb_frame = np.ascontiguousarray(rgb_frame)
            
            # Find faces using configured detection method
            face_locations = []
            
            # Use face_recognition library for detection (default/auto)
            if self.detection_method in ("auto", "both"):
                try:
                    face_locations = face_recognition.face_locations(rgb_frame, model=self.model)
                except Exception as e:
                    logger.error(f"face_recognition.face_locations failed: {str(e)}")
                    logger.debug(f"Frame details: shape={rgb_frame.shape}, dtype={rgb_frame.dtype}, contiguous={rgb_frame.flags['C_CONTIGUOUS']}")
                    # Fall back to Haar Cascade if available
                    if self.detection_method == "both" and self.haar_cascade_path:
                        logger.info("Falling back to Haar Cascade only")
                    elif self.detection_method == "auto":
                        return []
            
            # Add Haar Cascade detection if configured
            if self.detection_method in ("haar", "both") and self.haar_cascade_path:
                try:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    face_cascade = cv2.CascadeClassifier(self.haar_cascade_path)
                    haar_faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
                    
                    # Convert (x, y, w, h) to (top, right, bottom, left) and add to face_locations
                    for (x, y, w, h) in haar_faces:
                        top, right, bottom, left = y, x + w, y + h, x
                        haar_location = (top, right, bottom, left)
                        
                        # Check if this location overlaps with existing detections (avoid duplicates)
                        is_duplicate = False
                        for existing_loc in face_locations:
                            # Simple overlap check
                            if (abs(existing_loc[0] - top) < 30 and 
                                abs(existing_loc[1] - right) < 30 and
                                abs(existing_loc[2] - bottom) < 30 and
                                abs(existing_loc[3] - left) < 30):
                                is_duplicate = True
                                break
                        
                        if not is_duplicate:
                            face_locations.append(haar_location)
                except Exception as e:
                    logger.error(f"Haar Cascade detection failed: {str(e)}")
            
            # If no faces detected, return early
            if not face_locations:
                return []
            
            # Encode detected faces
            try:
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            except Exception as e:
                logger.error(f"face_recognition.face_encodings failed: {str(e)}")
                logger.debug(f"Frame details: shape={rgb_frame.shape}, dtype={rgb_frame.dtype}")
                return []
            
            results = []
            for face_encoding, face_location in zip(face_encodings, face_locations):
                matches = face_recognition.compare_faces(
                    self.known_face_encodings, 
                    face_encoding, 
                    tolerance=self.tolerance
                )
                face_distances = face_recognition.face_distance(
                    self.known_face_encodings, 
                    face_encoding
                )
                
                name = "Unknown"
                confidence = 0.0
                
                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        name = self.known_face_names[best_match_index]
                        confidence = 1.0 - face_distances[best_match_index]
                
                results.append({
                    "name": name,
                    "confidence": float(confidence),
                    "location": face_location
                })
            
            return results
        except Exception as e:
            logger.error(f"Error recognizing faces from camera: {str(e)}")
            return []
    
    def save_encodings(self, filepath: str) -> bool:
        """
        Save known face encodings to a file.
        
        Args:
            filepath: Path to save the encodings
            
        Returns:
            True if successful, False otherwise
        """
        try:
            data = {
                "encodings": self.known_face_encodings,
                "names": self.known_face_names
            }
            with open(filepath, "wb") as f:
                pickle.dump(data, f)
            logger.info(f"Saved {len(self.known_face_names)} face encodings to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save encodings: {str(e)}")
            return False
    
    def load_encodings(self, filepath: str) -> bool:
        """
        Load known face encodings from a file.
        
        Args:
            filepath: Path to load the encodings from
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not Path(filepath).exists():
                logger.warning(f"Encodings file not found: {filepath}")
                return False
            
            with open(filepath, "rb") as f:
                data = pickle.load(f)
            
            self.known_face_encodings = data["encodings"]
            self.known_face_names = data["names"]
            logger.info(f"Loaded {len(self.known_face_names)} face encodings from {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to load encodings: {str(e)}")
            return False
    
    def clear_known_faces(self):
        """Clear all known face encodings."""
        self.known_face_encodings = []
        self.known_face_names = []
        logger.info("Cleared all known face encodings")
