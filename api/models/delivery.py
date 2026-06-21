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


class Delivery(Base):
    __tablename__ = "deliveries"

    delivery_id = Column(Integer, primary_key=True, autoincrement=True)
    delivery_no = Column(String(50), unique=True, nullable=False)
    supplier_name = Column(String(100), nullable=True)
    received_at_site_id = Column(Integer, ForeignKey("sites.site_id"), nullable=False)
    received_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    received_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    notes = Column(Text, nullable=True)

    site = relationship("Site", back_populates="deliveries")
    receiver = relationship("User", back_populates="deliveries_received")
    motors = relationship("Motor", back_populates="delivery")

    def __repr__(self):
        return f"<Delivery(id={self.delivery_id}, no={self.delivery_no}, site_id={self.received_at_site_id})>"
