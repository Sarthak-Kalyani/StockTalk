from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "StockTalk Backend"
    database_url: str = "sqlite:///./stocktalk_dev.db"
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_bucket: str = "stocktalk-attachments"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()