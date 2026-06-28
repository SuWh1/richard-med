from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "Richard Med"
    API_V1_PREFIX: str = "/api/v1"
    BACKEND_CORS_ORIGINS: str = "http://localhost:5173"

    POSTGRES_USER: str = "richard_med"
    POSTGRES_PASSWORD: str = "richard_med"
    POSTGRES_DB: str = "richard_med"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    # Geocoding (offline only — clinic addresses → lat/lng). Empty key disables it.
    YANDEX_GEOCODER_API_KEY: str = ""
    YANDEX_GEOCODER_URL: str = "https://geocode-maps.yandex.ru/v1"

    # LLM match verification (offline only — confirms semantic suggestions). Empty key disables it.
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash-lite"
    GEMINI_URL: str = "https://generativelanguage.googleapis.com/v1beta/models"
    # Min seconds between verify calls, to respect free-tier RPM (15 RPM → 4s; 0 = off).
    GEMINI_MIN_INTERVAL_SEC: float = 4.5

    # Auth: signs our own JWTs; admin role is granted to these emails on sign-up.
    AUTH_SECRET: str = "dev-secret-change-me-to-a-long-random-value-in-prod"
    ADMIN_EMAILS: str = "aidyn.fatikh@gmail.com,apasdauren70@gmail.com"

    @property
    def admin_emails(self) -> set[str]:
        return {e.strip().lower() for e in self.ADMIN_EMAILS.split(",") if e.strip()}

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.BACKEND_CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
