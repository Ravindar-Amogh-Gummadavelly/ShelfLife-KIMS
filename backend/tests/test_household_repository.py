from unittest.mock import MagicMock
from uuid import UUID

from pymongo import ReturnDocument
from pymongo.collection import Collection
from pymongo.database import Database

from app.models.household import (
    HouseholdCreate,
    HouseholdMemberCreate,
    HouseholdMemberFoodProfileUpdate,
)
from app.repositories.households import HouseholdRepository


def test_repository_persists_household_and_retrieves_it() -> None:
    collection = MagicMock(spec=Collection)
    database = MagicMock(spec=Database)
    database.__getitem__.return_value = collection
    repository = HouseholdRepository(database)

    household = repository.create(
        HouseholdCreate(
            name="My Household",
            members=[
                {
                    "name": "Alex",
                    "ageCategory": "adult",
                    "constraints": ["vegetarian"],
                    "preferences": ["Indian"],
                }
            ],
        )
    )

    stored_document = collection.insert_one.call_args.args[0]
    assert stored_document["_id"] == str(household.household_id)
    assert "householdId" not in stored_document
    assert stored_document["members"][0]["personId"] == str(
        household.members[0].person_id
    )

    collection.find_one.return_value = stored_document.copy()
    retrieved = repository.get_by_id(household.household_id)

    collection.find_one.assert_called_once_with(
        {"_id": str(household.household_id)}
    )
    assert retrieved == household


def test_repository_adds_member_to_existing_household() -> None:
    collection = MagicMock(spec=Collection)
    collection.update_one.return_value.matched_count = 1
    database = MagicMock(spec=Database)
    database.__getitem__.return_value = collection
    repository = HouseholdRepository(database)
    household_id = UUID("4f720716-cc5c-4a4a-9d06-41de7abdb871")

    member = repository.add_member(
        household_id,
        HouseholdMemberCreate(
            name="Alex",
            allergies=["peanuts"],
            dietaryRestrictions=["vegetarian"],
            preferredFoods=["lentils"],
        ),
    )

    collection.update_one.assert_called_once()
    query, update = collection.update_one.call_args.args
    assert query == {"_id": str(household_id)}
    assert update["$push"]["members"]["name"] == "Alex"
    assert update["$push"]["members"]["allergies"] == ["peanuts"]
    assert update["$push"]["members"]["dietaryRestrictions"] == ["vegetarian"]
    assert member is not None
    assert UUID(update["$push"]["members"]["personId"]) == member.person_id


def test_repository_updates_member_food_profile() -> None:
    collection = MagicMock(spec=Collection)
    database = MagicMock(spec=Database)
    database.__getitem__.return_value = collection
    repository = HouseholdRepository(database)
    household_id = UUID("4f720716-cc5c-4a4a-9d06-41de7abdb871")
    person_id = UUID("2f720716-cc5c-4a4a-9d06-41de7abdb871")
    collection.find_one_and_update.return_value = {
        "_id": str(household_id),
        "name": "My Household",
        "members": [
            {
                "personId": str(person_id),
                "name": "Alex",
                "allergies": ["peanuts"],
                "prohibitedFoods": [],
                "dietaryRestrictions": ["vegetarian"],
                "dislikes": [],
                "preferredFoods": ["lentils"],
                "spiceLevel": "low",
                "texturePreferences": [],
                "cuisinePreferences": [],
            }
        ],
    }

    member = repository.update_member_food_profile(
        household_id,
        person_id,
        HouseholdMemberFoodProfileUpdate(
            allergies=["peanuts"],
            dietaryRestrictions=["vegetarian"],
            preferredFoods=["lentils"],
            spiceLevel="low",
        ),
    )

    collection.find_one_and_update.assert_called_once()
    query, update = collection.find_one_and_update.call_args.args
    assert query == {
        "_id": str(household_id),
        "members.personId": str(person_id),
    }
    assert update["$set"]["members.$.allergies"] == ["peanuts"]
    assert update["$set"]["members.$.dietaryRestrictions"] == ["vegetarian"]
    assert update["$set"]["members.$.preferredFoods"] == ["lentils"]
    assert member is not None
    assert member.person_id == person_id
    assert member.allergies == ["peanuts"]
    assert collection.find_one_and_update.call_args.kwargs["return_document"] == (
        ReturnDocument.AFTER
    )
