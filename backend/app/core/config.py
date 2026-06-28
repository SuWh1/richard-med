from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "Richard Med"
    API_V1_PREFIX: str = "/api/v1"
    BACKEND_CORS_ORIGINS: str = "http://localhost:5173"
    # Allow any Vercel deployment (production + per-branch preview URLs) by default.
    BACKEND_CORS_ORIGIN_REGEX: str = r"https://.*\.vercel\.app"

    POSTGRES_USER: str = "richard_med"
    POSTGRES_PASSWORD: str = "richard_med"
    POSTGRES_DB: str = "richard_med"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    # Geocoding (offline only — clinic addresses → lat/lng). Empty key disables it.
    YANDEX_GEOCODER_API_KEY: str = ""
    YANDEX_GEOCODER_URL: str = "https://geocode-maps.yandex.ru/v1"

    # 2GIS ratings/reviews (offline only — never called in the user/search path).
    # Step A (firm-id discovery) runs via the Node browser collector; Step B (reviews
    # refresh) hits the public reviews API below with a stable firm_id, no browser.
    TWOGIS_REVIEWS_KEY: str = "6e7e1929-4ea9-4a5d-8c05-d601860389bd"
    TWOGIS_REVIEWS_URL: str = "https://public-api.reviews.2gis.com/3.0/branches"
    # A 2GIS firm is accepted as a branch's match only within this radius (geocoding drift).
    TWOGIS_MATCH_RADIUS_M: int = 500
    # Reviews older than this are re-fetched on the daily refresh; fresh ones are skipped.
    TWOGIS_REVIEW_TTL_DAYS: int = 7
    TWOGIS_REVIEW_SAMPLE: int = 5

    # LLM match verification (offline only — confirms semantic suggestions). Empty key disables it.
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash-lite"
    GEMINI_URL: str = "https://generativelanguage.googleapis.com/v1beta/models"
    # Min seconds between verify calls, to respect free-tier RPM (15 RPM → 4s; 0 = off).
    GEMINI_MIN_INTERVAL_SEC: float = 4.5

    # Live on-miss lookup: when a search finds no DB prices, fetch the single queried
    # service from DOQ's public API, persist it as normal source-backed records, and
    # return it in the same response. Time-boxed and best-effort — a failure falls back
    # to the normal empty result, so search never hangs. DOQ only (KDL has no per-service
    # query); never bypasses the DB write, so results stay auditable (Price Passport).
    LIVE_FALLBACK_ENABLED: bool = True
    LIVE_FALLBACK_TIMEOUT_SEC: float = 3.0

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
