from datetime import date, timedelta
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from pymongo import ReturnDocument
from pymongo.collection import Collection
from pymongo.database import Database

from app.models.inventory import ConsumptionCreate, InventoryCreate, InventoryUpdate
from app.repositories.inventory import (
    InsufficientInventoryQuantity,
    InventoryRepository,
)

HOUSEHOLD_ID = UUID("4f720716-cc5c-4a4a-9d06-41de7abdb871")
INVENTORY_ID = UUID("2f720716-cc5c-4a4a-9d06-41de7abdb871")


def _stored_item(
    *,
    quantity: float = 4,
    consumption_history: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "_id": str(INVENTORY_ID),
        "householdId": str(HOUSEHOLD_ID),
        "ingredient": "Spinach",
        "category": "produce",
        "quantity": quantity,
        "unit": "bunches",
        "purchaseDate": date.today().isoformat(),
        "expiryDate": (date.today() + timedelta(days=4)).isoformat(),
        "storage": "refrigerator",
        "notes": None,
        "consumptionHistory": consumption_history or [],
    }


def _repository() -> tuple[InventoryRepository, MagicMock]:
    collection = MagicMock(spec=Collection)
    database = MagicMock(spec=Database)
    database.__getitem__.return_value = collection
    return InventoryRepository(database), collection


def test_create_stores_inventory_item_without_derived_status() -> None:
    repository, collection = _repository()
    item = repository.create(
        HOUSEHOLD_ID,
        InventoryCreate(
            ingredient="Spinach",
            category="produce",
            quantity=4,
            unit="bunches",
        ),
    )

    document = collection.insert_one.call_args.args[0]

    assert document["_id"] == str(item.inventory_id)
    assert document["householdId"] == str(HOUSEHOLD_ID)
    assert "inventoryId" not in document
    assert "status" not in document
    assert item.quantity == 4


def test_get_item_is_scoped_to_its_household() -> None:
    repository, collection = _repository()
    collection.find_one.return_value = _stored_item()

    item = repository.get_by_id(HOUSEHOLD_ID, INVENTORY_ID)

    collection.find_one.assert_called_once_with(
        {"_id": str(INVENTORY_ID), "householdId": str(HOUSEHOLD_ID)}
    )
    assert item is not None
    assert item.inventory_id == INVENTORY_ID
    assert item.household_id == HOUSEHOLD_ID


def test_list_sorts_items_by_expiry_then_name() -> None:
    repository, collection = _repository()
    later = _stored_item()
    later["_id"] = str(uuid4())
    later["ingredient"] = "Zucchini"
    later["expiryDate"] = (date.today() + timedelta(days=8)).isoformat()
    sooner = _stored_item()
    sooner["_id"] = str(uuid4())
    sooner["ingredient"] = "Spinach"
    sooner["expiryDate"] = (date.today() + timedelta(days=1)).isoformat()
    collection.find.return_value = [later, sooner]

    items = repository.list_for_household(HOUSEHOLD_ID)

    collection.find.assert_called_once_with({"householdId": str(HOUSEHOLD_ID)})
    assert [item.ingredient for item in items] == ["Spinach", "Zucchini"]


def test_update_preserves_consumption_history() -> None:
    repository, collection = _repository()
    collection.find_one_and_update.return_value = _stored_item()

    item = repository.update(
        HOUSEHOLD_ID,
        INVENTORY_ID,
        InventoryUpdate(
            ingredient="Spinach",
            category="produce",
            quantity=4,
            unit="bunches",
            storage="refrigerator",
        ),
    )

    query, update = collection.find_one_and_update.call_args.args
    assert query == {"_id": str(INVENTORY_ID), "householdId": str(HOUSEHOLD_ID)}
    assert update["$set"]["quantity"] == 4
    assert "consumptionHistory" not in update["$set"]
    assert collection.find_one_and_update.call_args.kwargs["return_document"] == (
        ReturnDocument.AFTER
    )
    assert item is not None
    assert item.quantity == 4


def test_delete_is_scoped_to_household_and_reports_match() -> None:
    repository, collection = _repository()
    collection.delete_one.return_value.deleted_count = 1

    deleted = repository.delete(HOUSEHOLD_ID, INVENTORY_ID)

    collection.delete_one.assert_called_once_with(
        {"_id": str(INVENTORY_ID), "householdId": str(HOUSEHOLD_ID)}
    )
    assert deleted


def test_consumption_atomically_decrements_and_records_history() -> None:
    repository, collection = _repository()
    collection.update_one.return_value.matched_count = 1
    collection.find_one.return_value = _stored_item(
        quantity=2.5,
        consumption_history=[
            {
                "quantity": 1.5,
                "consumedAt": "2026-10-04T12:00:00+00:00",
            }
        ],
    )

    item = repository.consume(
        HOUSEHOLD_ID,
        INVENTORY_ID,
        ConsumptionCreate(quantity=1.5),
    )

    query, update = collection.update_one.call_args.args
    assert query == {
        "_id": str(INVENTORY_ID),
        "householdId": str(HOUSEHOLD_ID),
        "quantity": {"$gte": 1.5},
    }
    assert update["$inc"] == {"quantity": -1.5}
    assert update["$push"]["consumptionHistory"]["quantity"] == 1.5
    assert item is not None
    assert item.quantity == 2.5
    assert len(item.consumption_history) == 1


def test_consumption_rejects_quantity_above_remaining_stock() -> None:
    repository, collection = _repository()
    collection.update_one.return_value.matched_count = 0
    collection.find_one.return_value = _stored_item(quantity=1)

    with pytest.raises(InsufficientInventoryQuantity):
        repository.consume(
            HOUSEHOLD_ID,
            INVENTORY_ID,
            ConsumptionCreate(quantity=2),
        )


def test_get_missing_inventory_item_returns_none() -> None:
    repository, collection = _repository()
    collection.find_one.return_value = None

    item = repository.get_by_id(HOUSEHOLD_ID, INVENTORY_ID)

    assert item is None
