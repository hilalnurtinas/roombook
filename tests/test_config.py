import pytest

from app.config import _load_settings


def test_missing_required_env_var_fails_fast(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(SystemExit) as exc_info:
        _load_settings(None)

    assert exc_info.value.code == 1
    assert "database_url" in capsys.readouterr().err
