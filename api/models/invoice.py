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

class PaymentMethod(str, enum.Enum):
    CASH = "CASH"
    CARD = "CARD"
    FINANCING = "FINANCING"
    BANK_TRANSFER = "BANK_TRANSFER"


class InvoiceStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    VOIDED = "VOIDED"


class Invoice(Base):
    __tablename__ = "invoices"

    invoice_id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_no = Column(String(50), unique=True, nullable=False)
    
    # Customer identification - must match government ID
    customer_name = Column(String(200), nullable=False)
    customer_id_number = Column(String(100), nullable=True)
    customer_id_type = Column(String(50), nullable=True)
    customer_id_issue_date = Column(String(20), nullable=True)
    customer_id_expiry_date = Column(String(20), nullable=True)
    customer_id_authority = Column(String(100), nullable=True)
    
    # Contact details
    customer_phone = Column(String(20), nullable=False)
    customer_alt_phone = Column(String(20), nullable=True)
    customer_email = Column(String(100), nullable=True)
    
    # Physical address
    customer_region = Column(String(100), nullable=True)
    customer_city = Column(String(100), nullable=True)
    customer_sub_city = Column(String(100), nullable=True)
    customer_woreda = Column(String(100), nullable=True)
    customer_house_number = Column(String(50), nullable=True)
    
    payment_method = Column(SQLAEnum(PaymentMethod), nullable=False)

    subtotal = Column(Numeric(10, 2), nullable=False)
    tax = Column(Numeric(10, 2), nullable=False)
    total = Column(Numeric(10, 2), nullable=False)

    sold_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    sold_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    site_id = Column(Integer, ForeignKey("sites.site_id"), nullable=False)

    status = Column(SQLAEnum(InvoiceStatus), nullable=False, default=InvoiceStatus.PENDING_APPROVAL)
    payment_proof_path = Column(String(500), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    rejection_reason = Column(Text, nullable=True)

    seller = relationship("User", foreign_keys=[sold_by], back_populates="invoices_sold")
    approver = relationship("User", foreign_keys=[approved_by], back_populates="invoices_approved")
    site = relationship("Site", back_populates="invoices")
    motor_links = relationship("InvoiceMotor", back_populates="invoice", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Invoice(id={self.invoice_id}, no={self.invoice_no}, status={self.status}, total={self.total})>"