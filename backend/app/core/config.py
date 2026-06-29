from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    app_name: str = "志愿参谋 API"
    api_prefix: str = "/api/v1"

    # Database
    database_url: str = "sqlite+aiosqlite:///./gaokao.db"

    # DeepSeek
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3457"

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
