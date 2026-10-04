from pathlib import Path

import pytest
from pydantic import ValidationError

from app.config import Settings, get_settings


def test_settings_load_mongodb_configuration_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MONGODB_URI", "mongodb://localhost:27017")
    monkeypatch.setenv("MONGODB_DATABASE", "shelflife_test")

    settings = get_settings()

    assert settings.mongodb_uri.get_secret_value() == "mongodb://localhost:27017"
    assert settings.mongodb_database == "shelflife_test"
    assert "mongodb://localhost:27017" not in repr(settings)


def test_settings_load_local_env_file(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "MONGODB_URI=mongodb://localhost:27017\n"
        "MONGODB_DATABASE=shelflife_test\n",
        encoding="utf-8",
    )

    settings = Settings(_env_file=env_file)

    assert settings.mongodb_uri.get_secret_value() == "mongodb://localhost:27017"
    assert settings.mongodb_database == "shelflife_test"


@pytest.mark.parametrize(
    ("uri", "database"),
    [
        ("", "shelflife_test"),
        ("mongodb://localhost:27017", ""),
    ],
)
def test_settings_reject_empty_mongodb_configuration(
    monkeypatch: pytest.MonkeyPatch,
    uri: str,
    database: str,
) -> None:
    monkeypatch.setenv("MONGODB_URI", uri)
    monkeypatch.setenv("MONGODB_DATABASE", database)

    with pytest.raises(ValidationError):
        get_settings()
