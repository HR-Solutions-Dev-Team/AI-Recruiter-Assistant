from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "AI Recruiter Assistant API"
    host: str = "0.0.0.0"
    port: int = 443
    static_dir: str = "/app/static"
    ssl_cert_file: str = "/app/certs/cert.pem"
    ssl_key_file: str = "/app/certs/key.pem"

    @property
    def static_path(self) -> Path:
        return Path(self.static_dir)

    @property
    def static_dir_exists(self) -> bool:
        return self.static_path.exists()


settings = Settings()
