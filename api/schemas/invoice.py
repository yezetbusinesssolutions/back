from pydantic import BaseModel, field_serializer
from enum import Enum
from decimal import Decimal
from datetime import datetime
from typing import Optional


class PaymentMethod(str, Enum):
    CASH = "CASH"
    CARD = "CARD"
    FINANCING = "FINANCING"
    BANK_TRANSFER = "BANK_TRANSFER"


class InvoiceStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    VOIDED = "VOIDED"


class InvoiceBase(BaseModel):
    invoice_no: str | None = None
    customer_name: str
    customer_id_number: str | None = None
    customer_id_type: str | None = None
    customer_id_issue_date: str | None = None
    customer_id_expiry_date: str | None = None
    customer_id_authority: str | None = None
    customer_phone: str
    customer_alt_phone: str | None = None
    customer_email: str | None = None
    customer_region: str | None = None
    customer_city: str | None = None
    customer_sub_city: str | None = None
    customer_woreda: str | None = None
    customer_house_number: str | None = None
    payment_method: PaymentMethod
    subtotal: Decimal
    tax: Decimal
    total: Decimal
    site_id: int


class InvoiceCreate(InvoiceBase):
    motor_ids: list[int]
    payment_proof_path: str | None = None


class InvoiceUpdate(BaseModel):
    status: InvoiceStatus | None = None
    rejection_reason: str | None = None


class InvoiceApproval(BaseModel):
    approve: bool
    rejection_reason: str | None = None


class InvoiceResponse(InvoiceBase):
    invoice_id: int
    sold_at: datetime
    status: str
    sold_by_name: str | None = None
    site_name: str | None = None
    motor_count: int | None = None
    motor_links: list[dict] | None = None
    payment_proof_path: str | None = None

    class Config:
        from_attributes = True

    @field_serializer('status')
    def serialize_status(self, value) -> str:
        if hasattr(value, 'value'):
            return value.value
        return value

    @field_serializer('payment_method')
    def serialize_payment_method(self, value) -> str:
        if hasattr(value, 'value'):
            return value.value
        return value