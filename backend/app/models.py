from sqlalchemy import Text, ForeignKey, UniqueConstraint, Index
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    BigInteger,
    Numeric,
    Date,
    JSON,
    Integer,
)
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)  # Supabase handles this
    role = Column(
        String(20),
        nullable=False,
        default="shopkeeper",
    )  # shopkeeper, vendor, admin
    status = Column(
        String(20),
        nullable=False,
        default="active",
    )  # active, inactive, pending
    supabase_uid = Column(UUID(as_uuid=True), unique=True, index=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class BusinessProfile(Base):
    __tablename__ = "business_profiles"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, index=True)
    user_id = Column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    business_name = Column(String(200), nullable=False)
    address = Column(Text, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    service_area = Column(String(100), nullable=True)  # city/area for manual search
    phone = Column(String(20), nullable=True)
    gst_number = Column(String(20), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Product(Base):
    __tablename__ = "products"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, index=True)
    business_id = Column(
        BigInteger,
        ForeignKey("business_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(200), nullable=False, index=True)
    sku = Column(String(50), unique=True, index=True)
    category = Column(String(100), nullable=True, index=True)
    unit = Column(String(30), nullable=False, default="piece")
    quantity = Column(Integer, nullable=False, default=0)
    min_stock_level = Column(Integer, nullable=False, default=0)
    cost_price = Column(Numeric(12, 2), nullable=False, default=0)
    selling_price = Column(Numeric(12, 2), nullable=False, default=0)
    vendor_id = Column(
        BigInteger,
        ForeignKey("business_profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_products_low_stock", "business_id", "quantity", postgresql_where="quantity <= min_stock_level"),
    )


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, index=True)
    product_id = Column(
        BigInteger,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    quantity_change = Column(Integer, nullable=False)  # positive = in, negative = out
    reason = Column(
        String(50),
        nullable=False,
    )  # manual, bill, sale, adjustment, order, return
    source = Column(String(50), nullable=False)  # manual, bill_upload, order_fulfillment, etc.
    actor_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    related_bill_id = Column(
        BigInteger,
        ForeignKey("purchase_bills.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    related_order_id = Column(
        BigInteger,
        ForeignKey("orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    notes = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_inventory_movements_product_created", "product_id", "created_at"),
    )


class PurchaseBill(Base):
    __tablename__ = "purchase_bills"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, index=True)
    business_id = Column(
        BigInteger,
        ForeignKey("business_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    vendor_id = Column(
        BigInteger,
        ForeignKey("business_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    invoice_number = Column(String(100), nullable=False)
    invoice_date = Column(Date, nullable=False)
    file_path = Column(Text, nullable=False)  # Supabase Storage path
    ocr_status = Column(
        String(20),
        nullable=False,
        default="pending",
    )  # pending, processing, completed, failed, review_needed
    ocr_raw_json = Column(JSON, nullable=True)
    subtotal = Column(Numeric(12, 2), nullable=True)
    tax_total = Column(Numeric(12, 2), nullable=True)
    grand_total = Column(Numeric(12, 2), nullable=True)
    confirmed = Column(Boolean, nullable=False, default=False)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    confirmed_by = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "vendor_id",
            "invoice_number",
            "invoice_date",
            name="uq_bill_vendor_invoice_date",
        ),
        Index("ix_purchase_bills_business_status", "business_id", "ocr_status"),
    )


class PurchaseBillLine(Base):
    __tablename__ = "purchase_bill_lines"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, index=True)
    bill_id = Column(
        BigInteger,
        ForeignKey("purchase_bills.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id = Column(
        BigInteger,
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    extracted_name = Column(String(200), nullable=False)
    quantity = Column(Numeric(10, 3), nullable=False)
    unit = Column(String(30), nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    tax = Column(Numeric(12, 2), nullable=False, default=0)
    line_total = Column(Numeric(12, 2), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class PriceRecord(Base):
    __tablename__ = "price_records"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, index=True)
    product_id = Column(
        BigInteger,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    vendor_id = Column(
        BigInteger,
        ForeignKey("business_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    price = Column(Numeric(12, 2), nullable=False)
    unit = Column(String(30), nullable=False)
    pack_size = Column(Numeric(10, 3), nullable=False, default=1)
    tax_included = Column(Boolean, nullable=False, default=True)
    date = Column(Date, nullable=False, index=True)
    source = Column(
        String(20),
        nullable=False,
    )  # bill, order, catalogue, manual
    source_id = Column(BigInteger, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_price_records_product_date", "product_id", "date"),
        Index("ix_price_records_vendor_date", "vendor_id", "date"),
        Index("ix_price_records_comparison", "product_id", "vendor_id", "unit", "pack_size"),
    )


# Vendor Discovery Models
class VendorCatalogue(Base):
    __tablename__ = "vendor_catalogue"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, index=True)
    vendor_id = Column(
        BigInteger,
        ForeignKey("business_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True, index=True)
    price = Column(Numeric(12, 2), nullable=False)
    unit = Column(String(30), nullable=False, default="piece")
    pack_size = Column(Numeric(10, 3), nullable=False, default=1)
    available_quantity = Column(Integer, nullable=False, default=0)
    is_available = Column(Boolean, nullable=False, default=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_vendor_catalogue_vendor_available", "vendor_id", "is_available"),
    )


class VendorLocation(Base):
    __tablename__ = "vendor_locations"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, index=True)
    vendor_id = Column(
        BigInteger,
        ForeignKey("business_profiles.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(String(300), nullable=True)
    city = Column(String(100), nullable=True)
    service_radius_km = Column(Float, nullable=False, default=10.0)
    geom = Column("geom", JSON, nullable=True)  # PostGIS geography point - stored as JSON for SQLite compat
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# Chat Models
class Conversation(Base):
    __tablename__ = "conversations"

    __table_args__ = (
        UniqueConstraint(
            "shopkeeper_id",
            "vendor_id",
            name="uq_conversation_pair",
        ),
    )

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, index=True)
    shopkeeper_id = Column(
        BigInteger,
        ForeignKey("business_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    vendor_id = Column(
        BigInteger,
        ForeignKey("business_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, index=True)
    conversation_id = Column(
        BigInteger,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, nullable=False, default=False)
    attachment_path = Column(Text, nullable=True)
    attachment_type = Column(String(50), nullable=True)  # image, pdf, document
    attachment_size = Column(Integer, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_messages_conversation_created", "conversation_id", "created_at"),
    )


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, index=True)
    message_id = Column(
        BigInteger,
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_path = Column(Text, nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False)
    original_name = Column(String(255), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


# Orders & Payments Models
class Order(Base):
    __tablename__ = "orders"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, index=True)
    buyer_id = Column(
        BigInteger,
        ForeignKey("business_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    vendor_id = Column(
        BigInteger,
        ForeignKey("business_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = Column(
        String(20),
        nullable=False,
        default="draft",
    )  # draft, sent, accepted, rejected, processing, shipped, delivered, cancelled
    total_amount = Column(Numeric(12, 2), nullable=False, default=0)
    delivery_address = Column(Text, nullable=True)
    contact_phone = Column(String(20), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_orders_buyer_created", "buyer_id", "created_at"),
        Index("ix_orders_vendor_created", "vendor_id", "created_at"),
        Index("ix_orders_status", "status"),
    )


class OrderLine(Base):
    __tablename__ = "order_lines"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, index=True)
    order_id = Column(
        BigInteger,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id = Column(
        BigInteger,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_name = Column(String(200), nullable=False)  # Snapshot at order time
    quantity = Column(Numeric(10, 3), nullable=False)
    unit = Column(String(30), nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    line_total = Column(Numeric(12, 2), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class Payment(Base):
    __tablename__ = "payments"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, index=True)
    order_id = Column(
        BigInteger,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider = Column(String(30), nullable=False, default="razorpay")
    provider_order_id = Column(String(100), nullable=True, index=True)
    provider_payment_id = Column(String(100), nullable=True, index=True)
    provider_signature = Column(String(255), nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="INR")
    status = Column(
        String(20),
        nullable=False,
        default="pending",
    )  # pending, success, failed, refunded
    verified = Column(Boolean, nullable=False, default=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    webhook_payload = Column(JSON, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )