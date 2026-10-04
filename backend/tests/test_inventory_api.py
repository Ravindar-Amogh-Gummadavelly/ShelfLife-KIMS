from collections.abc import Iterator
from datetime import date, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException, Request
from fastapi.testclient import TestClient

import app.api.inventory as inventory_api
from app.main import app
from app.models.inventory import (
    ConsumptionCreate,
    ConsumptionRecord,
    InventoryCreate,
    InventoryItem,
    InventoryUpdate,
)
from app.repositories.inventory import InsufficientInventoryQuantity

HOUSEHOLD_ID = UUID("4f720716-cc5c-4a4a-9d06-41de7abdb871")


class FakeHouseholdRepository:
    def exists(self, household_id: UUID) -> bool:
        return household_id == HOUSEHOLD_ID


class FakeInventoryRepository:
    def __init__(self) -> None:
        self.items: dict[UUID, InventoryItem] = {}

    def create(self, household_id: UUID, item_data: InventoryCreate) -> InventoryItem:
        item = InventoryItem(
            household_id=household_id,
            **item_data.model_dump(),
        )
        self.items[item.inventory_id] = item
        return item

    def list_for_household(self, household_id: UUID) -> list[InventoryItem]:
        return sorted(
            (
                item
                for item in self.items.values()
                if item.household_id == household_id
            ),
            key=lambda item: item.expiry_date or date.max,
        )

    def update(
        self,
        household_id: UUID,
        inventory_id: UUID,
        item_data: InventoryUpdate,
    ) -> InventoryItem | None:
        existing = self.items.get(inventory_id)
        if existing is None or existing.household_id != household_id:
            return None
        updated = InventoryItem(
            inventory_id=inventory_id,
            household_id=household_id,
            consumption_history=existing.consumption_history,
            **item_data.model_dump(),
        )
        self.items[inventory_id] = updated
        return updated

    def delete(self, household_id: UUID, inventory_id: UUID) -> bool:
        existing = self.items.get(inventory_id)
        if existing is None or existing.household_id != household_id:
            return False
        del self.items[inventory_id]
        return True

    def consume(
        self,
        household_id: UUID,
        inventory_id: UUID,
        consumption: ConsumptionCreate,
    ) -> InventoryItem | None:
        existing = self.items.get(inventory_id)
        if existing is None or existing.household_id != household_id:
            return None
        if consumption.quantity > existing.quantity:
            raise InsufficientInventoryQuantity
        updated = existing.model_copy(
            update={
                "quantity": existing.quantity - consumption.quantity,
                "consumption_history": [
                    *existing.consumption_history,
                    ConsumptionRecord(quantity=consumption.quantity),
                ],
            }
        )
        self.items[inventory_id] = updated
        return updated


@pytest.fixture
def repositories() -> Iterator[FakeInventoryRepository]:
    repository = FakeInventoryRepository()
    app.dependency_overrides[inventory_api.get_inventory_repository] = (
        lambda: lambda: repository
    )
    app.dependency_overrides[inventory_api.get_household_repository] = (
        lambda: lambda: FakeHouseholdRepository()
    )
    try:
        yield repository
    finally:
        app.dependency_overrides.pop(inventory_api.get_inventory_repository, None)
        app.dependency_overrides.pop(inventory_api.get_household_repository, None)


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def _inventory_payload(**overrides: object) -> dict[str, object]:
    return {
        "ingredient": "Spinach",
        "category": "produce",
        "quantity": 4,
        "unit": "bunches",
        "purchaseDate": date.today().isoformat(),
        "expiryDate": (date.today() + timedelta(days=2)).isoformat(),
        "storage": "refrigerator",
        "notes": "Use in soup",
        **overrides,
    }


