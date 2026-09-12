import sys

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str


def _load_settings(_env_file: str | None = ".env") -> Settings:
    try:
        return Settings(_env_file=_env_file)
    except ValidationError as exc:
        missing = ", ".join(sorted({str(error["loc"][0]) for error in exc.errors()}))
        sys.stderr.write(
            f"roombook: missing required environment variable(s): {missing}\n"
            "See .env.example for the full list.\n"
        )
        raise SystemExit(1) from None


settings = _load_settings()
