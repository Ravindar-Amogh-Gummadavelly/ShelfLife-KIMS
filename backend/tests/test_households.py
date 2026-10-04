from collections.abc import Iterator
from uuid import UUID

from fastapi import HTTPException, Request
import pytest
from fastapi.testclient import TestClient

import app.api.households as households_api
from app.api.households import get_household_repository
from app.main import app
from app.models.household import (
    Household,
    HouseholdCreate,
    HouseholdMember,
    HouseholdMemberCreate,
    HouseholdMemberFoodProfileUpdate,
)


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

    def add_member(
        self,
        household_id: UUID,
        member_data: HouseholdMemberCreate,
    ) -> HouseholdMember | None:
        household = self.households.get(household_id)
        if household is None:
            return None
        member = HouseholdMember.model_validate(
            member_data.model_dump(by_alias=True)
        )
        household.members.append(member)
        return member

    def update_member_food_profile(
        self,
        household_id: UUID,
        person_id: UUID,
        profile: HouseholdMemberFoodProfileUpdate,
    ) -> HouseholdMember | None:
        household = self.households.get(household_id)
        if household is None:
            return None
        for index, member in enumerate(household.members):
            if member.person_id == person_id:
                updated_member = HouseholdMember.model_validate(
                    {
                        **member.model_dump(),
                        **profile.model_dump(),
                    }
                )
                household.members[index] = updated_member
                return updated_member
        return None


@pytest.fixture
def household_repository() -> Iterator[FakeHouseholdRepository]:
    repository = FakeHouseholdRepository()
    app.dependency_overrides[get_household_repository] = lambda: lambda: repository
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
                    "allergies": ["peanuts"],
                    "prohibitedFoods": ["pork"],
                    "dietaryRestrictions": ["vegetarian"],
                    "dislikes": [" mushrooms ", "MUSHROOMS"],
                    "preferredFoods": ["lentils"],
                    "texturePreferences": ["firm"],
                    "cuisinePreferences": ["Indian", " indian "],
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
    assert body["members"][0]["allergies"] == ["peanuts"]
    assert body["members"][0]["prohibitedFoods"] == ["pork"]
    assert body["members"][0]["dietaryRestrictions"] == ["vegetarian"]
    assert body["members"][0]["dislikes"] == ["mushrooms"]
    assert body["members"][0]["preferredFoods"] == ["lentils"]
    assert body["members"][0]["texturePreferences"] == ["firm"]
    assert body["members"][0]["cuisinePreferences"] == ["Indian"]
    assert body["members"][0]["spiceLevel"] == "low"
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


@pytest.mark.usefixtures("household_repository")
def test_add_household_member_with_food_profile(client: TestClient) -> None:
    create_response = client.post(
        "/api/households",
        json={"name": "My Household"},
    )
    household_id = create_response.json()["householdId"]

    add_response = client.post(
        f"/api/households/{household_id}/members",
        json={
            "name": "Alex",
            "allergies": ["peanuts"],
            "dietaryRestrictions": ["vegetarian"],
            "dislikes": ["mushrooms"],
            "preferredFoods": ["lentils"],
            "spiceLevel": "low",
            "texturePreferences": ["firm"],
            "cuisinePreferences": ["Indian"],
        },
    )

    assert add_response.status_code == 201
    member = add_response.json()
    assert UUID(member["personId"])
    assert member["allergies"] == ["peanuts"]
    assert member["dietaryRestrictions"] == ["vegetarian"]
    assert member["dislikes"] == ["mushrooms"]
    assert member["spiceLevel"] == "low"

    get_response = client.get(f"/api/households/{household_id}")
    assert len(get_response.json()["members"]) == 1
    assert get_response.json()["members"][0]["personId"] == member["personId"]


