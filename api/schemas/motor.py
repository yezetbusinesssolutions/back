from pydantic import BaseModel, ConfigDict, field_serializer
from enum import Enum
from datetime import datetime


class MotorStatus(str, Enum):
    RECEIVED = "RECEIVED"
    IN_PROGRESS = "IN_PROGRESS"
    READY_FOR_SALE = "READY_FOR_SALE"
    RESERVED = "RESERVED"
    SOLD = "SOLD"
    DEFECTIVE = "DEFECTIVE"


class MotorBase(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    serial_number: str
    model_name: str
    color: str | None = None
    current_site_id: int
    delivery_id: int | None = None


class MotorCreate(MotorBase):
    delivery_no: str | None = None


class MotorUpdate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    model_name: str | None = None
    color: str | None = None
    status: MotorStatus | None = None
    current_site_id: int | None = None
    assembled_by: int | None = None
    quality_check_passed: bool | None = None
    defect_reason: str | None = None


class MotorResponse(MotorBase):
    motor_id: int
    status: str
    received_at: datetime
    received_by: int
    assembly_started: datetime | None = None
    assembled_at: datetime | None = None
    assembled_by: int | None = None
    quality_check_passed: bool | None = None
    defect_reason: str | None = None

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    @field_serializer('status')
    def serialize_status(self, value) -> str:
        if hasattr(value, 'value'):
            return value.value
        return value