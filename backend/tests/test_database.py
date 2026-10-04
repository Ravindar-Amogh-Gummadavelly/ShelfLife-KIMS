from unittest.mock import MagicMock, Mock

import pytest

from app.config import Settings
from app.database import MongoDatabase


def test_database_selects_configured_database_and_pings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = MagicMock()
    selected_database = Mock()
    client.__getitem__.return_value = selected_database

    def create_client(uri: str, **options: int) -> MagicMock:
        assert uri == "mongodb://localhost:27017"
        assert options == {"serverSelectionTimeoutMS": 3000}
        return client

    monkeypatch.setattr("app.database.MongoClient", create_client)
    settings = Settings(
        _env_file=None,
        mongodb_uri="mongodb://localhost:27017",
        mongodb_database="shelflife_test",
    )

    database = MongoDatabase(settings)
    database.ping()
    database.close()

    assert database.database is selected_database
    client.__getitem__.assert_called_once_with("shelflife_test")
    client.admin.command.assert_called_once_with("ping")
    client.close.assert_called_once_with()


def test_inventory_index_is_created_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = MagicMock()
    selected_database = MagicMock()
    inventory_collection = MagicMock()
    client.__getitem__.return_value = selected_database
    selected_database.__getitem__.return_value = inventory_collection
    monkeypatch.setattr("app.database.MongoClient", lambda *args, **kwargs: client)
    settings = Settings(
        _env_file=None,
        mongodb_uri="mongodb://localhost:27017",
        mongodb_database="shelflife_test",
    )

    database = MongoDatabase(settings)
    database.ensure_inventory_indexes()
    database.ensure_inventory_indexes()

    inventory_collection.create_index.assert_called_once_with(
        "householdId",
        name="inventory_household_id",
    )
