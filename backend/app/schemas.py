from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Any
import uuid
from pydantic import BaseModel, ConfigDict, Field, EmailStr


# -----------------------------
# Auth Schemas
# -----------------------------

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: str
    status: str
    supabase_uid: Optional[uuid.UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserProfileUpdate(BaseModel):
    business_name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    address: Optional[str] = Field(default=None, max_length=500)
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    service_area: Optional[str] = Field(default=None, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=20)
    gst_number: Optional[str] = Field(default=None, max_length=20)


class BusinessProfileResponse(BaseModel):
    id: int
    user_id: int
    business_name: str
    address: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    service_area: Optional[str]
    phone: Optional[str]
    gst_number: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -----------------------------
# Product / Inventory Schemas
# -----------------------------

class ProductBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    sku: Optional[str] = Field(default=None, max_length=50)
    category: Optional[str] = Field(default=None, max_length=100)
    unit: str = Field(default="piece", min_length=1, max_length=30)
    quantity: int = Field(default=0, ge=0)
    min_stock_level: int = Field(default=0, ge=0)
    cost_price: Decimal = Field(default=0, ge=0, decimal_places=2, max_digits=12)
    selling_price: Decimal = Field(default=0, ge=0, decimal_places=2, max_digits=12)
    vendor_id: Optional[int] = Field(default=None, gt=0)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    sku: Optional[str] = Field(default=None, max_length=50)
    category: Optional[str] = Field(default=None, max_length=100)
    unit: Optional[str] = Field(default=None, min_length=1, max_length=30)
    quantity: Optional[int] = Field(default=None, ge=0)
    min_stock_level: Optional[int] = Field(default=None, ge=0)
    cost_price: Optional[Decimal] = Field(default=None, ge=0, decimal_places=2, max_digits=12)
    selling_price: Optional[Decimal] = Field(default=None, ge=0, decimal_places=2, max_digits=12)
    vendor_id: Optional[int] = Field(default=None, gt=0)
    is_active: Optional[bool] = None


class ProductResponse(ProductBase):
    id: int
    business_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StockAdjustment(BaseModel):
    quantity_change: int = Field(..., description="Positive for stock in, negative for stock out")
    reason: str = Field(..., pattern="^(manual|bill|sale|adjustment|order|return)$")
    notes: Optional[str] = Field(default=None, max_length=500)


class InventoryMovementResponse(BaseModel):
    id: int
    product_id: int
    quantity_change: int
    reason: str
    source: str
    actor_id: int
    related_bill_id: Optional[int]
    related_order_id: Optional[int]
    notes: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -----------------------------
# OCR / Bill Schemas
# -----------------------------

class BillLineItemBase(BaseModel):
    extracted_name: str = Field(min_length=1, max_length=200)
    quantity: Decimal = Field(gt=0, decimal_places=3, max_digits=10)
    unit: str = Field(min_length=1, max_length=30)
    unit_price: Decimal = Field(ge=0, decimal_places=2, max_digits=12)
    tax: Decimal = Field(default=0, ge=0, decimal_places=2, max_digits=12)
    line_total: Decimal = Field(ge=0, decimal_places=2, max_digits=12)


class BillLineItemReview(BillLineItemBase):
    id: int
    product_id: Optional[int] = None
    category: Optional[str] = Field(default=None, max_length=100)
    sku: Optional[str] = Field(default=None, max_length=50)
    match_confidence: Optional[float] = Field(default=None, ge=0, le=1)


class PurchaseBillResponse(BaseModel):
    id: int
    business_id: int
    vendor_id: int
    invoice_number: str
    invoice_date: date
    file_path: str
    ocr_status: str
    ocr_raw_json: Optional[dict]
    subtotal: Optional[Decimal]
    tax_total: Optional[Decimal]
    grand_total: Optional[Decimal]
    confirmed: bool
    confirmed_at: Optional[datetime]
    confirmed_by: Optional[int]
    line_items: List[BillLineItemReview]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BillConfirmRequest(BaseModel):
    vendor_id: int = Field(gt=0)
    invoice_number: str = Field(min_length=1, max_length=100)
    invoice_date: date
    line_items: List[BillLineItemReview]


# -----------------------------
# Vendor Catalogue Schemas
# -----------------------------

class CatalogueCreate(BaseModel):
    vendor_id: int = Field(gt=0)
    product_name: str = Field(min_length=1, max_length=150)
    description: Optional[str] = Field(default=None, max_length=500)
    category: Optional[str] = Field(default=None, max_length=100)
    price: Decimal = Field(gt=0, decimal_places=2, max_digits=12)
    unit: str = Field(default="piece", min_length=1, max_length=30)
    pack_size: Decimal = Field(default=1, gt=0, decimal_places=3, max_digits=10)
    available_quantity: int = Field(default=0, ge=0)
    is_available: bool = True


class CatalogueUpdate(BaseModel):
    product_name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    description: Optional[str] = Field(default=None, max_length=500)
    category: Optional[str] = Field(default=None, max_length=100)
    price: Optional[Decimal] = Field(default=None, gt=0, decimal_places=2, max_digits=12)
    unit: Optional[str] = Field(default=None, min_length=1, max_length=30)
    pack_size: Optional[Decimal] = Field(default=None, gt=0, decimal_places=3, max_digits=10)
    available_quantity: Optional[int] = Field(default=None, ge=0)
    is_available: Optional[bool] = None


class CatalogueResponse(BaseModel):
    id: int
    vendor_id: int
    product_name: str
    description: Optional[str]
    category: Optional[str]
    price: Decimal
    unit: str
    pack_size: Decimal
    available_quantity: int
    is_available: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -----------------------------
# Vendor Location Schemas
# -----------------------------

class VendorLocationCreate(BaseModel):
    vendor_id: int = Field(gt=0)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    address: Optional[str] = Field(default=None, max_length=300)
    city: Optional[str] = Field(default=None, max_length=100)
    service_radius_km: float = Field(default=10, gt=0, le=500)


class VendorLocationUpdate(BaseModel):
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    address: Optional[str] = Field(default=None, max_length=300)
    city: Optional[str] = Field(default=None, max_length=100)
    service_radius_km: Optional[float] = Field(default=None, gt=0, le=500)


class VendorLocationResponse(BaseModel):
    id: int
    vendor_id: int
    latitude: float
    longitude: float
    address: Optional[str]
    city: Optional[str]
    service_radius_km: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -----------------------------
# Vendor Discovery Schemas
# -----------------------------

class VendorSearchResult(BaseModel):
    vendor_id: int
    business_name: str
    address: Optional[str]
    city: Optional[str]
    distance_km: float
    service_radius_km: float
    products: List[dict]


class PriceRecordResponse(BaseModel):
    id: int
    product_id: int
    vendor_id: int
    vendor_name: str
    price: Decimal
    unit: str
    pack_size: Decimal
    tax_included: bool
    date: date
    source: str
    source_id: Optional[int]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -----------------------------
# Chat Schemas
# -----------------------------

class ConversationCreate(BaseModel):
    vendor_id: int = Field(gt=0)


class ConversationResponse(BaseModel):
    id: int
    shopkeeper_id: int
    vendor_id: int
    vendor_name: Optional[str] = None
    shopkeeper_name: Optional[str] = None
    created_at: datetime
    last_message: Optional["MessageResponse"] = None
    unread_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)
    attachment_path: Optional[str] = None
    attachment_type: Optional[str] = Field(default=None, pattern="^(image|pdf|document)$")
    attachment_size: Optional[int] = None


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    sender_id: int
    content: str
    is_read: bool
    attachment_path: Optional[str]
    attachment_type: Optional[str]
    attachment_size: Optional[int]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -----------------------------
