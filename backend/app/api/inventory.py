from collections.abc import Callable
from typing import Annotated, NoReturn
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pymongo.errors import PyMongoError

from app.database import get_database
from app.models.inventory import (
    ConsumptionCreate,
    InventoryCreate,
    InventoryItem,
    InventoryUpdate,
)
from app.repositories.households import HouseholdRepository
from app.repositories.inventory import (
    InsufficientInventoryQuantity,
    InventoryRepository,
)

router = APIRouter(
    prefix="/households/{household_id}/inventory",
    tags=["inventory"],
)


def get_inventory_repository(
    request: Request,
) -> Callable[[], InventoryRepository]:
    def build_repository() -> InventoryRepository:
        database = get_database(request)
        database.ensure_inventory_indexes()
        return InventoryRepository(database.database)

    return build_repository


def get_household_repository(
    request: Request,
) -> Callable[[], HouseholdRepository]:
    return lambda: HouseholdRepository(get_database(request).database)


def _raise_database_unavailable() -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Database is unavailable",
    ) from None


@router.post(
    "",
    response_model=InventoryItem,
    status_code=status.HTTP_201_CREATED,
)
def create_inventory_item(
    household_id: UUID,
    item_data: InventoryCreate,
    inventory_repository_factory: Annotated[
        Callable[[], InventoryRepository],
        Depends(get_inventory_repository),
    ],
    household_repository_factory: Annotated[
        Callable[[], HouseholdRepository],
        Depends(get_household_repository),
    ],
) -> InventoryItem:
    try:
        if not household_repository_factory().exists(household_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Household not found",
            )
        return inventory_repository_factory().create(household_id, item_data)
    except PyMongoError:
        _raise_database_unavailable()


@router.get("", response_model=list[InventoryItem])
def get_inventory(
    household_id: UUID,
    inventory_repository_factory: Annotated[
        Callable[[], InventoryRepository],
        Depends(get_inventory_repository),
    ],
    household_repository_factory: Annotated[
        Callable[[], HouseholdRepository],
        Depends(get_household_repository),
    ],
) -> list[InventoryItem]:
    try:
        if not household_repository_factory().exists(household_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Household not found",
            )
        return inventory_repository_factory().list_for_household(household_id)
    except PyMongoError:
        _raise_database_unavailable()


@router.put("/{inventory_id}", response_model=InventoryItem)
def update_inventory_item(
    household_id: UUID,
    inventory_id: UUID,
    item_data: InventoryUpdate,
    inventory_repository_factory: Annotated[
        Callable[[], InventoryRepository],
        Depends(get_inventory_repository),
    ],
) -> InventoryItem:
    try:
        item = inventory_repository_factory().update(
            household_id,
            inventory_id,
            item_data,
        )
    except PyMongoError:
        _raise_database_unavailable()

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found",
        )
    return item


@router.delete("/{inventory_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inventory_item(
    household_id: UUID,
    inventory_id: UUID,
    inventory_repository_factory: Annotated[
        Callable[[], InventoryRepository],
        Depends(get_inventory_repository),
    ],
) -> Response:
    try:
        deleted = inventory_repository_factory().delete(household_id, inventory_id)
    except PyMongoError:
        _raise_database_unavailable()

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{inventory_id}/consumption", response_model=InventoryItem)
def consume_inventory_item(
    household_id: UUID,
    inventory_id: UUID,
    consumption: ConsumptionCreate,
    inventory_repository_factory: Annotated[
        Callable[[], InventoryRepository],
        Depends(get_inventory_repository),
    ],
) -> InventoryItem:
    try:
        item = inventory_repository_factory().consume(
            household_id,
            inventory_id,
            consumption,
        )
    except InsufficientInventoryQuantity:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Consumption quantity exceeds the remaining inventory",
        ) from None
    except PyMongoError:
        _raise_database_unavailable()

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found",
        )
    return item
