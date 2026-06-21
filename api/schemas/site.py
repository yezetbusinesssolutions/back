from pydantic import BaseModel, field_serializer
from enum import Enum


class SiteType(str, Enum):
    WAREHOUSE = "WAREHOUSE"
    SHOWROOM = "SHOWROOM"
    ASSEMBLY_PLANT = "ASSEMBLY_PLANT"
    JOINT = "JOINT"


class SiteBase(BaseModel):
    site_name: str
    site_type: str
    address: str | None = None


class SiteCreate(SiteBase):
    pass


class SiteUpdate(SiteBase):
    pass


class SiteResponse(SiteBase):
    site_id: int

    class Config:
        from_attributes = True

    @field_serializer('site_type')
    def serialize_site_type(self, value) -> str:
        if hasattr(value, 'value'):
            return value.value
        return value
