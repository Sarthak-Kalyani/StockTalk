from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "StockTalk Backend"
    database_url: str = "sqlite:///./stocktalk_dev.db"

    # Supabase Configuration
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""  # For verifying Supabase JWTs
    supabase_jwks_url: str = ""    # e.g., https://<project>.supabase.co/auth/v1/.well-known/jwks.json

    # Google Cloud Vision (OCR)
    google_cloud_vision_credentials: str = ""  # Path to service account JSON or JSON string

    # Razorpay (Payments)
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""

    # File Storage (Supabase Storage)
    supabase_storage_bucket_bills: str = "bills"
    supabase_storage_bucket_chat: str = "chat-attachments"
    supabase_storage_bucket_catalogue: str = "catalogue-images"

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()