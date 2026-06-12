# backend/services/cloudinary_service.py
import cloudinary
import cloudinary.uploader
from config.settings import Config


cloudinary.config(
    cloud_name=Config.CLOUDINARY_CLOUD_NAME,
    api_key=Config.CLOUDINARY_API_KEY,
    api_secret=Config.CLOUDINARY_API_SECRET,
    secure=True,
)


class CloudinaryService:
    PROFILE_FOLDER = 'talent_bridge/profiles'

    @staticmethod
    def upload_profile_image(file_stream, user_id: int) -> str | None:
        """Upload a profile image and return its secure URL, or None on failure."""
        try:
            result = cloudinary.uploader.upload(
                file_stream,
                folder=CloudinaryService.PROFILE_FOLDER,
                public_id=f'user_{user_id}',
                overwrite=True,
                resource_type='image',
                transformation=[
                    {'width': 400, 'height': 400, 'crop': 'fill', 'gravity': 'face'},
                    {'quality': 'auto:good', 'fetch_format': 'auto'},
                ],
            )
            return result.get('secure_url')
        except Exception as e:
            print(f'[Cloudinary] Upload error for user {user_id}: {e}')
            return None

    @staticmethod
    def delete_image(public_id: str) -> bool:
        try:
            cloudinary.uploader.destroy(public_id)
            return True
        except Exception as e:
            print(f'[Cloudinary] Delete error {public_id}: {e}')
            return False


cloudinary_service = CloudinaryService()
