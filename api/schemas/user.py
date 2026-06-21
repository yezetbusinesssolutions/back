from pydantic import BaseModel, field_serializer
from enum import Enum


class UserRole(str, Enum):
    RECEIVER = "RECEIVER"
    ASSEMBLER = "ASSEMBLER"
    SALES_REP = "SALES_REP"
    ADMIN = "ADMIN"


class UserBase(BaseModel):
    username: str
    full_name: str
    role: str
    assigned_site_id: int | None = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    username: str | None = None
    full_name: str | None = None
    role: UserRole | None = None
    assigned_site_id: int | None = None
    password: str | None = None


class UserResponse(UserBase):
    user_id: int

    class Config:
        from_attributes = True

    @field_serializer('role')
    def serialize_role(self, value) -> str:
        if hasattr(value, 'value'):
            return value.value
        return value
