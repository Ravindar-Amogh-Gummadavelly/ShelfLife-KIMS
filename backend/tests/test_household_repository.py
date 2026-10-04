from unittest.mock import MagicMock

from pymongo.collection import Collection
from pymongo.database import Database

from app.models.household import HouseholdCreate
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
