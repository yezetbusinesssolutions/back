from pydantic import BaseModel
from datetime import datetime


class DeliveryBase(BaseModel):
    delivery_no: str
    supplier_name: str | None = None
    received_at_site_id: int
    notes: str | None = None


class DeliveryCreate(DeliveryBase):
    pass


class DeliveryResponse(DeliveryBase):
    delivery_id: int
    received_at: datetime
    received_by: int

    class Config:
        from_attributes = True
