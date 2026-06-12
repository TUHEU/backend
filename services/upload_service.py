# backend/services/upload_service.py
import cloudinary
import cloudinary.uploader
from config.settings import Config


cloudinary.config(
    cloud_name=Config.CLOUDINARY_CLOUD_NAME,
    api_key=Config.CLOUDINARY_API_KEY,
    api_secret=Config.CLOUDINARY_API_SECRET,
    secure=True,
)


class UploadService:
    """Handles file uploads to Cloudinary."""

    @staticmethod
    def upload_profile_image(file_stream, public_id: str | None = None) -> str | None:
        """
        Upload a profile image to Cloudinary.
        Returns the secure URL or None on failure.
        """
        try:
            result = cloudinary.uploader.upload(
                file_stream,
                folder='talent_bridge/profiles',
                public_id=public_id,
                overwrite=True,
                resource_type='image',
                transformation=[
                    {'width': 400, 'height': 400, 'crop': 'fill', 'gravity': 'face'},
                    {'quality': 'auto', 'fetch_format': 'auto'},
                ],
            )
            return result.get('secure_url')
        except Exception as e:
            print(f"[UPLOAD] Cloudinary error: {e}")
            return None

    @staticmethod
    def delete_image(public_id: str) -> bool:
        try:
            cloudinary.uploader.destroy(public_id)
            return True
        except Exception as e:
            print(f"[UPLOAD] Delete error: {e}")
            return False


upload_service = UploadService()
