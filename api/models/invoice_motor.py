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


class InvoiceMotor(Base):
    __tablename__ = "invoice_motors"

    invoice_id = Column(Integer, ForeignKey("invoices.invoice_id", ondelete="CASCADE"), primary_key=True)
    motor_id = Column(Integer, ForeignKey("motors.motor_id", ondelete="RESTRICT"), primary_key=True, unique=True)

    invoice = relationship("Invoice", back_populates="motor_links")
    motor = relationship("Motor", back_populates="invoice_links")

    def __repr__(self):
        return f"<InvoiceMotor(invoice_id={self.invoice_id}, motor_id={self.motor_id})>"
