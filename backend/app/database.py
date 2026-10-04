from threading import Lock
from typing import Any

from fastapi import HTTPException, Request
from pydantic import ValidationError
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from app.config import Settings, get_settings


class MongoDatabase:
    def __init__(self, settings: Settings) -> None:
        self._client: MongoClient[dict[str, Any]] = MongoClient(
            settings.mongodb_uri.get_secret_value(),
            serverSelectionTimeoutMS=3000,
        )
        self.database = self._client[settings.mongodb_database]
        self._inventory_indexes_lock = Lock()
        self._inventory_indexes_ready = False

    def ping(self) -> None:
        self._client.admin.command("ping")

    def ensure_inventory_indexes(self) -> None:
        with self._inventory_indexes_lock:
            if self._inventory_indexes_ready:
                return
            self.database["inventory_items"].create_index(
                "householdId",
                name="inventory_household_id",
            )
            self._inventory_indexes_ready = True

    def close(self) -> None:
        self._client.close()


def get_database(request: Request) -> MongoDatabase:
    with request.app.state.database_lock:
        database = request.app.state.database
        if database is not None:
            return database

        try:
            settings = get_settings()
            database = MongoDatabase(settings)
        except (ValidationError, PyMongoError):
            raise HTTPException(
                status_code=503,
                detail="Database configuration is unavailable",
            ) from None

        request.app.state.database = database
        return database
