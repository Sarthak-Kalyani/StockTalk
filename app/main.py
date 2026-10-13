import math

from sqlalchemy import select, or_
from app.schemas import ConversationCreate, ConversationResponse, MessageCreate, MessageResponse
from app.schemas import VendorLocationCreate, VendorLocationResponse
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Base, engine, get_db
from app import models
from app.schemas import CatalogueCreate, CatalogueResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Development convenience. We will use migrations
    # for the shared PostgreSQL database later.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.app_name,
    description="StockTalk vendor discovery and B2B chat backend",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
def home():
    return {
        "message": "Welcome to StockTalk Backend",
        "module": "Person 3 - Vendor Discovery & B2B Chat",
    }


@app.get("/health")
def health():
    return {"status": "ok", "service": "stocktalk-backend"}


@app.post(
    "/vendors/catalogue",
    response_model=CatalogueResponse,
    status_code=201,
    tags=["Vendor Catalogue"],
)
def add_catalogue_product(
    payload: CatalogueCreate,
    db: Session = Depends(get_db),
):
    product = models.VendorCatalogue(**payload.model_dump())

    db.add(product)
    db.commit()
    db.refresh(product)

    return product


@app.get(
    "/vendors/catalogue",
    response_model=list[CatalogueResponse],
    tags=["Vendor Catalogue"],
)
def list_catalogue(
    search: str | None = Query(default=None, max_length=150),
    category: str | None = Query(default=None, max_length=100),
    vendor_id: int | None = Query(default=None, gt=0),
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
    db: Session = Depends(get_db),
):
    if (
        min_price is not None
        and max_price is not None
        and min_price > max_price
    ):
        raise HTTPException(
            status_code=400,
            detail="min_price cannot exceed max_price",
        )

    stmt = select(models.VendorCatalogue).where(
        models.VendorCatalogue.is_available.is_(True)
    )

    if search:
        stmt = stmt.where(
            models.VendorCatalogue.product_name.ilike(f"%{search}%")
        )

    if category:
        stmt = stmt.where(
            models.VendorCatalogue.category.ilike(f"%{category}%")
        )

    if vendor_id is not None:
        stmt = stmt.where(
            models.VendorCatalogue.vendor_id == vendor_id
        )

    if min_price is not None:
        stmt = stmt.where(
            models.VendorCatalogue.price >= min_price
        )

    if max_price is not None:
        stmt = stmt.where(
            models.VendorCatalogue.price <= max_price
        )

    stmt = stmt.order_by(models.VendorCatalogue.product_name)

    return db.scalars(stmt).all()


@app.get(
    "/vendors/catalogue/{product_id}",
    response_model=CatalogueResponse,
    tags=["Vendor Catalogue"],
)
def get_catalogue_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    product = db.get(models.VendorCatalogue, product_id)

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Catalogue product not found",
        )

    return product


def calculate_distance_km(lat1, lon1, lat2, lon2):
    """Calculate the distance between two coordinates."""
    earth_radius_km = 6371.0

    lat1, lon1, lat2, lon2 = map(
        math.radians, [lat1, lon1, lat2, lon2]
    )

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    # Clamp against floating-point rounding errors.
    a = max(0.0, min(1.0, a))

    return 2 * earth_radius_km * math.asin(math.sqrt(a))


@app.post(
    "/vendors/location",
    response_model=VendorLocationResponse,
    tags=["Vendor Discovery"],
)
def save_vendor_location(
    payload: VendorLocationCreate,
    db: Session = Depends(get_db),
):
    location = db.scalar(
        select(models.VendorLocation).where(
            models.VendorLocation.vendor_id == payload.vendor_id
        )
    )

    if location is None:
        location = models.VendorLocation(**payload.model_dump())
        db.add(location)
    else:
        for key, value in payload.model_dump().items():
            setattr(location, key, value)

    db.commit()
    db.refresh(location)
    return location