def test_create_and_list_inventory_items(
    client: TestClient,
    repositories: FakeInventoryRepository,
) -> None:
    create_response = client.post(
        f"/api/households/{HOUSEHOLD_ID}/inventory",
        json=_inventory_payload(),
    )

    assert create_response.status_code == 201
    item = create_response.json()
    assert UUID(item["inventoryId"])
    assert item["householdId"] == str(HOUSEHOLD_ID)
    assert item["status"] == "EXPIRING"
    assert item["quantity"] == 4

    list_response = client.get(f"/api/households/{HOUSEHOLD_ID}/inventory")

    assert list_response.status_code == 200
    assert [record["inventoryId"] for record in list_response.json()] == [
        item["inventoryId"]
    ]
    assert len(repositories.items) == 1


def test_create_inventory_rejects_invalid_values(client: TestClient) -> None:
    response = client.post(
        f"/api/households/{HOUSEHOLD_ID}/inventory",
        json=_inventory_payload(quantity=0),
    )

    assert response.status_code == 422


def test_inventory_requires_an_existing_household(
    client: TestClient,
    repositories: FakeInventoryRepository,
) -> None:
    missing_id = uuid4()

    response = client.post(
        f"/api/households/{missing_id}/inventory",
        json=_inventory_payload(),
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Household not found"}
    assert repositories.items == {}


def test_update_inventory_item(
    client: TestClient,
    repositories: FakeInventoryRepository,
) -> None:
    create_response = client.post(
        f"/api/households/{HOUSEHOLD_ID}/inventory",
        json=_inventory_payload(),
    )
    inventory_id = create_response.json()["inventoryId"]

    response = client.put(
        f"/api/households/{HOUSEHOLD_ID}/inventory/{inventory_id}",
        json=_inventory_payload(quantity=2, storage="freezer"),
    )

    assert response.status_code == 200
    assert response.json()["quantity"] == 2
    assert response.json()["storage"] == "freezer"
    assert len(repositories.items) == 1


def test_delete_inventory_item(
    client: TestClient,
    repositories: FakeInventoryRepository,
) -> None:
    create_response = client.post(
        f"/api/households/{HOUSEHOLD_ID}/inventory",
        json=_inventory_payload(),
    )
    inventory_id = create_response.json()["inventoryId"]

    response = client.delete(
        f"/api/households/{HOUSEHOLD_ID}/inventory/{inventory_id}"
    )

    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/api/households/{HOUSEHOLD_ID}/inventory").json() == []
    assert repositories.items == {}


def test_consumption_updates_remaining_quantity_and_history(
    client: TestClient,
    repositories: FakeInventoryRepository,
) -> None:
    create_response = client.post(
        f"/api/households/{HOUSEHOLD_ID}/inventory",
        json=_inventory_payload(),
    )
    inventory_id = create_response.json()["inventoryId"]

    response = client.post(
        f"/api/households/{HOUSEHOLD_ID}/inventory/{inventory_id}/consumption",
        json={"quantity": 1.5},
    )

    assert response.status_code == 200
    assert response.json()["quantity"] == 2.5
    assert response.json()["consumptionHistory"][0]["quantity"] == 1.5
    assert response.json()["consumptionHistory"][0]["consumedAt"]
    assert next(iter(repositories.items.values())).quantity == 2.5


def test_consumption_cannot_exceed_remaining_quantity(
    client: TestClient,
    repositories: FakeInventoryRepository,
) -> None:
    create_response = client.post(
        f"/api/households/{HOUSEHOLD_ID}/inventory",
        json=_inventory_payload(quantity=1),
    )
    inventory_id = create_response.json()["inventoryId"]

    response = client.post(
        f"/api/households/{HOUSEHOLD_ID}/inventory/{inventory_id}/consumption",
        json={"quantity": 2},
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Consumption quantity exceeds the remaining inventory"
    }
    assert next(iter(repositories.items.values())).quantity == 1


def test_inventory_database_failure_is_reported_without_leaking_configuration(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def database_is_unavailable(request: Request) -> None:
        assert request.method == "GET"
        raise HTTPException(
            status_code=503,
            detail="Database configuration is unavailable",
        )

    monkeypatch.setattr(inventory_api, "get_database", database_is_unavailable)

    response = client.get(f"/api/households/{HOUSEHOLD_ID}/inventory")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database configuration is unavailable"}
