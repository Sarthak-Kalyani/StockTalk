import math
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Base, engine, get_db, init_db
from app import models, schemas
from app.api import auth, inventory, bills, vendors, chat, orders, payments, dashboard


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Development convenience. Use migrations for production.
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    description="StockTalk B2B Inventory and Supplier Communication Platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration
cors_origins = [origin.strip() for origin in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/health")
def health():
    return {"status": "ok", "service": "stocktalk-backend", "version": "1.0.0"}


# Root endpoint
@app.get("/")
def root():
    return {
        "message": "Welcome to StockTalk Backend",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


# Include API routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(inventory.router, prefix="/api/v1")
app.include_router(bills.router, prefix="/api/v1")
app.include_router(vendors.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")
app.include_router(payments.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")


# Legacy endpoints for backward compatibility (Person 3's original work)
# These will be deprecated once frontend migrates to new API structure

@app.post(
    "/vendors/catalogue",
    response_model=schemas.CatalogueResponse,
    status_code=201,
    tags=["Legacy - Vendor Catalogue"],
    deprecated=True,
)
def legacy_add_catalogue_product(
    payload: schemas.CatalogueCreate,
    db: Session = Depends(get_db),
):
    product = models.VendorCatalogue(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@app.get(
    "/vendors/catalogue",
    response_model=list[schemas.CatalogueResponse],
    tags=["Legacy - Vendor Catalogue"],
    deprecated=True,
)
def legacy_list_catalogue(
    search: str | None = Query(default=None, max_length=150),
    category: str | None = Query(default=None, max_length=100),
    vendor_id: int | None = Query(default=None, gt=0),
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
    db: Session = Depends(get_db),
):
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(status_code=400, detail="min_price cannot exceed max_price")

    stmt = select(models.VendorCatalogue).where(models.VendorCatalogue.is_available.is_(True))

    if search:
        stmt = stmt.where(models.VendorCatalogue.product_name.ilike(f"%{search}%"))
    if category:
        stmt = stmt.where(models.VendorCatalogue.category.ilike(f"%{category}%"))
    if vendor_id is not None:
        stmt = stmt.where(models.VendorCatalogue.vendor_id == vendor_id)
    if min_price is not None:
        stmt = stmt.where(models.VendorCatalogue.price >= min_price)
    if max_price is not None:
        stmt = stmt.where(models.VendorCatalogue.price <= max_price)

    stmt = stmt.order_by(models.VendorCatalogue.product_name)
    return db.scalars(stmt).all()


def calculate_distance_km(lat1, lon1, lat2, lon2):
    """Calculate the distance between two coordinates."""
    earth_radius_km = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)
    a = max(0.0, min(1.0, a))
    return 2 * earth_radius_km * math.asin(math.sqrt(a))


@app.post(
    "/vendors/location",
    response_model=schemas.VendorLocationResponse,
    tags=["Legacy - Vendor Discovery"],
    deprecated=True,
)
def legacy_save_vendor_location(
    payload: schemas.VendorLocationCreate,
    db: Session = Depends(get_db),
):
    location = db.scalar(
        select(models.VendorLocation).where(models.VendorLocation.vendor_id == payload.vendor_id)
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
    tags=["Legacy - Vendor Discovery"],
    deprecated=True,
)
def legacy_find_nearby_vendors(
    latitude: float = Query(ge=-90, le=90),
    longitude: float = Query(ge=-180, le=180),
    radius_km: float = Query(default=10, gt=0, le=500),
    product: str | None = Query(default=None, max_length=150),
    max_price: float | None = Query(default=None, ge=0),
    db: Session = Depends(get_db),
):
    locations = db.scalars(select(models.VendorLocation)).all()
    results = []
    for location in locations:
        distance = calculate_distance_km(latitude, longitude, location.latitude, location.longitude)
        if distance > radius_km:
            continue
        if distance > location.service_radius_km:
            continue
        stmt = select(models.VendorCatalogue).where(
            models.VendorCatalogue.vendor_id == location.vendor_id,
            models.VendorCatalogue.is_available.is_(True),
        )
        if product:
            stmt = stmt.where(models.VendorCatalogue.product_name.ilike(f"%{product}%"))
        if max_price is not None:
            stmt = stmt.where(models.VendorCatalogue.price <= max_price)
        products = db.scalars(stmt).all()
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


# Legacy Chat endpoints
@app.post("/conversations", response_model=schemas.ConversationResponse, status_code=201, tags=["Legacy - Chat"], deprecated=True)
def legacy_create_conversation(payload: schemas.ConversationCreate, db: Session = Depends(get_db)):
    if payload.shopkeeper_id == payload.vendor_id:
        raise HTTPException(status_code=400, detail="Shopkeeper and vendor must be different users.")
    conversation = db.query(models.Conversation).filter(
        models.Conversation.shopkeeper_id == payload.shopkeeper_id,
        models.Conversation.vendor_id == payload.vendor_id
    ).first()
    if conversation:
        return conversation
    conversation = models.Conversation(shopkeeper_id=payload.shopkeeper_id, vendor_id=payload.vendor_id)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


@app.get("/conversations", response_model=list[schemas.ConversationResponse], tags=["Legacy - Chat"], deprecated=True)
def legacy_get_conversations(user_id: int = Query(gt=0), db: Session = Depends(get_db)):
    conversations = db.query(models.Conversation).filter(
        (models.Conversation.shopkeeper_id == user_id) | (models.Conversation.vendor_id == user_id)
    ).order_by(models.Conversation.id.desc()).all()
    return conversations


@app.post("/conversations/{conversation_id}/messages", response_model=schemas.MessageResponse, status_code=201, tags=["Legacy - Chat"], deprecated=True)
def legacy_send_message(conversation_id: int, payload: schemas.MessageCreate, db: Session = Depends(get_db)):
    conversation = db.query(models.Conversation).filter(models.Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    if payload.sender_id not in (conversation.shopkeeper_id, conversation.vendor_id):
        raise HTTPException(status_code=403, detail="You are not a participant in this conversation.")
    message = models.Message(conversation_id=conversation_id, sender_id=payload.sender_id, content=payload.content.strip())
    if not message.content:
        raise HTTPException(status_code=422, detail="Message cannot be empty.")
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


@app.get("/conversations/{conversation_id}/messages", response_model=list[schemas.MessageResponse], tags=["Legacy - Chat"], deprecated=True)
def legacy_get_messages(conversation_id: int, user_id: int = Query(gt=0), db: Session = Depends(get_db)):
    conversation = db.query(models.Conversation).filter(models.Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    if user_id not in (conversation.shopkeeper_id, conversation.vendor_id):
        raise HTTPException(status_code=403, detail="You are not a participant in this conversation.")
    messages = db.query(models.Message).filter(models.Message.conversation_id == conversation_id).order_by(models.Message.id.asc()).all()
    return messages