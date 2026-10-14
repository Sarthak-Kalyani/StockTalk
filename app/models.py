from sqlalchemy import Text, ForeignKey, UniqueConstraint
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
)
from sqlalchemy.sql import func

from app.database import Base


class VendorCatalogue(Base):
    __tablename__ = "vendor_catalogue"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, nullable=False, index=True)

    product_name = Column(String(150), nullable=False, index=True)
    description = Column(String(500), nullable=True)
    category = Column(String(100), nullable=True, index=True)

    price = Column(Float, nullable=False)
    unit = Column(String(30), nullable=False, default="piece")
    available_quantity = Column(Integer, nullable=False, default=0)

    is_available = Column(Boolean, nullable=False, default=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class VendorLocation(Base):
    __tablename__ = "vendor_locations"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, nullable=False, unique=True, index=True)

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(String(300), nullable=True)
    city = Column(String(100), nullable=True)

    # Maximum distance this vendor serves customers, in kilometres.
    service_radius_km = Column(Float, nullable=False, default=10.0)


class Conversation(Base):
    __tablename__ = "conversations"

    __table_args__ = (
        UniqueConstraint(
            "shopkeeper_id",
            "vendor_id",
            name="uq_conversation_pair"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    shopkeeper_id = Column(Integer, nullable=False, index=True)
    vendor_id = Column(Integer, nullable=False, index=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id"),
        nullable=False,
        index=True
    )
    sender_id = Column(Integer, nullable=False, index=True)
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )


class ChatAttachment(Base):
    __tablename__ = "chat_attachments"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id"),
        nullable=False,
        index=True
    )
    sender_id = Column(Integer, nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=False, unique=True)
    content_type = Column(String(100), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
