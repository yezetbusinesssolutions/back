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

class SiteType(str, enum.Enum):
    WAREHOUSE = "WAREHOUSE"
    SHOWROOM = "SHOWROOM"
    ASSEMBLY_PLANT = "ASSEMBLY_PLANT"
    JOINT = "JOINT"


class Site(Base):
    __tablename__ = "sites"

    site_id = Column(Integer, primary_key=True, autoincrement=True)
    site_name = Column(String(100), nullable=False)
    site_type = Column(SQLAEnum(SiteType), nullable=False)
    address = Column(Text, nullable=True)

    users = relationship("User", back_populates="assigned_site")
    motors = relationship("Motor", back_populates="current_site")
    deliveries = relationship("Delivery", back_populates="site")
    invoices = relationship("Invoice", back_populates="site")

    def __repr__(self):
        return f"<Site(id={self.site_id}, name={self.site_name}, type={self.site_type})>"
