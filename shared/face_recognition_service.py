"""Face recognition helpers powered by InsightFace detection + embeddings."""

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import logging
import numpy as np
import pickle
from insightface.app import FaceAnalysis

logger = logging.getLogger("attendance_app.face_recognition")


class FaceRecognitionService:
    """Service for face detection, encoding, and recognition without dlib."""

    def __init__(
        self,
        tolerance: float = 0.75,
        haar_cascade_path: Optional[str] = None,
        detection_method: str = "insightface",
        embedding_model: str = "buffalo_l",
        det_size: Tuple[int, int] = (640, 640),
    ):
        self.tolerance = tolerance
        self.haar_cascade_path = haar_cascade_path
        self.embedding_model_name = embedding_model or "buffalo_l"
        self.det_size = det_size
        self.known_face_encodings: List[np.ndarray] = []
        self.known_face_names: List[str] = []
        self.embedding_size: Optional[int] = None

        self._haar_cascade = None
        self._insight_app: Optional[FaceAnalysis] = None
        self._load_face_analysis()

        method_aliases = {
            "auto": "insightface",
            "mediapipe": "insightface",
            "insightface": "insightface",
        }
        normalized_method = method_aliases.get(detection_method.lower(), "insightface")
        self.detection_method = normalized_method

        logger.info(
            "Initialized FaceRecognitionService (embedding=%s, tolerance=%.2f, detection=%s)",
            self.embedding_model_name,
            self.tolerance,
            self.detection_method,
        )
    
    def detect_faces(self, image_path: str, method: str = "auto", haar_cascade_path: Optional[str] = None) -> List[Tuple[int, int, int, int]]:
        """Detect faces in an image using the configured detector."""

        image_bgr = self._load_image(image_path)
        locations, _ = self._run_face_analysis(image_bgr)
        return locations
    
    def encode_face(self, image_path: str) -> Optional[np.ndarray]:
        """Generate an embedding for the first face in the supplied image."""

        if not Path(image_path).exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")

        image_bgr = cv2.imread(image_path)
        if image_bgr is None:
            raise ValueError(f"Failed to load image: {image_path}")

        face_locations, embeddings = self._run_face_analysis(image_bgr)
        if not face_locations:
            logger.warning(f"No face detected in {image_path}")
            return None

        if len(face_locations) > 1:
            logger.warning(f"Multiple faces detected in {image_path}, using first face")

        embedding = embeddings[0]
        if embedding is not None:
            logger.info(f"Successfully encoded face from {image_path}")
            if self.embedding_size is None:
                self.embedding_size = embedding.shape[0]
        return embedding
    
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

            image_bgr = cv2.imread(image_path)
            if image_bgr is None:
                raise ValueError(f"Failed to load image: {image_path}")

            face_locations, embeddings = self._run_face_analysis(image_bgr)
            if not face_locations:
                logger.warning(f"No faces detected in {image_path}")
                return []
            return self._match_embeddings(embeddings, face_locations)
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
            validated_frame = self._validate_frame(frame)
            rgb_frame = cv2.cvtColor(validated_frame, cv2.COLOR_BGR2RGB)
            if not rgb_frame.flags["C_CONTIGUOUS"]:
                rgb_frame = np.ascontiguousarray(rgb_frame)

            face_locations, embeddings = self._run_face_analysis(validated_frame)
            if not face_locations:
                logger.warning(f"No faces detected in frame using method: {self.detection_method}")
                return []
            return self._match_embeddings(embeddings, face_locations)
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
                "names": self.known_face_names,
                "embedding_model": self.embedding_model_name,
                "embedding_size": self.embedding_size,
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

            encodings = [np.array(enc, dtype=np.float32) for enc in data.get("encodings", [])]
            names = data.get("names", [])

            if encodings and data.get("embedding_size"):
                self.embedding_size = int(data["embedding_size"])

            if encodings and self.embedding_size and len(encodings[0]) != self.embedding_size:
                logger.warning("Stored encodings dimension mismatch. Please re-register students.")
                return False

            self.known_face_encodings = encodings
            self.known_face_names = names
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

    def detect_faces_in_frame(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect faces from an already captured frame."""

        try:
            validated = self._validate_frame(frame)
            locations, _ = self._run_face_analysis(validated)
            return locations
        except Exception as e:
            logger.error(f"Failed to detect faces from frame: {str(e)}")
            return []

    def _load_face_analysis(self):
        try:
            self._insight_app = FaceAnalysis(name=self.embedding_model_name)
        except Exception as exc:
            logger.warning(
                "Failed to load InsightFace pack '%s': %s. Falling back to default pack.",
                self.embedding_model_name,
                str(exc),
            )
            self._insight_app = FaceAnalysis()

        try:
            self._insight_app.prepare(ctx_id=-1, det_size=self.det_size)
        except Exception as exc:
            logger.warning(
                "InsightFace prepare failed with det_size=%s: %s. Retrying with defaults.",
                self.det_size,
                str(exc),
            )
            self._insight_app.prepare(ctx_id=-1)
        logger.info("InsightFace models loaded successfully")

    def _validate_frame(self, frame: np.ndarray) -> np.ndarray:
        if frame is None or not isinstance(frame, np.ndarray) or frame.size == 0:
            raise ValueError("Invalid frame provided")

        if len(frame.shape) != 3 or frame.shape[2] != 3:
            raise ValueError(f"Invalid frame shape: {frame.shape}")

        if frame.dtype != np.uint8:
            if frame.max() <= 1.0:
                frame = (frame * 255).astype(np.uint8)
            else:
                frame = np.clip(frame, 0, 255).astype(np.uint8)

        if not frame.flags["C_CONTIGUOUS"]:
            frame = np.ascontiguousarray(frame)

        return frame

    def _run_face_analysis(self, frame_bgr: np.ndarray) -> Tuple[List[Tuple[int, int, int, int]], List[np.ndarray]]:
        validated = self._validate_frame(frame_bgr)
        if self._insight_app is None:
            raise RuntimeError("InsightFace analysis pipeline is not initialized")

        faces = self._insight_app.get(validated)
        locations: List[Tuple[int, int, int, int]] = []
        embeddings: List[np.ndarray] = []

        for face in faces:
            x1, y1, x2, y2 = face.bbox.astype(int)
            trimmed = self._trim_bbox(validated.shape, (y1, x2, y2, x1))
            if trimmed is None:
                continue
            locations.append(trimmed)
            embeddings.append(np.array(face.embedding, dtype=np.float32))

        if self.embedding_size is None and embeddings:
            self.embedding_size = embeddings[0].shape[0]

        return locations, embeddings

    def _trim_bbox(self, shape: Tuple[int, int, int], box: Tuple[int, int, int, int]) -> Optional[Tuple[int, int, int, int]]:
        h, w = shape[0], shape[1]
        top, right, bottom, left = box

        top = max(0, min(h, top))
        bottom = max(0, min(h, bottom))
        left = max(0, min(w, left))
        right = max(0, min(w, right))

        if bottom <= top or right <= left:
            return None
        return (top, right, bottom, left)

    @staticmethod
    def _load_image(image_path: str) -> np.ndarray:
        if not Path(image_path).exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")

        image_bgr = cv2.imread(image_path)
        if image_bgr is None:
            raise ValueError(f"Failed to load image: {image_path}")
        return image_bgr

    def _match_embeddings(
        self,
        embeddings: List[Optional[np.ndarray]],
        locations: List[Tuple[int, int, int, int]],
    ) -> List[Dict[str, any]]:
        results: List[Dict[str, any]] = []

        if not embeddings:
            return results

        if not self.known_face_encodings:
            for location in locations:
                results.append({"name": "Unknown", "confidence": 0.0, "location": location})
            logger.warning("No known face encodings loaded; all matches will be Unknown")
            return results

        known_matrix = np.stack(self.known_face_encodings)

        for embedding, location in zip(embeddings, locations):
            if embedding is None:
                results.append({"name": "Unknown", "confidence": 0.0, "location": location})
                continue

            distances = np.linalg.norm(known_matrix - embedding, axis=1)
            best_index = int(np.argmin(distances))
            best_distance = float(distances[best_index])

            if best_distance <= self.tolerance:
                name = self.known_face_names[best_index]
                confidence = max(0.0, 1.0 - (best_distance / max(self.tolerance, 1e-6)))
            else:
                name = "Unknown"
                confidence = 0.0

            results.append({"name": name, "confidence": float(confidence), "location": location})

        return results

    def __del__(self):
        try:
            if self._insight_app and hasattr(self._insight_app, "release"):
                self._insight_app.release()
        except Exception:
            pass
