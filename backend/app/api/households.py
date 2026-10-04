from collections.abc import Callable
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pymongo.errors import PyMongoError

from app.database import get_database
from app.models.household import (
    Household,
    HouseholdCreate,
    HouseholdMember,
    HouseholdMemberCreate,
    HouseholdMemberFoodProfileUpdate,
)
from app.repositories.households import HouseholdRepository

router = APIRouter(prefix="/households", tags=["households"])


def get_household_repository(
    request: Request,
) -> Callable[[], HouseholdRepository]:
    return lambda: HouseholdRepository(get_database(request).database)


@router.post(
    "",
    response_model=Household,
    status_code=status.HTTP_201_CREATED,
)
def create_household(
    household_data: HouseholdCreate,
    repository_factory: Annotated[
        Callable[[], HouseholdRepository],
        Depends(get_household_repository),
    ],
) -> Household:
    try:
        repository = repository_factory()
        return repository.create(household_data)
    except PyMongoError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable",
        ) from None


@router.get("/{household_id}", response_model=Household)
def get_household(
    household_id: UUID,
    repository_factory: Annotated[
        Callable[[], HouseholdRepository],
        Depends(get_household_repository),
    ],
) -> Household:
    try:
        repository = repository_factory()
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


@router.post(
    "/{household_id}/members",
    response_model=HouseholdMember,
    status_code=status.HTTP_201_CREATED,
)
def add_household_member(
    household_id: UUID,
    member_data: HouseholdMemberCreate,
    repository_factory: Annotated[
        Callable[[], HouseholdRepository],
        Depends(get_household_repository),
    ],
) -> HouseholdMember:
    try:
        repository = repository_factory()
        member = repository.add_member(household_id, member_data)
    except PyMongoError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable",
        ) from None

    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Household not found",
        )
    return member


@router.put(
    "/{household_id}/members/{person_id}/food-profile",
    response_model=HouseholdMember,
)
def update_household_member_food_profile(
    household_id: UUID,
    person_id: UUID,
    profile: HouseholdMemberFoodProfileUpdate,
    repository_factory: Annotated[
        Callable[[], HouseholdRepository],
        Depends(get_household_repository),
    ],
) -> HouseholdMember:
    try:
        repository = repository_factory()
        member = repository.update_member_food_profile(
            household_id,
            person_id,
            profile,
        )
    except PyMongoError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable",
        ) from None

    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Household member not found",
        )
    return member
