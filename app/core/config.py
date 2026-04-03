from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Notion Configuration (STILL REQUIRED - Phase 2 migration not yet complete)
    notion_token: str
    notion_feeds_db_id: str
    notion_read_later_db_id: str
    notion_weekly_digests_db_id: str
    
    # Supabase Configuration (Phase 1 complete - database infrastructure ready)
    supabase_url: str
    supabase_key: str
    
    # Discord Configuration
    discord_token: str
    discord_channel_id: int
    
    # LLM (Groq) Configuration
    groq_api_key: str

    # Timezone Configuration
    timezone: str = "Asia/Taipei"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
