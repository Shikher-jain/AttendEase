"""Face recognition helpers powered by Mediapipe detection and DeepFace embeddings."""

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import logging
import mediapipe as mp
import numpy as np
import pickle
from deepface import DeepFace

logger = logging.getLogger("attendance_app.face_recognition")


class FaceRecognitionService:
    """Service for face detection, encoding, and recognition without dlib."""

    def __init__(
        self,
        tolerance: float = 0.75,
        haar_cascade_path: Optional[str] = None,
        detection_method: str = "mediapipe",
        embedding_model: str = "Facenet512",
        min_detection_confidence: float = 0.6,
    ):
        self.tolerance = tolerance
        self.haar_cascade_path = haar_cascade_path
        self.embedding_model_name = embedding_model
        self.min_detection_confidence = min_detection_confidence
        self.known_face_encodings: List[np.ndarray] = []
        self.known_face_names: List[str] = []
        self.embedding_size: Optional[int] = None

        self._embedding_model = None
        self._haar_cascade = None
        self._mp_face_detection = mp.solutions.face_detection.FaceDetection(
            model_selection=0,
            min_detection_confidence=self.min_detection_confidence,
        )

        method_aliases = {
            "auto": "mediapipe",
            "mediapipe": "mediapipe",
            "haar": "haar",
            "both": "both",
        }
        normalized_method = method_aliases.get(detection_method.lower(), "mediapipe")

        self.detection_method = normalized_method
        if normalized_method in ("haar", "both"):
            self._load_haar_classifier(self.haar_cascade_path)
            if self._haar_cascade is None:
                logger.warning("Haar cascade unavailable, falling back to Mediapipe only")
                self.detection_method = "mediapipe"

        logger.info(
            "Initialized FaceRecognitionService (embedding=%s, tolerance=%.2f, detection=%s)",
            self.embedding_model_name,
            self.tolerance,
            self.detection_method,
        )
    
    def detect_faces(self, image_path: str, method: str = "auto", haar_cascade_path: Optional[str] = None) -> List[Tuple[int, int, int, int]]:
        """Detect faces in an image using Mediapipe and/or Haar cascade."""

        if not Path(image_path).exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")

        image_bgr = cv2.imread(image_path)
        if image_bgr is None:
            raise ValueError(f"Failed to load image: {image_path}")

        return self._detect_faces_from_bgr(
            image_bgr,
            method=method,
            cascade_path=haar_cascade_path,
        )
    
    def encode_face(self, image_path: str) -> Optional[np.ndarray]:
        """Generate an embedding for the first face in the supplied image."""

        if not Path(image_path).exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")

        image_bgr = cv2.imread(image_path)
        if image_bgr is None:
            raise ValueError(f"Failed to load image: {image_path}")

        face_locations = self._detect_faces_from_bgr(image_bgr)
        if not face_locations:
            logger.warning(f"No face detected in {image_path}")
            return None

        if len(face_locations) > 1:
            logger.warning(f"Multiple faces detected in {image_path}, using first face")

        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        face_patch = self._extract_face(image_rgb, face_locations[0])
        if face_patch is None:
            logger.error("Failed to crop face from image for encoding")
            return None

        embedding = self._compute_embedding(face_patch)
        if embedding is not None:
            logger.info(f"Successfully encoded face from {image_path}")
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

            face_locations = self._detect_faces_from_bgr(image_bgr)
            if not face_locations:
                logger.warning(f"No faces detected in {image_path}")
                return []

            image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
            embeddings = self._encode_faces_from_frame(image_rgb, face_locations)
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

            face_locations = self._detect_faces_from_bgr(validated_frame)
            if not face_locations:
                logger.warning(f"No faces detected in frame using method: {self.detection_method}")
                return []

            embeddings = self._encode_faces_from_frame(rgb_frame, face_locations)
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
            return self._detect_faces_from_bgr(validated)
        except Exception as e:
            logger.error(f"Failed to detect faces from frame: {str(e)}")
            return []

    def _prepare_frame_rgb(self, frame: np.ndarray) -> np.ndarray:
        validated = self._validate_frame(frame)
        rgb_frame = cv2.cvtColor(validated, cv2.COLOR_BGR2RGB)
        if not rgb_frame.flags["C_CONTIGUOUS"]:
            rgb_frame = np.ascontiguousarray(rgb_frame)
        return rgb_frame

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

    def _detect_faces_from_bgr(
        self,
        frame_bgr: np.ndarray,
        method: Optional[str] = None,
        cascade_path: Optional[str] = None,
    ) -> List[Tuple[int, int, int, int]]:
        method_aliases = {
            "auto": "mediapipe",
            "mediapipe": "mediapipe",
            "haar": "haar",
            "both": "both",
        }
        method_to_use = method_aliases.get((method or self.detection_method).lower(), "mediapipe")

        locations: List[Tuple[int, int, int, int]] = []

        if method_to_use in ("mediapipe", "both"):
            rgb_frame = self._prepare_frame_rgb(frame_bgr)
            locations.extend(self._detect_with_mediapipe(rgb_frame))

        if method_to_use in ("haar", "both"):
            cascade = self._load_haar_classifier(cascade_path)
            if cascade is not None:
                locations.extend(self._detect_with_haar(frame_bgr, cascade))

        return self._deduplicate_locations(locations)

    def _detect_with_mediapipe(self, rgb_frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        detections = self._mp_face_detection.process(rgb_frame)
        if not detections.detections:
            return []

        height, width, _ = rgb_frame.shape
        locations: List[Tuple[int, int, int, int]] = []

        for detection in detections.detections:
            bbox = detection.location_data.relative_bounding_box
            x_min = max(0.0, bbox.xmin)
            y_min = max(0.0, bbox.ymin)
            w = min(1.0, bbox.width)
            h = min(1.0, bbox.height)

            left = int(x_min * width)
            top = int(y_min * height)
            right = int(min(width, (x_min + w) * width))
            bottom = int(min(height, (y_min + h) * height))

            if right - left > 0 and bottom - top > 0:
                locations.append((top, right, bottom, left))

        return locations

    def _detect_with_haar(
        self,
        frame_bgr: np.ndarray,
        cascade: cv2.CascadeClassifier,
    ) -> List[Tuple[int, int, int, int]]:
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        locations: List[Tuple[int, int, int, int]] = []
        for (x, y, w, h) in faces:
            top, right, bottom, left = y, x + w, y + h, x
            locations.append((top, right, bottom, left))
        return locations

    def _load_haar_classifier(self, cascade_path: Optional[str]) -> Optional[cv2.CascadeClassifier]:
        target_path = cascade_path or self.haar_cascade_path
        if not target_path or not Path(target_path).exists():
            return None

        if self._haar_cascade is not None and target_path == self.haar_cascade_path:
            return self._haar_cascade

        cascade = cv2.CascadeClassifier(target_path)
        if cascade.empty():
            logger.error(f"Haar Cascade file is invalid: {target_path}")
            return None

        self._haar_cascade = cascade
        self.haar_cascade_path = target_path
        logger.info(f"Loaded Haar Cascade from {target_path}")
        return self._haar_cascade

    def _deduplicate_locations(self, locations: List[Tuple[int, int, int, int]]) -> List[Tuple[int, int, int, int]]:
        filtered: List[Tuple[int, int, int, int]] = []
        for candidate in locations:
            is_duplicate = False
            for existing in filtered:
                if self._boxes_overlap(candidate, existing):
                    is_duplicate = True
                    break
            if not is_duplicate:
                filtered.append(candidate)
        return filtered

    @staticmethod
    def _boxes_overlap(box_a: Tuple[int, int, int, int], box_b: Tuple[int, int, int, int]) -> bool:
        return (
            abs(box_a[0] - box_b[0]) < 30
            and abs(box_a[1] - box_b[1]) < 30
            and abs(box_a[2] - box_b[2]) < 30
            and abs(box_a[3] - box_b[3]) < 30
        )

    def _encode_faces_from_frame(
        self,
        frame_rgb: np.ndarray,
        face_locations: List[Tuple[int, int, int, int]],
    ) -> List[Optional[np.ndarray]]:
        embeddings: List[Optional[np.ndarray]] = []
        for location in face_locations:
            face_patch = self._extract_face(frame_rgb, location)
            if face_patch is None:
                embeddings.append(None)
                continue
            embeddings.append(self._compute_embedding(face_patch))
        return embeddings

    def _extract_face(self, frame_rgb: np.ndarray, location: Tuple[int, int, int, int]) -> Optional[np.ndarray]:
        top, right, bottom, left = location
        h, w, _ = frame_rgb.shape

        top = max(0, min(h, top))
        bottom = max(0, min(h, bottom))
        left = max(0, min(w, left))
        right = max(0, min(w, right))

        if bottom <= top or right <= left:
            return None

        face = frame_rgb[top:bottom, left:right]
        if face.size == 0:
            return None

        if not face.flags["C_CONTIGUOUS"]:
            face = np.ascontiguousarray(face)
        return face

    def _compute_embedding(self, face_rgb: np.ndarray) -> Optional[np.ndarray]:
        try:
            model = self._ensure_embedding_model()
            representations = DeepFace.represent(
                img_path=face_rgb,
                model_name=self.embedding_model_name,
                detector_backend="skip",
                enforce_detection=False,
                normalization="base",
                align=True,
                model=model,
            )

            if not representations:
                return None

            embedding = np.array(representations[0]["embedding"], dtype=np.float32)
            if self.embedding_size is None:
                self.embedding_size = embedding.shape[0]
            return embedding
        except Exception as e:
            logger.error(f"Failed to compute embedding: {str(e)}")
            return None

    def _ensure_embedding_model(self):
        if self._embedding_model is None:
            logger.info("Loading DeepFace model '%s'", self.embedding_model_name)
            self._embedding_model = DeepFace.build_model(self.embedding_model_name)
            try:
                self.embedding_size = int(self._embedding_model.outputs[0].shape[-1])
            except Exception:
                self.embedding_size = None
        return self._embedding_model

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
            if self._mp_face_detection:
                self._mp_face_detection.close()
        except Exception:
            pass
