from pydantic import BaseModel, field_serializer
from enum import Enum
from datetime import datetime


class TransferReason(str, Enum):
    RECEIVED = "RECEIVED"
    ASSEMBLY_COMPLETE = "ASSEMBLY_COMPLETE"
    STOCK_MOVE = "STOCK_MOVE"
    RETURN_DEFECTIVE = "RETURN_DEFECTIVE"
    SALE_TRANSFER = "SALE_TRANSFER"


class SiteTransferHistoryBase(BaseModel):
    motor_id: int
    from_site_id: int | None = None
    to_site_id: int | None = None
    transferred_by: int
    reason: str


class SiteTransferHistoryCreate(SiteTransferHistoryBase):
    pass


class SiteTransferHistoryResponse(SiteTransferHistoryBase):
    transfer_id: int
    transferred_at: datetime

    class Config:
        from_attributes = True

    @field_serializer('reason')
    def serialize_reason(self, value) -> str:
        if hasattr(value, 'value'):
            return value.value
        return value
