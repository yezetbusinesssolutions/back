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

class UserRole(str, enum.Enum):
    RECEIVER = "RECEIVER"
    ASSEMBLER = "ASSEMBLER"
    SALES_REP = "SALES_REP"
    ADMIN = "ADMIN"


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(SQLAEnum(UserRole), nullable=False)
    assigned_site_id = Column(Integer, ForeignKey("sites.site_id"), nullable=True)
    password_hash = Column(String(255), nullable=False)

    assigned_site = relationship("Site", back_populates="users")
    deliveries_received = relationship("Delivery", back_populates="receiver")
    motors_received = relationship("Motor", foreign_keys="Motor.received_by", back_populates="receiver")
    motors_assembled = relationship("Motor", foreign_keys="Motor.assembled_by", back_populates="assembler")
    transfers_initiated = relationship("SiteTransferHistory", back_populates="transferred_by_user")
    invoices_sold = relationship("Invoice", foreign_keys="Invoice.sold_by", back_populates="seller")
    invoices_approved = relationship("Invoice", foreign_keys="Invoice.approved_by", back_populates="approver")

    def __repr__(self):
        return f"<User(id={self.user_id}, username={self.username}, role={self.role})>"