# Order Schemas
# -----------------------------

class OrderLineCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: Decimal = Field(gt=0, decimal_places=3, max_digits=10)
    unit: str = Field(min_length=1, max_length=30)
    unit_price: Decimal = Field(gt=0, decimal_places=2, max_digits=12)


class OrderCreate(BaseModel):
    vendor_id: int = Field(gt=0)
    items: List[OrderLineCreate] = Field(min_length=1)
    delivery_address: Optional[str] = Field(default=None, max_length=500)
    contact_phone: Optional[str] = Field(default=None, max_length=20)
    notes: Optional[str] = Field(default=None, max_length=500)


class OrderLineResponse(BaseModel):
    id: int
    order_id: int
    product_id: int
    product_name: str
    quantity: Decimal
    unit: str
    unit_price: Decimal
    line_total: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderStatusUpdate(BaseModel):
    status: str = Field(pattern="^(accepted|rejected|processing|shipped|delivered|cancelled)$")


class OrderResponse(BaseModel):
    id: int
    buyer_id: int
    vendor_id: int
    status: str
    total_amount: Decimal
    delivery_address: Optional[str]
    contact_phone: Optional[str]
    notes: Optional[str]
    items: List[OrderLineResponse]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -----------------------------
# Payment Schemas
# -----------------------------

class RazorpayOrderResponse(BaseModel):
    razorpay_order_id: str
    amount: int  # in paise
    currency: str
    key_id: str
    callback_url: str


class PaymentResponse(BaseModel):
    id: int
    order_id: int
    provider: str
    provider_payment_id: Optional[str]
    amount: Decimal
    currency: str
    status: str
    verified: bool
    verified_at: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -----------------------------
# Dashboard Schemas
# -----------------------------

class ShopkeeperDashboardResponse(BaseModel):
    total_products: int
    low_stock_count: int
    total_stock_value: Decimal
    recent_bills: int
    pending_orders: int
    unread_messages: int
    price_changes_today: int


class VendorDashboardResponse(BaseModel):
    catalogue_products: int
    active_products: int
    incoming_orders: int
    pending_orders: int
    unread_messages: int
    total_sales_this_month: Decimal


# -----------------------------
# Generic Response Schemas
# -----------------------------

class ErrorDetail(BaseModel):
    field: Optional[str] = None
    message: str


class ErrorResponse(BaseModel):
    error: dict


class PaginatedResponse(BaseModel):
    data: List[Any]
    meta: dict