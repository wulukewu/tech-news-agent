from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Supabase Configuration
    supabase_url: str
    supabase_key: str
    
    # Discord Configuration
    discord_token: str
    discord_channel_id: int
    
    # LLM (Groq) Configuration
    groq_api_key: str

    # Timezone Configuration
    timezone: str = "Asia/Taipei"
    
    # RSS Configuration
    rss_fetch_days: int = 7
    
    # Scheduler Configuration
    scheduler_cron: str = "0 */6 * * *"  # Every 6 hours by default
    scheduler_timezone: str | None = None  # Defaults to timezone if not set
    
    # Batch Processing Configuration
    batch_size: int = 50  # Maximum articles per batch
    batch_split_threshold: int = 100  # Split into multiple batches above this
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
