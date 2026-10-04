from datetime import date, datetime, timezone
from enum import StrEnum
from typing import Annotated, Self
from uuid import UUID, uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    computed_field,
    model_validator,
)

InventoryLabel = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=120),
]
InventoryCategory = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=60),
]
InventoryUnit = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=30),
]
PositiveQuantity = Annotated[float, Field(gt=0, allow_inf_nan=False)]
RemainingQuantity = Annotated[float, Field(ge=0, allow_inf_nan=False)]
InventoryNotes = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=500),
]


class InventoryStatus(StrEnum):
    FRESH = "FRESH"
    USE_SOON = "USE_SOON"
    EXPIRING = "EXPIRING"
    EXPIRED = "EXPIRED"


class InventoryValues(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    ingredient: InventoryLabel
    category: InventoryCategory
    unit: InventoryUnit
    purchase_date: date | None = Field(default=None, alias="purchaseDate")
    expiry_date: date | None = Field(default=None, alias="expiryDate")
    storage: InventoryLabel | None = None
    notes: InventoryNotes | None = None

    @model_validator(mode="after")
    def validate_item_dates(self) -> Self:
        if (
            self.purchase_date is not None
            and self.expiry_date is not None
            and self.expiry_date < self.purchase_date
        ):
            raise ValueError("Expiry date cannot be before purchase date")
        return self


class InventoryCreate(InventoryValues):
    quantity: PositiveQuantity


class InventoryUpdate(InventoryCreate):
    pass


class ConsumptionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quantity: PositiveQuantity


class ConsumptionRecord(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    quantity: PositiveQuantity
    consumed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        alias="consumedAt",
    )


def determine_inventory_status(
    expiry_date: date | None,
    *,
    today: date | None = None,
) -> InventoryStatus:
    if expiry_date is None:
        return InventoryStatus.FRESH

    days_until_expiry = (expiry_date - (today or date.today())).days
    if days_until_expiry < 0:
        return InventoryStatus.EXPIRED
    if days_until_expiry <= 3:
        return InventoryStatus.EXPIRING
    if days_until_expiry <= 7:
        return InventoryStatus.USE_SOON
    return InventoryStatus.FRESH


class InventoryItem(InventoryValues):
    inventory_id: UUID = Field(default_factory=uuid4, alias="inventoryId")
    household_id: UUID = Field(alias="householdId")
    quantity: RemainingQuantity
    consumption_history: list[ConsumptionRecord] = Field(
        default_factory=list,
        alias="consumptionHistory",
    )

    @computed_field
    @property
    def status(self) -> InventoryStatus:
        return determine_inventory_status(self.expiry_date)
