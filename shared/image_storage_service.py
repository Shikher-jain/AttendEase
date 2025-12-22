"""
Image storage service supporting both local filesystem and Cloudinary cloud storage.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Tuple
import io

logger = logging.getLogger("attendance_app.storage")

# Try to import cloudinary
try:
    import cloudinary
    import cloudinary.uploader
    import cloudinary.api
    from PIL import Image
    CLOUDINARY_AVAILABLE = True
except ImportError:
    CLOUDINARY_AVAILABLE = False
    logger.warning("Cloudinary not available. Using local storage only.")


class ImageStorageService:
    """Service for storing and retrieving images (local or cloud)."""
    
    def __init__(self, storage_type: str = "local", upload_dir: str = "student_images", 
                 cloudinary_config: Optional[dict] = None):
        """
        Initialize the image storage service.
        
        Args:
            storage_type: 'local' or 'cloudinary'
            upload_dir: Local directory for file storage (fallback for cloudinary too)
            cloudinary_config: Dict with cloud_name, api_key, api_secret
        """
        self.storage_type = storage_type.lower()
        self.upload_dir = upload_dir
        
        # Ensure local directory exists
        os.makedirs(upload_dir, exist_ok=True)
        
        # Configure Cloudinary if using cloud storage
        if self.storage_type == "cloudinary":
            if not CLOUDINARY_AVAILABLE:
                logger.error("Cloudinary requested but not installed. Falling back to local storage.")
                self.storage_type = "local"
            elif cloudinary_config:
                cloudinary.config(
                    cloud_name=cloudinary_config.get("cloud_name"),
                    api_key=cloudinary_config.get("api_key"),
                    api_secret=cloudinary_config.get("api_secret"),
                    secure=True
                )
                logger.info("Cloudinary configured successfully")
            else:
                logger.warning("Cloudinary config missing. Falling back to local storage.")
                self.storage_type = "local"
        
        logger.info(f"Image storage initialized: {self.storage_type}")
    
    def save_image(self, file_content: bytes, student_name: str, filename: str) -> Tuple[bool, str]:
        """
        Save an image to storage.
        
        Args:
            file_content: Image file bytes
            student_name: Student name (for folder/tag)
            filename: Original filename
            
        Returns:
            Tuple of (success: bool, path_or_url: str)
        """
        try:
            if self.storage_type == "cloudinary":
                return self._save_to_cloudinary(file_content, student_name, filename)
            else:
                return self._save_to_local(file_content, student_name, filename)
        except Exception as e:
            logger.error(f"Error saving image: {str(e)}")
            # Fallback to local storage
            if self.storage_type == "cloudinary":
                logger.info("Cloudinary failed, falling back to local storage")
                return self._save_to_local(file_content, student_name, filename)
            return False, ""
    
    def _save_to_local(self, file_content: bytes, student_name: str, filename: str) -> Tuple[bool, str]:
        """Save image to local filesystem."""
        try:
            student_dir = os.path.join(self.upload_dir, student_name.replace(" ", "_"))
            os.makedirs(student_dir, exist_ok=True)
            
            file_path = os.path.join(student_dir, filename)
            
            with open(file_path, "wb") as f:
                f.write(file_content)
            
            logger.info(f"Saved image locally: {file_path}")
            return True, file_path
        except Exception as e:
            logger.error(f"Error saving to local storage: {str(e)}")
            return False, ""
    
    def _save_to_cloudinary(self, file_content: bytes, student_name: str, filename: str) -> Tuple[bool, str]:
        """Save image to Cloudinary."""
        try:
            # Upload to cloudinary with student name as folder and tag
            upload_result = cloudinary.uploader.upload(
                file_content,
                folder=f"attendease/{student_name.replace(' ', '_')}",
                public_id=Path(filename).stem,
                tags=[student_name, "attendance"],
                overwrite=True,
                resource_type="image"
            )
            
            url = upload_result.get("secure_url")
            logger.info(f"Saved image to Cloudinary: {url}")
            
            # Also save locally as cache/backup
            self._save_to_local(file_content, student_name, filename)
            
            return True, url
        except Exception as e:
            logger.error(f"Error saving to Cloudinary: {str(e)}")
            return False, ""
    
    def get_image_path(self, image_ref: str) -> str:
        """
        Get the image path/URL.
        
        Args:
            image_ref: Local path or Cloudinary URL
            
        Returns:
            Image path or URL
        """
        return image_ref
    
    def download_image_temp(self, image_ref: str) -> Optional[str]:
        """
        Download image to temporary file if it's a URL, or return local path.
        
        Args:
            image_ref: Local path or Cloudinary URL
            
        Returns:
            Local file path (temporary or original)
        """
        try:
            # If it's a URL, download it
            if image_ref.startswith("http://") or image_ref.startswith("https://"):
                import requests
                import tempfile
                
                response = requests.get(image_ref, timeout=10)
                response.raise_for_status()
                
                # Create temp file
                suffix = Path(image_ref).suffix or ".jpg"
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
                temp_file.write(response.content)
                temp_file.close()
                
                logger.info(f"Downloaded image to temp file: {temp_file.name}")
                return temp_file.name
            else:
                # It's already a local path
                if os.path.exists(image_ref):
                    return image_ref
                else:
                    logger.error(f"Local file not found: {image_ref}")
                    return None
        except Exception as e:
            logger.error(f"Error downloading image: {str(e)}")
            return None
    
    def delete_image(self, image_ref: str) -> bool:
        """
        Delete an image from storage.
        
        Args:
            image_ref: Local path or Cloudinary URL
            
        Returns:
            True if successful
        """
        try:
            if self.storage_type == "cloudinary" and image_ref.startswith("http"):
                # Extract public_id from URL and delete from Cloudinary
                # Cloudinary URL format: https://res.cloudinary.com/{cloud_name}/image/upload/{public_id}.{ext}
                parts = image_ref.split("/upload/")
                if len(parts) > 1:
                    public_id = parts[1].rsplit(".", 1)[0]
                    cloudinary.uploader.destroy(public_id)
                    logger.info(f"Deleted from Cloudinary: {public_id}")
            
            # Also try to delete local file if it exists
            if os.path.exists(image_ref):
                os.remove(image_ref)
                logger.info(f"Deleted local file: {image_ref}")
            
            return True
        except Exception as e:
            logger.error(f"Error deleting image: {str(e)}")
            return False
