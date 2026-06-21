from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, ForeignKey, DateTime, 
    Numeric, Enum as SQLAEnum, UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from api.database import Base
import enum

class TransferReason(str, enum.Enum):
    RECEIVED = "RECEIVED"
    ASSEMBLY_COMPLETE = "ASSEMBLY_COMPLETE"
    STOCK_MOVE = "STOCK_MOVE"
    RETURN_DEFECTIVE = "RETURN_DEFECTIVE"
    SALE_TRANSFER = "SALE_TRANSFER"


class SiteTransferHistory(Base):
    __tablename__ = "site_transfer_history"

    transfer_id = Column(Integer, primary_key=True, autoincrement=True)
    motor_id = Column(Integer, ForeignKey("motors.motor_id", ondelete="CASCADE"), nullable=False)
    from_site_id = Column(Integer, ForeignKey("sites.site_id"), nullable=True)
    to_site_id = Column(Integer, ForeignKey("sites.site_id"), nullable=True)
    transferred_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    transferred_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    reason = Column(SQLAEnum(TransferReason), nullable=False)

    motor = relationship("Motor", back_populates="transfer_history")
    from_site = relationship("Site", foreign_keys=[from_site_id])
    to_site = relationship("Site", foreign_keys=[to_site_id])
    transferred_by_user = relationship("User", back_populates="transfers_initiated")

    def __repr__(self):
        return f"<Transfer(id={self.transfer_id}, motor={self.motor_id}, reason={self.reason})>"