@pytest.mark.usefixtures("household_repository")
def test_add_household_member_returns_not_found_for_unknown_household(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/households/4f720716-cc5c-4a4a-9d06-41de7abdb871/members",
        json={"name": "Alex"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Household not found"}


@pytest.mark.usefixtures("household_repository")
def test_update_member_food_profile_and_retrieve_it(client: TestClient) -> None:
    create_response = client.post(
        "/api/households",
        json={"name": "My Household", "members": [{"name": "Alex"}]},
    )
    household_id = create_response.json()["householdId"]
    person_id = create_response.json()["members"][0]["personId"]

    update_response = client.put(
        f"/api/households/{household_id}/members/{person_id}/food-profile",
        json={
            "allergies": ["peanuts"],
            "prohibitedFoods": ["pork"],
            "dietaryRestrictions": ["vegetarian"],
            "dislikes": ["mushrooms"],
            "preferredFoods": ["lentils"],
            "spiceLevel": "medium",
            "texturePreferences": ["firm"],
            "cuisinePreferences": ["Indian"],
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["allergies"] == ["peanuts"]
    assert update_response.json()["dietaryRestrictions"] == ["vegetarian"]
    assert update_response.json()["dislikes"] == ["mushrooms"]
    assert update_response.json()["spiceLevel"] == "medium"

    get_response = client.get(f"/api/households/{household_id}")
    member = get_response.json()["members"][0]
    assert member["personId"] == person_id
    assert member["allergies"] == ["peanuts"]
    assert member["prohibitedFoods"] == ["pork"]
    assert member["preferredFoods"] == ["lentils"]
    assert member["texturePreferences"] == ["firm"]
    assert member["cuisinePreferences"] == ["Indian"]


@pytest.mark.usefixtures("household_repository")
def test_update_member_food_profile_returns_not_found(client: TestClient) -> None:
    response = client.put(
        "/api/households/4f720716-cc5c-4a4a-9d06-41de7abdb871"
        "/members/2f720716-cc5c-4a4a-9d06-41de7abdb871/food-profile",
        json={},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Household member not found"}


@pytest.mark.usefixtures("household_repository")
def test_update_member_food_profile_rejects_invalid_spice_level(
    client: TestClient,
) -> None:
    create_response = client.post(
        "/api/households",
        json={"name": "My Household", "members": [{"name": "Alex"}]},
    )
    household_id = create_response.json()["householdId"]
    person_id = create_response.json()["members"][0]["personId"]

    response = client.put(
        f"/api/households/{household_id}/members/{person_id}/food-profile",
        json={"spiceLevel": "extreme"},
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "payload",
    [
        {"name": ""},
        {"name": "   "},
        {"name": "My Household", "members": [{"name": ""}]},
        {"name": "My Household", "unexpected": "field"},
        {"name": "My Household", "members": [{"name": "Alex", "allergies": [" "]}]},
        {"name": "My Household", "members": [{"name": "Alex", "spiceLevel": "extreme"}]},
        {
            "name": "My Household",
            "members": [
                {
                    "name": "Alex",
                    "allergies": ["peanuts"],
                    "dislikes": ["peanuts"],
                }
            ],
        },
        {
            "name": "My Household",
            "members": [
                {
                    "name": "Alex",
                    "allergies": ["peanuts"],
                    "preferredFoods": [" PEANUTS "],
                }
            ],
        },
    ],
)
def test_create_household_rejects_invalid_request(
    client: TestClient,
    payload: dict[str, object],
) -> None:
    response = client.post("/api/households", json=payload)

    assert response.status_code == 422


def test_invalid_household_request_does_not_load_database(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_database_is_loaded(request: Request) -> None:
        assert request.method == "POST"
        raise AssertionError("Database must not be loaded for invalid input")

    monkeypatch.setattr(
        households_api,
        "get_database",
        fail_if_database_is_loaded,
    )

    response = client.post("/api/households", json={"name": ""})

    assert response.status_code == 422


def test_valid_household_request_surfaces_database_configuration_failure(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def database_is_unavailable(request: Request) -> None:
        assert request.method == "POST"
        raise HTTPException(
            status_code=503,
            detail="Database configuration is unavailable",
        )

    monkeypatch.setattr(households_api, "get_database", database_is_unavailable)

    response = client.post("/api/households", json={"name": "My Household"})

    assert response.status_code == 503
    assert response.json() == {"detail": "Database configuration is unavailable"}


@pytest.mark.usefixtures("household_repository")
def test_get_household_returns_not_found(client: TestClient) -> None:
    response = client.get("/api/households/4f720716-cc5c-4a4a-9d06-41de7abdb871")

    assert response.status_code == 404
    assert response.json() == {"detail": "Household not found"}


def test_get_household_rejects_malformed_id(
    client: TestClient,
) -> None:
    response = client.get("/api/households/not-a-uuid")

    assert response.status_code == 422
