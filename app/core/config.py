from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Notion Configuration
    notion_token: str
    notion_feeds_db_id: str
    notion_read_later_db_id: str
    
    # Discord Configuration
    discord_token: str
    discord_channel_id: int
    
    # LLM (Groq) Configuration
    groq_api_key: str
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
