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
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
