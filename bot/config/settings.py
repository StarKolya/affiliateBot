from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", env_ignore_empty=True)

    BOT_TOKEN: str

    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    CHANNEL_ID: int
    CHANNEL_URL: str | None = None

    CHANNEL_ID_2: int | None = None
    CHANNEL_URL_2: str | None = None

    BOT_USERNAME: str

    # Channel to notify on every new applicant (optional — leave blank to disable)
    APPLICANT_NOTIFICATIONS_CHANNEL_ID: int | None = None

    # Comma-separated telegram IDs bootstrapped as admins on first startup
    ADMIN_TELEGRAM_IDS: list[int] = []

    @property
    def db_url(self) -> str:
        return (
            f"mysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


settings = Settings()
