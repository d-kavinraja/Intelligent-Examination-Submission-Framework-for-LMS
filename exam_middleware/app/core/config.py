"""
Examination Middleware - Configuration Module
Pydantic Settings for type-safe configuration management
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
import json


class Settings(BaseSettings):
    """Application Settings with validation"""
    
    # Application
    app_name: str = Field(default="Exam Submission Middleware")
    app_version: str = Field(default="1.0.0")
    debug: bool = Field(default=False)
    secret_key: str = Field(default="change-this-secret-key")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=60)
    
    # Server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    reload: bool = Field(default=True)
    
    # PostgreSQL
    postgres_host: str = Field(default="localhost")
    postgres_port: int = Field(default=5432)
    postgres_user: str = Field(default="postgres")
    postgres_password: str = Field(default="")
    postgres_db: str = Field(default="exam_middleware")
    database_url: Optional[str] = None
    
    # Redis
    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379)
    redis_password: str = Field(default="")
    redis_db: int = Field(default=0)
    redis_url: Optional[str] = None
    
    # Moodle - Configure for your Moodle instance
    # Default: College's Moodle at lms.ai.saveetha.in
    moodle_base_url: str = Field(default="https://lms.ai.saveetha.in")
    moodle_ws_endpoint: str = Field(default="/webservice/rest/server.php")
    moodle_upload_endpoint: str = Field(default="/webservice/upload.php")
    moodle_token_endpoint: str = Field(default="/login/token.php")
    moodle_service: str = Field(default="moodle_mobile_app")
    # OPTIONAL: Admin token only needed for admin operations
    # Students use their own Moodle tokens for submissions
    moodle_admin_token: Optional[str] = None

    # Email Notifications (SendGrid preferred, SMTP fallback)
    sendgrid_api_key: str = Field(default="")
    email_from_email: str = Field(default="")
    email_from_name: str = Field(default="Examination Middleware")
    
    # SMTP Mail (fallback for local dev)
    smtp_enabled: bool = Field(default=False)
    smtp_host: str = Field(default="")
    smtp_port: int = Field(default=587)
    smtp_username: str = Field(default="")
    smtp_password: str = Field(default="")
    smtp_use_tls: bool = Field(default=True)
    smtp_use_ssl: bool = Field(default=False)
    smtp_from_email: str = Field(default="")
    smtp_from_name: str = Field(default="Examination Middleware")
    
    # File Storage
    upload_dir: str = Field(default="./uploads")
    max_file_size_mb: int = Field(default=50)
    allowed_extensions: str = Field(default=".pdf,.jpg,.jpeg,.png")
    
    # ML Service Configuration
    # LOCAL MODE (default): Uses YOLO + CRNN models running on this machine
    # Set HF_SPACE_URL to use remote extraction via HuggingFace Spaces instead
    hf_space_url: str = Field(default="")  # Leave empty to use local models
    ml_service_url: str = Field(default="http://localhost:8501")  # Streamlit UI (optional)
    ml_service_enabled: bool = Field(default=False)  # Disable remote HF Spaces by default
    
    # Logging
    log_level: str = Field(default="INFO")
    log_file: str = Field(default="./logs/app.log")
    
    # CORS
    cors_origins: str = Field(default='["*"]')
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @property
    def database_url_computed(self) -> str:
        """Compute database URL if not provided"""
        if self.database_url:
            url = self.database_url
            # Render provides postgres:// but asyncpg needs postgresql+asyncpg://
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+asyncpg://", 1)
            elif url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            # If already has +asyncpg, leave it
            return url
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    @property
    def database_url_sync(self) -> str:
        """Synchronous database URL for migrations"""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    @property
    def redis_url_computed(self) -> str:
        """Compute Redis URL if not provided"""
        if self.redis_url:
            return self.redis_url
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    @property
    def moodle_webservice_url(self) -> str:
        """Full Moodle webservice URL"""
        return f"{self.moodle_base_url}{self.moodle_ws_endpoint}"
    
    @property
    def moodle_upload_url(self) -> str:
        """Full Moodle upload URL"""
        return f"{self.moodle_base_url}{self.moodle_upload_endpoint}"
    
    @property
    def moodle_token_url(self) -> str:
        """Full Moodle token URL"""
        return f"{self.moodle_base_url}{self.moodle_token_endpoint}"
    
    @property
    def allowed_extensions_list(self) -> List[str]:
        """Parse allowed extensions as list"""
        return [ext.strip() for ext in self.allowed_extensions.split(",")]
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins as list"""
        try:
            return json.loads(self.cors_origins)
        except json.JSONDecodeError:
            return ["*"]
    
    @property
    def max_file_size_bytes(self) -> int:
        """Max file size in bytes"""
        return self.max_file_size_mb * 1024 * 1024
    
    def get_subject_assignment_mapping(self) -> dict:
        """Return subject code to assignment ID mapping"""
        return {}

    @property
    def smtp_sender_email(self) -> str:
        """Resolved sender email address for outgoing notifications"""
        return self.smtp_from_email or self.smtp_username
    
    @property
    def email_sender_email(self) -> str:
        """Primary sender email (for SendGrid or SMTP)"""
        return self.email_from_email or self.smtp_sender_email


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()
