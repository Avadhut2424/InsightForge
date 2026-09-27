from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str = "development"
    app_port: int = 8000
    database_url: str
    openai_api_key: str
    tavily_api_key: str | None = None
    llm_provider: str = "ollama"
    ollama_base_url: str = "http://host.docker.internal:11434/v1"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
