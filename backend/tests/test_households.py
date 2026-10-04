from collections.abc import Iterator
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.api.households import get_household_repository
from app.main import app
from app.models.household import Household, HouseholdCreate


class FakeHouseholdRepository:
    def __init__(self) -> None:
        self.households: dict[UUID, Household] = {}

    def create(self, household_data: HouseholdCreate) -> Household:
        household = Household(
            name=household_data.name,
            members=[member.model_dump() for member in household_data.members],
        )
        self.households[household.household_id] = household
        return household

    def get_by_id(self, household_id: UUID) -> Household | None:
        return self.households.get(household_id)


@pytest.fixture
def household_repository() -> Iterator[FakeHouseholdRepository]:
    repository = FakeHouseholdRepository()
    app.dependency_overrides[get_household_repository] = lambda: repository
    try:
        yield repository
    finally:
        app.dependency_overrides.pop(get_household_repository, None)


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def test_create_household_returns_generated_id_and_members(
    client: TestClient,
    household_repository: FakeHouseholdRepository,
) -> None:
    response = client.post(
        "/api/households",
        json={
            "name": "My Household",
            "members": [
                {
                    "name": "Alex",
                    "ageCategory": "adult",
                    "constraints": ["vegetarian"],
                    "preferences": ["Indian"],
                    "texture": "firm",
                    "spiceLevel": "low",
                }
            ],
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert UUID(body["householdId"])
    assert body["name"] == "My Household"
    assert len(body["members"]) == 1
    assert UUID(body["members"][0]["personId"])
    assert body["members"][0]["ageCategory"] == "adult"
    assert body["members"][0]["constraints"] == ["vegetarian"]
    assert body["members"][0]["preferences"] == ["Indian"]
    assert household_repository.get_by_id(UUID(body["householdId"])) is not None


def test_get_household_returns_existing_household(
    client: TestClient,
    household_repository: FakeHouseholdRepository,
) -> None:
    create_response = client.post(
        "/api/households",
        json={"name": "My Household", "members": [{"name": "Alex"}]},
    )
    household_id = create_response.json()["householdId"]

    response = client.get(f"/api/households/{household_id}")

    assert response.status_code == 200
    assert response.json()["householdId"] == household_id
    assert response.json()["members"][0]["name"] == "Alex"
    assert UUID(household_id) in household_repository.households


@pytest.mark.parametrize(
    "payload",
    [
        {"name": ""},
        {"name": "   "},
        {"name": "My Household", "members": [{"name": ""}]},
        {"name": "My Household", "unexpected": "field"},
    ],
)
def test_create_household_rejects_invalid_request(
    client: TestClient,
    payload: dict[str, object],
) -> None:
    response = client.post("/api/households", json=payload)

    assert response.status_code == 422


@pytest.mark.usefixtures("household_repository")
def test_get_household_returns_not_found(
    client: TestClient,
) -> None:
    response = client.get("/api/households/4f720716-cc5c-4a4a-9d06-41de7abdb871")

    assert response.status_code == 404
    assert response.json() == {"detail": "Household not found"}


def test_get_household_rejects_malformed_id(
    client: TestClient,
) -> None:
    response = client.get("/api/households/not-a-uuid")

    assert response.status_code == 422
