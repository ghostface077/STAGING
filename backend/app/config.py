"""
Configuration centrale de l'application, chargée depuis les variables
d'environnement (voir le fichier .env à la racine du projet).
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Base de données
    database_url: str = "postgresql+psycopg2://itsupport:itsupport_dev_password@localhost:5432/itsupport_db"

    # Sécurité / JWT
    secret_key: str = "dev_only_secret_key_please_change"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    # Application
    environment: str = "development"
    backend_cors_origins: str = "http://localhost:3000"
    upload_dir: str = "/app/uploads"
    max_upload_size_mb: int = 15

    # Compte admin de démonstration (utilisé par le seed)
    seed_admin_email: str = "admin@itsupport.example"
    seed_admin_password: str = "Admin123!"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
