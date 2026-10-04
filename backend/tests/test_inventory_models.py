from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from app.models.inventory import (
    InventoryCreate,
    InventoryItem,
    InventoryStatus,
    determine_inventory_status,
)


@pytest.mark.parametrize(
    ("days_until_expiry", "expected_status"),
    [
        (-1, InventoryStatus.EXPIRED),
        (0, InventoryStatus.EXPIRING),
        (3, InventoryStatus.EXPIRING),
        (4, InventoryStatus.USE_SOON),
        (7, InventoryStatus.USE_SOON),
        (8, InventoryStatus.FRESH),
    ],
)
def test_inventory_status_uses_deterministic_expiry_windows(
    days_until_expiry: int,
    expected_status: InventoryStatus,
) -> None:
    today = date(2026, 10, 4)

    status = determine_inventory_status(
        today + timedelta(days=days_until_expiry),
        today=today,
    )

    assert status is expected_status


def test_inventory_without_expiry_is_fresh() -> None:
    assert determine_inventory_status(None, today=date(2026, 10, 4)) is InventoryStatus.FRESH


@pytest.mark.parametrize(
    "payload",
    [
        {"ingredient": "", "category": "produce", "quantity": 2, "unit": "pieces"},
        {"ingredient": "Rice", "category": "", "quantity": 2, "unit": "kg"},
        {"ingredient": "Rice", "category": "grain", "quantity": 0, "unit": "kg"},
        {"ingredient": "Rice", "category": "grain", "quantity": -1, "unit": "kg"},
        {"ingredient": "Rice", "category": "grain", "quantity": 1, "unit": ""},
        {
            "ingredient": "Rice",
            "category": "grain",
            "quantity": 1,
            "unit": "kg",
            "purchaseDate": "2026-10-05",
            "expiryDate": "2026-10-04",
        },
        {
            "ingredient": "Rice",
            "category": "grain",
            "quantity": 1,
            "unit": "kg",
            "status": "FRESH",
        },
    ],
)
def test_inventory_create_rejects_invalid_values(payload: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        InventoryCreate.model_validate(payload)


def test_inventory_item_exposes_computed_status() -> None:
    item = InventoryItem(
        householdId="4f720716-cc5c-4a4a-9d06-41de7abdb871",
        ingredient=" Spinach ",
        category=" produce ",
        quantity=2,
        unit=" bunches ",
        expiryDate=date.today() + timedelta(days=2),
    )

    payload = item.model_dump(mode="json", by_alias=True)

    assert item.ingredient == "Spinach"
    assert item.category == "produce"
    assert item.unit == "bunches"
    assert payload["status"] == InventoryStatus.EXPIRING.value
    assert payload["consumptionHistory"] == []
