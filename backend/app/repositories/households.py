from typing import Any
from uuid import UUID

from pymongo.collection import Collection
from pymongo.database import Database

from app.models.household import Household, HouseholdCreate, HouseholdMember


class HouseholdRepository:
    def __init__(self, database: Database[dict[str, Any]]) -> None:
        self._collection: Collection[dict[str, Any]] = database["households"]

    def create(self, household_data: HouseholdCreate) -> Household:
        household = Household(
            name=household_data.name,
            members=[
                HouseholdMember.model_validate(member.model_dump(by_alias=True))
                for member in household_data.members
            ],
        )
        document = household.model_dump(mode="json", by_alias=True)
        document["_id"] = document.pop("householdId")
        self._collection.insert_one(document)
        return household

    def get_by_id(self, household_id: UUID) -> Household | None:
        document = self._collection.find_one({"_id": str(household_id)})
        if document is None:
            return None

        document["householdId"] = document.pop("_id")
        return Household.model_validate(document)
