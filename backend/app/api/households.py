from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.errors import PyMongoError

from app.database import MongoDatabase, get_database
from app.models.household import Household, HouseholdCreate
from app.repositories.households import HouseholdRepository

router = APIRouter(prefix="/households", tags=["households"])


def get_household_repository(
    database: Annotated[MongoDatabase, Depends(get_database)],
) -> HouseholdRepository:
    return HouseholdRepository(database.database)


@router.post(
    "",
    response_model=Household,
    status_code=status.HTTP_201_CREATED,
)
def create_household(
    household_data: HouseholdCreate,
    repository: Annotated[HouseholdRepository, Depends(get_household_repository)],
) -> Household:
    try:
        return repository.create(household_data)
    except PyMongoError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable",
        ) from None


@router.get("/{household_id}", response_model=Household)
def get_household(
    household_id: UUID,
    repository: Annotated[HouseholdRepository, Depends(get_household_repository)],
) -> Household:
    try:
        household = repository.get_by_id(household_id)
    except PyMongoError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable",
        ) from None

    if household is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Household not found",
        )
    return household