@app.get(
    "/vendors/nearby",
    tags=["Vendor Discovery"],
)
def find_nearby_vendors(
    latitude: float = Query(ge=-90, le=90),
    longitude: float = Query(ge=-180, le=180),
    radius_km: float = Query(default=10, gt=0, le=500),
    product: str | None = Query(default=None, max_length=150),
    max_price: float | None = Query(default=None, ge=0),
    db: Session = Depends(get_db),
):
    locations = db.scalars(
        select(models.VendorLocation)
    ).all()

    results = []

    for location in locations:
        distance = calculate_distance_km(
            latitude,
            longitude,
            location.latitude,
            location.longitude,
        )

        if distance > radius_km:
            continue

        # Respect the vendor's configured service area too.
        if distance > location.service_radius_km:
            continue

        stmt = select(models.VendorCatalogue).where(
            models.VendorCatalogue.vendor_id == location.vendor_id,
            models.VendorCatalogue.is_available.is_(True),
        )

        if product:
            stmt = stmt.where(
                models.VendorCatalogue.product_name.ilike(
                    f"%{product}%"
                )
            )

        if max_price is not None:
            stmt = stmt.where(
                models.VendorCatalogue.price <= max_price
            )

        products = db.scalars(stmt).all()

        # When searching for a product, exclude vendors
        # that do not have a matching available product.
        if product and not products:
            continue

        results.append({
            "vendor_id": location.vendor_id,
            "latitude": location.latitude,
            "longitude": location.longitude,
            "address": location.address,
            "city": location.city,
            "distance_km": round(distance, 2),
            "service_radius_km": location.service_radius_km,
            "products": [
                {
                    "id": item.id,
                    "name": item.product_name,
                    "category": item.category,
                    "price": item.price,
                    "unit": item.unit,
                    "available_quantity": item.available_quantity,
                }
                for item in products
            ],
        })

    results.sort(key=lambda vendor: vendor["distance_km"])
    return results


# ---------------- B2B CHAT ----------------

@app.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=201
)
def create_conversation(
    payload: ConversationCreate,
    db: Session = Depends(get_db)
):
    if payload.shopkeeper_id == payload.vendor_id:
        raise HTTPException(
            status_code=400,
            detail="Shopkeeper and vendor must be different users."
        )

    # Reuse the conversation if it already exists.
    conversation = db.query(models.Conversation).filter(
        models.Conversation.shopkeeper_id == payload.shopkeeper_id,
        models.Conversation.vendor_id == payload.vendor_id
    ).first()

    if conversation:
        return conversation

    conversation = models.Conversation(
        shopkeeper_id=payload.shopkeeper_id,
        vendor_id=payload.vendor_id
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return conversation


@app.get(
    "/conversations",
    response_model=list[ConversationResponse]
)
def get_conversations(
    user_id: int = Query(gt=0),
    db: Session = Depends(get_db)
):
    conversations = db.query(models.Conversation).filter(
        or_(
            models.Conversation.shopkeeper_id == user_id,
            models.Conversation.vendor_id == user_id
        )
    ).order_by(
        models.Conversation.id.desc()
    ).all()

    return conversations


@app.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=201
)
def send_message(
    conversation_id: int,
    payload: MessageCreate,
    db: Session = Depends(get_db)
):
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id
    ).first()

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found."
        )

    # Only participants may send messages.
    if payload.sender_id not in (
        conversation.shopkeeper_id,
        conversation.vendor_id
    ):
        raise HTTPException(
            status_code=403,
            detail="You are not a participant in this conversation."
        )

    message = models.Message(
        conversation_id=conversation_id,
        sender_id=payload.sender_id,
        content=payload.content.strip()
    )

    if not message.content:
        raise HTTPException(
            status_code=422,
            detail="Message cannot be empty."
        )

    db.add(message)
    db.commit()
    db.refresh(message)

    return message


@app.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[MessageResponse]
)
def get_messages(
    conversation_id: int,
    user_id: int = Query(gt=0),
    db: Session = Depends(get_db)
):
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id
    ).first()

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found."
        )

    # Only participants may read chat history.
    if user_id not in (
        conversation.shopkeeper_id,
        conversation.vendor_id
    ):
        raise HTTPException(
            status_code=403,
            detail="You are not a participant in this conversation."
        )

    messages = db.query(models.Message).filter(
        models.Message.conversation_id == conversation_id
    ).order_by(
        models.Message.id.asc()
    ).all()

    return messages
