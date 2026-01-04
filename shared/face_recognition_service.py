"""DeepFace powered face recognition with Haar Cascade detection."""

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
import pickle
import logging

from deepface import DeepFace

try:
    import mediapipe as mp  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    mp = None


logger = logging.getLogger("attendance_app.face_recognition")


class FaceRecognitionService:
    """Face detection + recognition service built on OpenCV + DeepFace."""

    def __init__(
        self,
        model: str = "ArcFace",
        tolerance: float = 0.35,
        haar_cascade_path: Optional[str] = None,
        detection_method: str = "haar",
        distance_metric: str = "cosine",
    ) -> None:
        self.model = model  # Backwards compatible attribute name
        self.tolerance = tolerance  # Interpreted as maximum distance
        self.match_threshold = tolerance
        self.distance_metric = distance_metric.lower()
        self.haar_cascade_path = haar_cascade_path
        self.detection_method = detection_method.lower()
        if self.detection_method == "both":  # legacy value
            self.detection_method = "hybrid"
        if self.detection_method == "auto":
            self.detection_method = "haar"

        self.known_face_encodings: List[np.ndarray] = []
        self.known_face_names: List[str] = []

        self.haar_cascade: Optional[cv2.CascadeClassifier] = None
        self.mediapipe_detector = None
        self._initialize_detectors()

        self.embedding_model = DeepFace.build_model(self.model)
        logger.info(
            "Initialized DeepFace service | model=%s detection=%s metric=%s threshold=%.3f",
            self.model,
            self.detection_method,
            self.distance_metric,
            self.match_threshold,
        )

    # ------------------------------------------------------------------
    # Detector bootstrap
    # ------------------------------------------------------------------
    def _initialize_detectors(self) -> None:
        if self.haar_cascade_path and Path(self.haar_cascade_path).exists():
            cascade = cv2.CascadeClassifier(self.haar_cascade_path)
            if cascade.empty():
                logger.error("Haar Cascade file is invalid: %s", self.haar_cascade_path)
            else:
                self.haar_cascade = cascade
                logger.info("Haar Cascade loaded from %s", self.haar_cascade_path)
        else:
            if self.detection_method in ("haar", "hybrid"):
                logger.warning("Haar Cascade path not provided; detection may fail")

        if self.detection_method in ("mediapipe", "hybrid"):
            if mp is None:
                logger.warning("Mediapipe not installed; falling back to Haar Cascade only")
            else:
                self.mediapipe_detector = mp.solutions.face_detection.FaceDetection(
                    model_selection=0,
                    min_detection_confidence=0.6,
                )
                logger.info("MediaPipe face detector ready")

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    def detect_faces(self, image_path: str) -> List[Tuple[int, int, int, int]]:
        if not Path(image_path).exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        frame = cv2.imread(image_path)
        if frame is None:
            raise ValueError(f"Failed to load image: {image_path}")
        return self.detect_faces_in_frame(frame)

    def detect_faces_in_frame(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        processed = self._prepare_frame(frame)
        if processed is None:
            return []
        return self._detect_faces(processed)

    def encode_face(self, image_path: str) -> Optional[np.ndarray]:
        if not Path(image_path).exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        frame = cv2.imread(image_path)
        if frame is None:
            raise ValueError(f"Failed to load image: {image_path}")
        processed = self._prepare_frame(frame)
        if processed is None:
            return None

        boxes = self._detect_faces(processed)
        if not boxes:
            logger.warning("No face detected in %s", image_path)
            return None
        if len(boxes) > 1:
            logger.warning("Multiple faces detected in %s; using first", image_path)

        roi = self._crop_face(processed, boxes[0])
        return self._generate_embedding(roi)

    def add_known_face(self, name: str, image_path: str) -> bool:
        try:
            embedding = self.encode_face(image_path)
            if embedding is None:
                return False
            self.known_face_encodings.append(embedding)
            self.known_face_names.append(name)
            logger.info("Registered embedding for %s", name)
            return True
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Failed to add known face for %s: %s", name, exc)
            return False

    def recognize_face(self, image_path: str) -> List[Dict[str, object]]:
        if not Path(image_path).exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        frame = cv2.imread(image_path)
        if frame is None:
            raise ValueError(f"Failed to load image: {image_path}")
        return self._recognize_in_frame(frame)

    def recognize_from_camera(self, frame: np.ndarray) -> List[Dict[str, object]]:
        return self._recognize_in_frame(frame)

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def save_encodings(self, filepath: str) -> bool:
        try:
            data = {
                "encodings": [enc.tolist() for enc in self.known_face_encodings],
                "names": self.known_face_names,
                "metadata": {
                    "model": self.model,
                    "distance_metric": self.distance_metric,
                    "match_threshold": self.match_threshold,
                },
            }
            with open(filepath, "wb") as handle:
                pickle.dump(data, handle)
            logger.info("Saved %d embeddings to %s", len(self.known_face_names), filepath)
            return True
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Failed to save encodings: %s", exc)
            return False

    def load_encodings(self, filepath: str) -> bool:
        try:
            if not Path(filepath).exists():
                logger.warning("Encodings file not found: %s", filepath)
                return False

            with open(filepath, "rb") as handle:
                data = pickle.load(handle)

            metadata = data.get("metadata")
            if not metadata:
                logger.warning("Encodings metadata missing (legacy file); skipping load to avoid model mismatch")
                return False

            saved_model = metadata.get("model")
            if saved_model and saved_model != self.model:
                logger.warning(
                    "Encodings trained on %s but current model is %s; skipping load",
                    saved_model,
                    self.model,
                )
                return False

            self.known_face_encodings = [np.asarray(enc, dtype=np.float32) for enc in data["encodings"]]
            self.known_face_names = data["names"]
            logger.info("Loaded %d embeddings from %s", len(self.known_face_names), filepath)
            return True
        except Exception as exc:
            logger.error("Failed to load encodings: %s", exc)
            return False

    def clear_known_faces(self) -> None:
        self.known_face_encodings = []
        self.known_face_names = []
        logger.info("Cleared all stored embeddings")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _prepare_frame(self, frame: np.ndarray) -> Optional[np.ndarray]:
        if frame is None or not isinstance(frame, np.ndarray):
            return None
        if frame.ndim != 3 or frame.shape[2] != 3:
            logger.error("Frame must be BGR with 3 channels")
            return None
        if not frame.flags["C_CONTIGUOUS"]:
            frame = np.ascontiguousarray(frame)
        if frame.dtype != np.uint8:
            frame = np.clip(frame, 0, 255).astype(np.uint8)
        return frame

    def _detect_faces(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        detections: List[Tuple[int, int, int, int]] = []
        methods = self.detection_method

        if methods in ("haar", "hybrid"):
            detections.extend(self._detect_with_haar(frame))
        if methods in ("mediapipe", "hybrid"):
            detections.extend(self._detect_with_mediapipe(frame))

        if methods not in ("haar", "mediapipe", "hybrid"):
            logger.warning("Unsupported detection method %s; defaulting to Haar", methods)
            detections.extend(self._detect_with_haar(frame))

        return self._deduplicate_boxes(detections)

    def _detect_with_haar(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        if self.haar_cascade is None:
            return []
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.haar_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(70, 70))
        boxes: List[Tuple[int, int, int, int]] = []
        for (x, y, w, h) in faces:
            top = max(y, 0)
            left = max(x, 0)
            bottom = min(y + h, frame.shape[0])
            right = min(x + w, frame.shape[1])
            if bottom - top > 0 and right - left > 0:
                boxes.append((top, right, bottom, left))
        return boxes

    def _detect_with_mediapipe(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        if self.mediapipe_detector is None:
            return []
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.mediapipe_detector.process(rgb)
        boxes: List[Tuple[int, int, int, int]] = []
        if result.detections:
            h, w, _ = frame.shape
            for detection in result.detections:
                bbox = detection.location_data.relative_bounding_box
                left = max(int(bbox.xmin * w), 0)
                top = max(int(bbox.ymin * h), 0)
                right = min(int((bbox.xmin + bbox.width) * w), w)
                bottom = min(int((bbox.ymin + bbox.height) * h), h)
                if bottom - top > 0 and right - left > 0:
                    boxes.append((top, right, bottom, left))
        return boxes

    def _deduplicate_boxes(self, boxes: List[Tuple[int, int, int, int]]) -> List[Tuple[int, int, int, int]]:
        if not boxes:
            return []
        unique: List[Tuple[int, int, int, int]] = []
        for candidate in boxes:
            if not any(self._boxes_overlap(candidate, existing) for existing in unique):
                unique.append(candidate)
        return unique

    @staticmethod
    def _boxes_overlap(box_a: Tuple[int, int, int, int], box_b: Tuple[int, int, int, int], tolerance: int = 25) -> bool:
        return (
            abs(box_a[0] - box_b[0]) < tolerance
            and abs(box_a[1] - box_b[1]) < tolerance
            and abs(box_a[2] - box_b[2]) < tolerance
            and abs(box_a[3] - box_b[3]) < tolerance
        )

    def _crop_face(self, frame: np.ndarray, box: Tuple[int, int, int, int]) -> Optional[np.ndarray]:
        top, right, bottom, left = box
        top = max(0, top)
        left = max(0, left)
        bottom = min(frame.shape[0], bottom)
        right = min(frame.shape[1], right)
        if bottom - top < 40 or right - left < 40:
            logger.debug("Face bounding box too small to encode")
            return None
        roi = frame[top:bottom, left:right]
        return roi if roi.size else None

    def _generate_embedding(self, face_roi: Optional[np.ndarray]) -> Optional[np.ndarray]:
        if face_roi is None:
            return None
        try:
            representation = DeepFace.represent(
                img_path=face_roi,
                model_name=self.model,
                detector_backend="skip",
                enforce_detection=False,
                model=self.embedding_model,
            )
            if not representation:
                return None
            embedding = np.asarray(representation[0]["embedding"], dtype=np.float32)
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            return embedding
        except Exception as exc:
            logger.error("Failed to generate embedding: %s", exc)
            return None

    def _recognize_in_frame(self, frame: np.ndarray) -> List[Dict[str, object]]:
        processed = self._prepare_frame(frame)
        if processed is None:
            return []
        boxes = self._detect_faces(processed)
        if not boxes:
            logger.debug("No faces detected in frame")
            return []

        results: List[Dict[str, object]] = []
        for box in boxes:
            embedding = self._generate_embedding(self._crop_face(processed, box))
            if embedding is None:
                continue
            name, confidence, distance = self._match_embedding(embedding)
            results.append(
                {
                    "name": name,
                    "confidence": confidence,
                    "distance": distance,
                    "location": box,
                }
            )
        return results

    def _match_embedding(self, embedding: np.ndarray) -> Tuple[str, float, Optional[float]]:
        if not self.known_face_encodings:
            return "Unknown", 0.0, None

        distances = [self._compute_distance(embedding, known) for known in self.known_face_encodings]
        best_index = int(np.argmin(distances))
        best_distance = float(distances[best_index])

        if best_distance <= self.match_threshold:
            confidence = max(0.0, 1.0 - (best_distance / self.match_threshold))
            return self.known_face_names[best_index], confidence, best_distance

        return "Unknown", 0.0, best_distance

    def _compute_distance(self, a: np.ndarray, b: np.ndarray) -> float:
        if self.distance_metric == "euclidean":
            return float(np.linalg.norm(a - b))
        # Default to cosine distance
        denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-10
        similarity = float(np.dot(a, b) / denom)
        return 1.0 - similarity
