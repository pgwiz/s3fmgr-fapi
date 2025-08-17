
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from pathlib import Path
import os
import uuid
import shutil
from fastapi import UploadFile

from app.core.config import settings

class BaseStorageService:
    def save(self, file: UploadFile, user_id: str) -> (str, str):
        """Saves an UploadFile object and returns the saved path/key and a unique filename."""
        raise NotImplementedError

    def save_from_path(self, source_path: Path, user_id: str, original_filename: str) -> (str, str):
        """Saves a file from a local path and returns the saved path/key and a unique filename."""
        raise NotImplementedError

    def get_download_url(self, file_path: str, filename: str) -> str:
        """Returns a downloadable URL for a file."""
        raise NotImplementedError

    def delete(self, file_path: str):
        """Deletes a file."""
        raise NotImplementedError
    def make_public(self, file_path: str):
        """Makes a stored object publicly readable."""
        raise NotImplementedError

    def get_public_url(self, file_path: str) -> str:
        """Constructs the permanent public URL for an object."""
        raise NotImplementedError

class LocalStorageService(BaseStorageService):
    def __init__(self):
        # --- FIX: Use an absolute path based on the project's root directory ---
        self.storage_path = Path.cwd() / "storage" / "local" / "files"
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def save(self, file: UploadFile, user_id: str) -> (str, str):
        user_storage_path = self.storage_path / user_id
        user_storage_path.mkdir(parents=True, exist_ok=True)
        
        saved_filename = f"{uuid.uuid4()}{Path(file.filename).suffix}"
        file_location = user_storage_path / saved_filename
        
        with open(file_location, "wb") as f:
            shutil.copyfileobj(file.file, f)
            
        # Return the absolute path as a string
        return str(file_location), saved_filename

    def save_from_path(self, source_path: Path, user_id: str, original_filename: str) -> (str, str):
        user_storage_path = self.storage_path / user_id
        user_storage_path.mkdir(parents=True, exist_ok=True)
        
        saved_filename = f"{uuid.uuid4()}{Path(original_filename).suffix}"
        dest_path = user_storage_path / saved_filename
        
        shutil.move(source_path, dest_path)
        # Return the absolute path as a string
        return str(dest_path), saved_filename

    def get_download_url(self, file_path: str, filename: str) -> str:
        return file_path

    def delete(self, file_path: str):
        try:
            if Path(file_path).is_file():
                os.remove(file_path)
        except Exception as e:
            print(f"Error deleting local file: {e}")
    def make_public(self, file_path: str):
    # Local files are not made public over the internet by this service.
    # This would require a web server configuration.
        print("Warning: 'make_public' is not applicable for local storage.")
        pass

    def get_public_url(self, file_path: str) -> str:
        # No permanent public URL for local files through this service.
        return None

class S3StorageService(BaseStorageService):
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
            region_name=settings.S3_REGION,
            config=Config(signature_version='s3v4')
        )
        self.bucket_name = settings.S3_BUCKET_NAME

    def save(self, file: UploadFile, user_id: str) -> (str, str):
        file_key = f"{user_id}/{uuid.uuid4()}{Path(file.filename).suffix}"
        self.s3_client.upload_fileobj(file.file, self.bucket_name, file_key)
        return file_key, Path(file_key).name
        
    def save_from_path(self, source_path: Path, user_id: str, original_filename: str) -> (str, str):
        file_key = f"{user_id}/{uuid.uuid4()}{Path(original_filename).suffix}"
        self.s3_client.upload_file(str(source_path), self.bucket_name, file_key)
        source_path.unlink(missing_ok=True) # Clean up temp file
        return file_key, Path(file_key).name

    def get_download_url(self, file_path: str, filename: str) -> str:
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': file_path, 'ResponseContentDisposition': f'attachment; filename="{filename}"'},
                ExpiresIn=3600
            )
            return url
        except ClientError as e:
            print(f"Error generating presigned URL: {e}")
            return None

    def delete(self, file_path: str):
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_path)
        except ClientError as e:
            print(f"Error deleting S3 object: {e}")
    def make_public(self, file_path: str):
        """Sets the Access Control List (ACL) of an S3 object to 'public-read'."""
        try:
            self.s3_client.put_object_acl(Bucket=self.bucket_name, Key=file_path, ACL='public-read')
        except ClientError as e:
            print(f"Error setting public ACL: {e}")
            raise # Re-raise the exception to be handled by the endpoint

    def get_public_url(self, file_path: str) -> str:
        """Constructs the permanent public URL for an S3 object."""
        return f"{self.s3_client.meta.endpoint_url}/{self.bucket_name}/{file_path}"

def get_storage_service() -> BaseStorageService:
    if settings.STORAGE_TYPE == 's3':
        return S3StorageService()
    return LocalStorageService()