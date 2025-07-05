
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # ... (Database and JWT settings remain the same) ...
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/fileapidb")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "a_very_secret_key")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # --- NEW: Storage Service Configuration ---
    # Can be 'local' or 's3'
    STORAGE_TYPE: str = os.getenv("STORAGE_TYPE", "s3") 

    # --- NEW: S3 (Scaleway) Configuration ---
    S3_ENDPOINT_URL: str = os.getenv("S3_ENDPOINT_URL", "https://storafe1.s3.fr-par.scw.cloud")
    S3_ACCESS_KEY_ID: str = os.getenv("S3_ACCESS_KEY_ID", "S3_ACCESS_KEY_ID")
    S3_SECRET_ACCESS_KEY: str = os.getenv("S3_SECRET_ACCESS_KEY", "S3_SECRET_ACCESS_KEY")
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "storafe1")
    S3_REGION: str = os.getenv("S3_REGION", "fr-par")

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()
