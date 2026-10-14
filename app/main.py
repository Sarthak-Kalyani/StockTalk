import math

import uuid
from pathlib import Path

from fastapi import WebSocket, WebSocketDisconnect
from app.database import SessionLocal

from fastapi.staticfiles import StaticFiles

from fastapi import UploadFile, File, Form
from supabase import create_client

from app.schemas import AttachmentResponse

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

def get_supabase_client():
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise HTTPException(
            status_code=500,
            detail="Supabase credentials are not configured."
        )

    return create_client(
        settings.supabase_url,
        settings.supabase_service_role_key
    )



class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, conversation_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.setdefault(
            conversation_id, []
        ).append(websocket)

    def disconnect(self, conversation_id: int, websocket: WebSocket):
        connections = self.active_connections.get(conversation_id, [])

        if websocket in connections:
            connections.remove(websocket)

        if not connections:
            self.active_connections.pop(conversation_id, None)

    async def broadcast(self, conversation_id: int, message: dict):
        connections = self.active_connections.get(
            conversation_id, []
        ).copy()

        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(conversation_id, connection)


chat_manager = ConnectionManager()



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


ALLOWED_FILES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".pdf": "application/pdf",
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@app.post(
    "/conversations/{conversation_id}/attachments",
    response_model=AttachmentResponse,
    status_code=201
)
async def upload_attachment(
    conversation_id: int,
    sender_id: int = Form(...),
    file: UploadFile = File(...),
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

    if sender_id not in (
        conversation.shopkeeper_id,
        conversation.vendor_id
    ):
        raise HTTPException(
            status_code=403,
            detail="You are not a participant in this conversation."
        )

    extension = Path(file.filename or "").suffix.lower()
    expected_type = ALLOWED_FILES.get(extension)

    if not expected_type:
        raise HTTPException(
            status_code=400,
            detail="Only JPG, PNG, GIF, WEBP, and PDF files are allowed."
        )

    if file.content_type != expected_type:
        raise HTTPException(
            status_code=400,
            detail="File type does not match its extension."
        )

    contents = await file.read(MAX_FILE_SIZE + 1)

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty."
        )

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File size must not exceed 10 MB."
        )

    # Check the file signature, not just its filename.
    valid_signature = (
        (extension in (".jpg", ".jpeg")
         and contents.startswith(b"\xff\xd8\xff"))
        or (extension == ".png"
            and contents.startswith(b"\x89PNG\r\n\x1a\n"))
        or (extension == ".gif"
            and contents.startswith((b"GIF87a", b"GIF89a")))
        or (extension == ".webp"
            and len(contents) >= 12
            and contents[:4] == b"RIFF"
            and contents[8:12] == b"WEBP")
        or (extension == ".pdf"
            and contents.startswith(b"%PDF-"))
    )

    if not valid_signature:
        raise HTTPException(
            status_code=400,
            detail="The file content does not match an allowed file type."
        )

    safe_name = f"{uuid.uuid4().hex}{extension}"
    storage_path = f"conversation-{conversation_id}/{safe_name}"

    try:
        supabase = get_supabase_client()

        supabase.storage.from_(
            settings.supabase_bucket
        ).upload(
            storage_path,
            contents,
            file_options={
                "content-type": expected_type,
                "upsert": "false"
            }
        )

    except Exception as exc:
        print(f"Attachment upload failed: {exc}")
        raise HTTPException(
            status_code=502,
            detail="Could not upload file to storage. Check server logs."
        ) from exc

    attachment = models.ChatAttachment(
        conversation_id=conversation_id,
        sender_id=sender_id,
        original_filename=Path(file.filename or "attachment").name[:255],
        storage_path=storage_path,
        content_type=expected_type,
        size_bytes=len(contents)
    )

    try:
        db.add(attachment)
        db.commit()
        db.refresh(attachment)
    except Exception as exc:
        db.rollback()
        # The uploaded object may remain in storage if the database fails.
        raise HTTPException(
            status_code=500,
            detail="File uploaded, but saving its record failed."
        ) from exc
    finally:
        await file.close()

    return attachment


