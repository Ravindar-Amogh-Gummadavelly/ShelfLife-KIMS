from typing import Annotated
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

NonEmptyName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=120),
]


class HouseholdMemberCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: NonEmptyName
    age_category: str | None = Field(default=None, alias="ageCategory")
    constraints: list[str] = Field(default_factory=list)
    preferences: list[str] = Field(default_factory=list)
    texture: str | None = None
    spice_level: str | None = Field(default=None, alias="spiceLevel")


class HouseholdCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: NonEmptyName
    members: list[HouseholdMemberCreate] = Field(default_factory=list)


class HouseholdMember(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    person_id: UUID = Field(default_factory=uuid4, alias="personId")
    name: NonEmptyName
    age_category: str | None = Field(default=None, alias="ageCategory")
    constraints: list[str] = Field(default_factory=list)
    preferences: list[str] = Field(default_factory=list)
    texture: str | None = None
    spice_level: str | None = Field(default=None, alias="spiceLevel")


class Household(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    household_id: UUID = Field(default_factory=uuid4, alias="householdId")
    name: NonEmptyName
    members: list[HouseholdMember] = Field(default_factory=list)
