from collections.abc import Iterator
from unittest.mock import MagicMock, Mock, call

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from pymongo.errors import ServerSelectionTimeoutError

from app.config import Settings
from app.database import MongoDatabase, get_database
from app.main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def test_health_endpoint_returns_ok(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_database_health_endpoint_returns_ok_when_ping_succeeds(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database = Mock(spec=MongoDatabase)
    monkeypatch.setitem(app.dependency_overrides, get_database, lambda: database)
    response = client.get("/api/health/db")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    database.ping.assert_called_once_with()


def test_database_health_endpoint_returns_503_when_ping_fails(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database = Mock(spec=MongoDatabase)
    database.ping.side_effect = ServerSelectionTimeoutError(
        "private connection detail"
    )
    monkeypatch.setitem(app.dependency_overrides, get_database, lambda: database)

    response = client.get("/api/health/db")
    assert response.status_code == 503
    assert response.json() == {"detail": "Database is unavailable"}
    assert "private connection detail" not in response.text


def test_database_health_reuses_client_between_requests(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MONGODB_URI", "mongodb://localhost:27017")
    monkeypatch.setenv("MONGODB_DATABASE", "shelflife_test")
    mongo_client = MagicMock()
    client_factory = Mock(return_value=mongo_client)
    monkeypatch.setattr("app.database.MongoClient", client_factory)

    first_response = client.get("/api/health/db")
    second_response = client.get("/api/health/db")

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    client_factory.assert_called_once_with(
        "mongodb://localhost:27017",
        serverSelectionTimeoutMS=3000,
    )
    mongo_client.admin.command.assert_has_calls([call("ping"), call("ping")])
    assert mongo_client.admin.command.call_count == 2


def test_database_health_endpoint_reports_missing_configuration(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def load_missing_settings() -> Settings:
        return Settings(_env_file=None)

    monkeypatch.setattr("app.database.get_settings", load_missing_settings)

    response = client.get("/api/health/db")

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Database configuration is unavailable"
    }
