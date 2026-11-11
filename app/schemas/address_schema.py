from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.user_schema import _validate_phone_number


class AddressFields(BaseModel):
    address_type: Literal["Home", "Office", "Other"]
    full_name: str = Field(min_length=1, max_length=150)
    phone_number: str = Field(min_length=7, max_length=20)
    address_line_1: str = Field(min_length=1, max_length=255)
    address_line_2: str | None = Field(default=None, max_length=255)
    city: str = Field(min_length=1, max_length=100)
    state: str = Field(min_length=1, max_length=100)
    country: str = Field(min_length=1, max_length=100)
    postal_code: str = Field(min_length=1, max_length=20)

    @field_validator(
        "full_name",
        "address_line_1",
        "address_line_2",
        "city",
        "state",
        "country",
        "postal_code",
    )
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank")
        return value

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        return _validate_phone_number(value)


class AddressCreate(AddressFields):
    model_config = ConfigDict(extra="forbid")

    is_default: bool = False


class AddressUpdate(AddressFields):
    model_config = ConfigDict(extra="forbid")

    is_default: bool = False


class AddressRead(AddressFields):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    is_default: bool
    created_at: datetime