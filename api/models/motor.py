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

class MotorStatus(str, enum.Enum):
    RECEIVED = "RECEIVED"
    IN_PROGRESS = "IN_PROGRESS"
    READY_FOR_SALE = "READY_FOR_SALE"
    RESERVED = "RESERVED"
    SOLD = "SOLD"
    DEFECTIVE = "DEFECTIVE"


class Motor(Base):
    __tablename__ = "motors"

    motor_id = Column(Integer, primary_key=True, autoincrement=True)
    serial_number = Column(String(100), unique=True, nullable=False)
    model_name = Column(String(100), nullable=False)
    color = Column(String(50), nullable=True)

    status = Column(SQLAEnum(MotorStatus), nullable=False, default=MotorStatus.RECEIVED)

    current_site_id = Column(Integer, ForeignKey("sites.site_id"), nullable=False)
    delivery_id = Column(Integer, ForeignKey("deliveries.delivery_id"), nullable=True)

    received_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    received_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)

    assembly_started = Column(DateTime(timezone=True), nullable=True)
    assembled_at = Column(DateTime(timezone=True), nullable=True)
    assembled_by = Column(Integer, ForeignKey("users.user_id"), nullable=True)

    quality_check_passed = Column(Boolean, nullable=True, default=None)
    defect_reason = Column(Text, nullable=True)

    current_site = relationship("Site", back_populates="motors")
    delivery = relationship("Delivery", back_populates="motors")
    receiver = relationship("User", foreign_keys=[received_by], back_populates="motors_received")
    assembler = relationship("User", foreign_keys=[assembled_by], back_populates="motors_assembled")

    transfer_history = relationship("SiteTransferHistory", back_populates="motor", cascade="all, delete-orphan")
    invoice_links = relationship("InvoiceMotor", back_populates="motor", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Motor(id={self.motor_id}, serial={self.serial_number}, status={self.status})>"