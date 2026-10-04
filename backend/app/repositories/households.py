from typing import Any
from uuid import UUID

from pymongo import ReturnDocument
from pymongo.collection import Collection
from pymongo.database import Database

from app.models.household import (
    Household,
    HouseholdCreate,
    HouseholdMember,
    HouseholdMemberCreate,
    HouseholdMemberFoodProfileUpdate,
)


def _build_member(member_data: HouseholdMemberCreate) -> HouseholdMember:
    return HouseholdMember.model_validate(member_data.model_dump(by_alias=True))


class HouseholdRepository:
    def __init__(self, database: Database[dict[str, Any]]) -> None:
        self._collection: Collection[dict[str, Any]] = database["households"]

    def create(self, household_data: HouseholdCreate) -> Household:
        household = Household(
            name=household_data.name,
            members=[_build_member(member) for member in household_data.members],
        )
        document = household.model_dump(mode="json", by_alias=True)
        document["_id"] = document.pop("householdId")
        self._collection.insert_one(document)
        return household

    def exists(self, household_id: UUID) -> bool:
        return (
            self._collection.find_one(
                {"_id": str(household_id)},
                {"_id": 1},
            )
            is not None
        )

    def add_member(
        self,
        household_id: UUID,
        member_data: HouseholdMemberCreate,
    ) -> HouseholdMember | None:
        member = _build_member(member_data)
        result = self._collection.update_one(
            {"_id": str(household_id)},
            {"$push": {"members": member.model_dump(mode="json", by_alias=True)}},
        )
        return member if result.matched_count else None

    def get_by_id(self, household_id: UUID) -> Household | None:
        document = self._collection.find_one({"_id": str(household_id)})
        if document is None:
            return None

        document["householdId"] = document.pop("_id")
        return Household.model_validate(document)

    def update_member_food_profile(
        self,
        household_id: UUID,
        person_id: UUID,
        profile: HouseholdMemberFoodProfileUpdate,
    ) -> HouseholdMember | None:
        fields = profile.model_dump(mode="json", by_alias=True)
        update = {
            f"members.$.{field_name}": value
            for field_name, value in fields.items()
        }
        document = self._collection.find_one_and_update(
            {
                "_id": str(household_id),
                "members.personId": str(person_id),
            },
            {"$set": update},
            return_document=ReturnDocument.AFTER,
        )
        if document is None:
            return None

        for member in document["members"]:
            if member["personId"] == str(person_id):
                return HouseholdMember.model_validate(member)
        return None
