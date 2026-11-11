import re
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def _validate_phone_number(value: str) -> str:
    value = value.strip()
    digits = re.sub(r"\D", "", value)
    if not re.fullmatch(r"\+?[0-9][0-9\s().-]*", value) or not 7 <= len(digits) <= 15:
        raise ValueError("Enter a valid phone number containing 7 to 15 digits")
    return value


class ProfileCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str = Field(min_length=1, max_length=150)
    phone_number: str = Field(min_length=7, max_length=20)
    date_of_birth: date | None = None
    gender: str | None = Field(default=None, max_length=20)
    profile_image: str | None = Field(default=None, max_length=500)

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Full name cannot be blank")
        return value

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        return _validate_phone_number(value)

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, value: date | None) -> date | None:
        if value is not None and value > date.today():
            raise ValueError("Date of birth cannot be in the future")
        return value


class ProfileUpdate(ProfileCreate):
    pass


class ProfilePatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str | None = Field(default=None, min_length=1, max_length=150)
    phone_number: str | None = Field(default=None, min_length=7, max_length=20)
    date_of_birth: date | None = None
    gender: str | None = Field(default=None, max_length=20)
    profile_image: str | None = Field(default=None, max_length=500)

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("Full name cannot be blank")
        return value

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _validate_phone_number(value)

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, value: date | None) -> date | None:
        if value is not None and value > date.today():
            raise ValueError("Date of birth cannot be in the future")
        return value

    @model_validator(mode="after")
    def reject_null_required_fields(self) -> "ProfilePatch":
        for field in ("full_name", "phone_number"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self


class ProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    auth_user_id: int
    full_name: str
    phone_number: str
    date_of_birth: date | None
    gender: str | None
    profile_image: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime