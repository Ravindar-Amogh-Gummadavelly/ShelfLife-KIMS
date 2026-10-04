from datetime import date
from typing import Any
from uuid import UUID

from pymongo import ReturnDocument
from pymongo.collection import Collection
from pymongo.database import Database

from app.models.inventory import (
    ConsumptionCreate,
    ConsumptionRecord,
    InventoryCreate,
    InventoryItem,
    InventoryUpdate,
)


class InsufficientInventoryQuantity(ValueError):
    pass


class InventoryRepository:
    def __init__(self, database: Database[dict[str, Any]]) -> None:
        self._collection: Collection[dict[str, Any]] = database["inventory_items"]

    def create(
        self,
        household_id: UUID,
        item_data: InventoryCreate,
    ) -> InventoryItem:
        item = InventoryItem(
            household_id=household_id,
            **item_data.model_dump(),
        )
        document = item.model_dump(
            mode="json",
            by_alias=True,
            exclude={"status"},
        )
        document["_id"] = document.pop("inventoryId")
        self._collection.insert_one(document)
        return item

    def get_by_id(
        self,
        household_id: UUID,
        inventory_id: UUID,
    ) -> InventoryItem | None:
        document = self._collection.find_one(
            {
                "_id": str(inventory_id),
                "householdId": str(household_id),
            }
        )
        if document is None:
            return None

        document["inventoryId"] = document.pop("_id")
        return InventoryItem.model_validate(document)

    def list_for_household(self, household_id: UUID) -> list[InventoryItem]:
        documents = self._collection.find({"householdId": str(household_id)})
        items: list[InventoryItem] = []
        for document in documents:
            document["inventoryId"] = document.pop("_id")
            items.append(InventoryItem.model_validate(document))
        return sorted(
            items,
            key=lambda item: (
                item.expiry_date or date.max,
                item.ingredient.casefold(),
            ),
        )

    def update(
        self,
        household_id: UUID,
        inventory_id: UUID,
        item_data: InventoryUpdate,
    ) -> InventoryItem | None:
        document = self._collection.find_one_and_update(
            {
                "_id": str(inventory_id),
                "householdId": str(household_id),
            },
            {"$set": item_data.model_dump(mode="json", by_alias=True)},
            return_document=ReturnDocument.AFTER,
        )
        if document is None:
            return None

        document["inventoryId"] = document.pop("_id")
        return InventoryItem.model_validate(document)

    def delete(self, household_id: UUID, inventory_id: UUID) -> bool:
        result = self._collection.delete_one(
            {
                "_id": str(inventory_id),
                "householdId": str(household_id),
            }
        )
        return result.deleted_count > 0

    def consume(
        self,
        household_id: UUID,
        inventory_id: UUID,
        consumption: ConsumptionCreate,
    ) -> InventoryItem | None:
        record = ConsumptionRecord(quantity=consumption.quantity)
        result = self._collection.update_one(
            {
                "_id": str(inventory_id),
                "householdId": str(household_id),
                "quantity": {"$gte": consumption.quantity},
            },
            {
                "$inc": {"quantity": -consumption.quantity},
                "$push": {
                    "consumptionHistory": record.model_dump(
                        mode="json",
                        by_alias=True,
                    )
                },
            },
        )
        if result.matched_count:
            return self.get_by_id(household_id, inventory_id)

        item = self.get_by_id(household_id, inventory_id)
        if item is not None:
            raise InsufficientInventoryQuantity(
                "Consumption quantity exceeds the remaining inventory"
            )
        return None
