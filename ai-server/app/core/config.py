from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    openai_api_key: str
    chroma_host: str = "localhost"
    chroma_port: int = 8001
    internal_api_key: str
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    # T-410: CORS 허용 오리진 (쉼표 구분, 기본값은 로컬 개발)
    allowed_origins: str = "http://localhost:3000"


settings = Settings()
