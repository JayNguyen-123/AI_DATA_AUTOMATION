from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App Settings
    PROJECT_NAME: str = "Enterprise AI Data Automation Pipeline"
    VERSION: str = "1.0.0"
    UPLOAD_DIR: str = "/tmp/automation_uploads"

    # Infrastructure Credentials
    DATABASE_URL: str = Field(..., validation_alias="DATABASE_URL")
    CELERY_BROKER_URL: str = Field(..., validation_alias="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field(..., validation_alias="CELERY_RESULT_BACKEND")

    # Cloud & Vendor APIs
    AWS_ACCESS_KEY_ID: str = Field(..., validation_alias="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str = Field(..., validation_alias="AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = "us-east-1"

    # Core AI & Proxy Settings
    OPENAI_API_KEY: str = Field(..., validation_alias="OPENAI_API_KEY")
    BRIGHT_DATA_ZONE_PROXY: str = Field(..., validation_alias="BRIGHT_DATA_ZONE_PROXY")

    # Read from local root environment profile
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
