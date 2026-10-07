from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_TITLE: str = "Bulk Certificate Generator API"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "High-performance backend API for bulk certificate generation, status tracking, and retrieval."
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    DATABASE_URL: str = "sqlite:///./bulk_certs.db"
    STORAGE_DIR: str = "storage/certificates"
    BASE_URL: str = "http://localhost:8000"
    MAX_BATCH_SIZE: int = 5000

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @property
    def storage_path(self) -> Path:
        path = Path(self.STORAGE_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
