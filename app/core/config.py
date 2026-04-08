import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='allow')
    database_url: str
    supabase_url: str
    supabase_key: str
    show_error_details: bool

    app_env: str
    task_token: str
    qstash_token: str | None = None


settings = Settings()