from enum import StrEnum
from typing import Annotated, Self
from uuid import UUID, uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

NonEmptyName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=120),
]
FoodLabel = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=80),
]


class SpiceLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


def normalize_food_labels(values: list[str]) -> list[str]:
    unique_values: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = value.strip()
        key = normalized.casefold()
        if key not in seen:
            seen.add(key)
            unique_values.append(normalized)
    return unique_values


def validate_food_category_separation(
    hard_values: list[str],
    soft_values: list[str],
) -> None:
    hard_labels = {value.casefold() for value in hard_values}
    overlap = hard_labels.intersection(value.casefold() for value in soft_values)
    if overlap:
        raise ValueError("A food cannot be both a hard constraint and a preference")


class MemberFoodProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    allergies: list[FoodLabel] = Field(default_factory=list)
    prohibited_foods: list[FoodLabel] = Field(default_factory=list, alias="prohibitedFoods")
    dietary_restrictions: list[FoodLabel] = Field(
        default_factory=list,
        alias="dietaryRestrictions",
    )
    dislikes: list[FoodLabel] = Field(default_factory=list)
    preferred_foods: list[FoodLabel] = Field(default_factory=list, alias="preferredFoods")
    texture_preferences: list[FoodLabel] = Field(
        default_factory=list,
        alias="texturePreferences",
    )
    cuisine_preferences: list[FoodLabel] = Field(
        default_factory=list,
        alias="cuisinePreferences",
    )
    spice_level: SpiceLevel | None = Field(default=None, alias="spiceLevel")

    @field_validator(
        "allergies",
        "prohibited_foods",
        "dietary_restrictions",
        "dislikes",
        "preferred_foods",
        "texture_preferences",
        "cuisine_preferences",
    )
    @classmethod
    def normalize_label_lists(cls, values: list[str]) -> list[str]:
        return normalize_food_labels(values)

    @model_validator(mode="after")
    def validate_constraint_preference_separation(self) -> Self:
        validate_food_category_separation(
            [
                *self.allergies,
                *self.prohibited_foods,
                *self.dietary_restrictions,
            ],
            [
                *self.dislikes,
                *self.preferred_foods,
                *self.texture_preferences,
                *self.cuisine_preferences,
            ],
        )
        return self


class HouseholdMemberCreate(MemberFoodProfile):
    name: NonEmptyName
    age_category: FoodLabel | None = Field(default=None, alias="ageCategory")
    constraints: list[FoodLabel] = Field(default_factory=list)
    preferences: list[FoodLabel] = Field(default_factory=list)
    texture: FoodLabel | None = None

    @field_validator("constraints", "preferences")
    @classmethod
    def normalize_legacy_label_lists(cls, values: list[str]) -> list[str]:
        return normalize_food_labels(values)


class HouseholdCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: NonEmptyName
    members: list[HouseholdMemberCreate] = Field(default_factory=list)


class HouseholdMember(HouseholdMemberCreate):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    person_id: UUID = Field(default_factory=uuid4, alias="personId")


class HouseholdMemberFoodProfileUpdate(MemberFoodProfile):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class HouseholdMemberHardConstraints(BaseModel):
    allergies: list[str]
    prohibited_foods: list[str]
    dietary_restrictions: list[str]
    legacy_constraints: list[str]


class HouseholdMemberSoftPreferences(BaseModel):
    dislikes: list[str]
    preferred_foods: list[str]
    spice_level: SpiceLevel | None
    texture_preferences: list[str]
    cuisine_preferences: list[str]
    legacy_preferences: list[str]
    legacy_texture: str | None


class HouseholdMemberClassification(BaseModel):
    hard_constraints: HouseholdMemberHardConstraints
    soft_preferences: HouseholdMemberSoftPreferences


class Household(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    household_id: UUID = Field(default_factory=uuid4, alias="householdId")
    name: NonEmptyName
    members: list[HouseholdMember] = Field(default_factory=list)
