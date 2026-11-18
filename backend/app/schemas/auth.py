"""Auth & user schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=120)
    role: str = Field(default="CITIZEN", pattern="^(CITIZEN|PATIENT)$",
                      description="Self-service registration is limited to CITIZEN/PATIENT; "
                                  "staff roles are provisioned by administrators.")
    phone: str | None = Field(default=None, max_length=30)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    phone: str | None = None
    created_at: datetime
    last_login_at: datetime | None = None


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class UserUpdateIn(BaseModel):
    role: str | None = Field(default=None, pattern="^(CITIZEN|PATIENT|CLINICIAN|MUNICIPAL_ADMIN|HEALTH_ADMIN|SUPER_ADMIN)$")
    is_active: bool | None = None
