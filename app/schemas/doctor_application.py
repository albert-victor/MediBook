"""Public doctor application form schema."""

import re
from typing import Self

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.schemas.auth import PASSWORD_MIN_LENGTH, PHONE_PATTERN


class DoctorApplicationForm(BaseModel):
    first_name: str = Field(min_length=2, max_length=100)
    last_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=20)
    password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=128)
    confirm_password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=128)
    specialization_id: int
    license_number: str = Field(min_length=3, max_length=60)
    hospital_name: str = Field(min_length=2, max_length=200)
    consultation_fee: float = Field(ge=0)
    experience_years: int = Field(default=0, ge=0)
    qualification: str | None = Field(default=None, max_length=200)
    terms_accepted: bool = False

    @field_validator("first_name", "last_name", "hospital_name", "license_number")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        if value is None or value.strip() == "":
            return None
        cleaned = value.strip()
        if not PHONE_PATTERN.match(cleaned):
            raise ValueError("Enter a valid phone number")
        return cleaned

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", value):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", value):
            raise ValueError("Password must contain at least one number")
        return value

    @model_validator(mode="after")
    def passwords_and_terms(self) -> Self:
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        if not self.terms_accepted:
            raise ValueError("You must accept the terms and conditions")
        return self
