from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Supabase Configuration
    supabase_url: str
    supabase_key: str
    
    # Discord Configuration
    discord_token: str
    discord_channel_id: Optional[int] = None  # 改為選填，因為改用 DM 通知
    
    # Discord OAuth2 Configuration
    discord_client_id: Optional[str] = None
    discord_client_secret: Optional[str] = None
    discord_redirect_uri: Optional[str] = None
    
    # LLM (Groq) Configuration
    groq_api_key: str

    # Timezone Configuration
    timezone: str = "Asia/Taipei"
    
    # RSS Configuration
    rss_fetch_days: int = 7
    
    # Scheduler Configuration
    scheduler_cron: str = "0 */6 * * *"  # Every 6 hours by default
    scheduler_timezone: str | None = None  # Defaults to timezone if not set
    
    # DM Notification Configuration
    dm_notification_cron: str | None = "10 */6 * * *"  # 10 minutes after fetch job
    
    # Batch Processing Configuration
    batch_size: int = 50  # Maximum articles per batch
    batch_split_threshold: int = 100  # Split into multiple batches above this
    
    # JWT Configuration
    jwt_secret: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_expiration_days: int = 7
    
    # CORS Configuration
    cors_origins: str = "http://localhost:3000"  # Comma-separated list
    
    # Rate Limiting Configuration
    rate_limit_per_minute_unauth: int = 100
    rate_limit_per_minute_auth: int = 300
    
    # Security Configuration
    cookie_secure: bool = True  # Use HTTPS in production
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    def validate_jwt_secret(self) -> None:
        """驗證 JWT Secret 長度"""
        if self.jwt_secret is None:
            raise ValueError("JWT_SECRET is required")
        if len(self.jwt_secret) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters")

settings = Settings()
