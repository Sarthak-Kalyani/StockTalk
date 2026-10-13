
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# -----------------------------
# Vendor Catalogue Schemas
# -----------------------------

class CatalogueCreate(BaseModel):
    vendor_id: int = Field(gt=0)
    product_name: str = Field(min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    category: str | None = Field(default=None, max_length=100)
    price: float = Field(gt=0, allow_inf_nan=False)
    unit: str = Field(default="piece", min_length=1, max_length=30)
    available_quantity: int = Field(default=0, ge=0)
    is_available: bool = True


class CatalogueResponse(BaseModel):
    id: int
    vendor_id: int
    product_name: str
    description: str | None
    category: str | None
    price: float
    unit: str
    available_quantity: int
    is_available: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -----------------------------
# Vendor Location Schemas
# -----------------------------

class VendorLocationCreate(BaseModel):
    vendor_id: int = Field(gt=0)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    address: str | None = Field(default=None, max_length=300)
    city: str | None = Field(default=None, max_length=100)
    service_radius_km: float = Field(
        default=10,
        gt=0,
        le=500,
        allow_inf_nan=False,
    )


class VendorLocationResponse(BaseModel):
    id: int
    vendor_id: int
    latitude: float
    longitude: float
    address: str | None
    city: str | None
    service_radius_km: float

    model_config = ConfigDict(from_attributes=True)


class ConversationCreate(BaseModel):
    shopkeeper_id: int = Field(gt=0)
    vendor_id: int = Field(gt=0)


class ConversationResponse(BaseModel):
    id: int
    shopkeeper_id: int
    vendor_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageCreate(BaseModel):
    sender_id: int = Field(gt=0)
    content: str = Field(min_length=1, max_length=5000)


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    sender_id: int
    content: str
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
