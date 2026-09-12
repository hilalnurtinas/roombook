import pytest
from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class _RequiredOnlySettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    database_url: str
    test_database_url: str


def test_missing_required_env_var_fails_fast(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("TEST_DATABASE_URL", raising=False)

    with pytest.raises(ValidationError):
        _RequiredOnlySettings()