@app.get(
    "/conversations/{conversation_id}/attachments/{attachment_id}/download"
)
def get_attachment_download_url(
    conversation_id: int,
    attachment_id: int,
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

    if user_id not in (
        conversation.shopkeeper_id,
        conversation.vendor_id
    ):
        raise HTTPException(
            status_code=403,
            detail="You are not a participant in this conversation."
        )

    attachment = db.query(models.ChatAttachment).filter(
        models.ChatAttachment.id == attachment_id,
        models.ChatAttachment.conversation_id == conversation_id
    ).first()

    if not attachment:
        raise HTTPException(
            status_code=404,
            detail="Attachment not found."
        )

    try:
        result = get_supabase_client().storage.from_(
            settings.supabase_bucket
        ).create_signed_url(
            attachment.storage_path,
            300
        )

        signed_url = result.get("signedURL") or result.get("signedUrl")

        if not signed_url:
            raise ValueError("Supabase did not return a signed URL.")

        return {
            "attachment_id": attachment.id,
            "filename": attachment.original_filename,
            "content_type": attachment.content_type,
            "size_bytes": attachment.size_bytes,
            "expires_in_seconds": 300,
            "download_url": signed_url
        }

    except Exception as exc:
        print(f"Signed URL creation failed: {exc}")
        raise HTTPException(
            status_code=502,
            detail="Could not generate a download link."
        ) from exc


@app.get(
    "/conversations/{conversation_id}/attachments",
    response_model=list[AttachmentResponse]
)
def list_attachments(
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

    if user_id not in (
        conversation.shopkeeper_id,
        conversation.vendor_id
    ):
        raise HTTPException(
            status_code=403,
            detail="You are not a participant in this conversation."
        )

    attachments = db.query(models.ChatAttachment).filter(
        models.ChatAttachment.conversation_id == conversation_id
    ).order_by(
        models.ChatAttachment.id.desc()
    ).all()

    return attachments


@app.post("/conversations/{conversation_id}/read")
def mark_messages_as_read(
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

    if user_id not in (
        conversation.shopkeeper_id,
        conversation.vendor_id
    ):
        raise HTTPException(
            status_code=403,
            detail="You are not a participant in this conversation."
        )

    # Mark only messages sent by the other participant as read.
    updated_count = db.query(models.Message).filter(
        models.Message.conversation_id == conversation_id,
        models.Message.sender_id != user_id,
        models.Message.is_read == False
    ).update(
        {models.Message.is_read: True},
        synchronize_session=False
    )

    db.commit()

    return {
        "conversation_id": conversation_id,
        "reader_id": user_id,
        "messages_marked_as_read": updated_count
    }


@app.get("/conversations/unread-counts")
def get_unread_counts(
    user_id: int = Query(gt=0),
    db: Session = Depends(get_db)
):
    conversations = db.query(models.Conversation).filter(
        or_(
            models.Conversation.shopkeeper_id == user_id,
            models.Conversation.vendor_id == user_id
        )
    ).all()

    results = []

    for conversation in conversations:
        unread_count = db.query(models.Message).filter(
            models.Message.conversation_id == conversation.id,
            models.Message.sender_id != user_id,
            models.Message.is_read == False
        ).count()

        other_user_id = (
            conversation.vendor_id
            if conversation.shopkeeper_id == user_id
            else conversation.shopkeeper_id
        )

        results.append({
            "conversation_id": conversation.id,
            "other_user_id": other_user_id,
            "unread_count": unread_count
        })

    return {
        "user_id": user_id,
        "conversations": results
    }



@app.websocket("/ws/conversations/{conversation_id}")
async def websocket_chat(
    websocket: WebSocket,
    conversation_id: int,
    user_id: int
):
    db = SessionLocal()

    try:
        conversation = db.query(models.Conversation).filter(
            models.Conversation.id == conversation_id
        ).first()

        if not conversation:
            await websocket.close(
                code=1008,
                reason="Conversation not found."
            )
            return

        if user_id not in (
            conversation.shopkeeper_id,
            conversation.vendor_id
        ):
            await websocket.close(
                code=1008,
                reason="You are not a participant."
            )
            return

        await chat_manager.connect(conversation_id, websocket)

        while True:
            payload = await websocket.receive_json()
            content = payload.get("content")

            if not isinstance(content, str):
                await websocket.send_json({
                    "error": "Message content must be text."
                })
                continue

            content = content.strip()

            if not content or len(content) > 5000:
                await websocket.send_json({
                    "error": "Message must contain 1–5000 characters."
                })
                continue

            # The sender ID comes from the connection, not the message body.
            message = models.Message(
                conversation_id=conversation_id,
                sender_id=user_id,
                content=content
            )

            db.add(message)
            db.commit()
            db.refresh(message)

            event = {
                "id": message.id,
                "conversation_id": message.conversation_id,
                "sender_id": message.sender_id,
                "content": message.content,
                "is_read": message.is_read,
                "created_at": (
                    message.created_at.isoformat()
                    if message.created_at else None
                )
            }

            await chat_manager.broadcast(conversation_id, event)

    except WebSocketDisconnect:
        pass

    finally:
        chat_manager.disconnect(conversation_id, websocket)
        db.close()

app.mount(
    "/frontend",
    StaticFiles(directory="frontend", html=True),
    name="frontend"
)