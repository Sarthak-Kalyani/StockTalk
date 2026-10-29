"""
Chat API Routes
"""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, func

from app.auth import get_current_user
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/conversations", tags=["Chat"])


@router.post("", response_model=schemas.ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    payload: schemas.ConversationCreate,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create or get existing conversation between shopkeeper and vendor.
    Shopkeeper initiates conversation with vendor.
    """
    # Verify vendor exists
    vendor_profile = db.query(models.BusinessProfile).filter(
        models.BusinessProfile.id == payload.vendor_id
    ).first()

    if not vendor_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )

    # Get shopkeeper's profile
    shopkeeper_profile = db.query(models.BusinessProfile).filter(
        models.BusinessProfile.user_id == user.id
    ).first()

    if not shopkeeper_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Complete your business profile first"
        )

    if shopkeeper_profile.id == payload.vendor_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot start conversation with yourself"
        )

    # Check if conversation exists
    conversation = db.query(models.Conversation).filter(
        models.Conversation.shopkeeper_id == shopkeeper_profile.id,
        models.Conversation.vendor_id == payload.vendor_id
    ).first()

    if conversation:
        return schemas.ConversationResponse(
            **conversation.__dict__,
            vendor_name=vendor_profile.business_name,
            shopkeeper_name=shopkeeper_profile.business_name,
        )

    # Create new conversation
    conversation = models.Conversation(
        shopkeeper_id=shopkeeper_profile.id,
        vendor_id=payload.vendor_id,
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return schemas.ConversationResponse(
        **conversation.__dict__,
        vendor_name=vendor_profile.business_name,
        shopkeeper_name=shopkeeper_profile.business_name,
    )


@router.get("", response_model=List[schemas.ConversationResponse])
async def list_conversations(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all conversations for current user."""
    # Get user's business profile
    profile = db.query(models.BusinessProfile).filter(
        models.BusinessProfile.user_id == user.id
    ).first()

    if not profile:
        return []

    # Get conversations where user is either shopkeeper or vendor
    stmt = select(models.Conversation).where(
        or_(
            models.Conversation.shopkeeper_id == profile.id,
            models.Conversation.vendor_id == profile.id
        )
    ).order_by(models.Conversation.created_at.desc())

    conversations = db.scalars(stmt).all()

    result = []
    for conv in conversations:
        # Get other party's profile
        other_id = conv.vendor_id if conv.shopkeeper_id == profile.id else conv.shopkeeper_id
        other_profile = db.query(models.BusinessProfile).filter(
            models.BusinessProfile.id == other_id
        ).first()

        # Get last message
        last_msg = db.query(models.Message).filter(
            models.Message.conversation_id == conv.id
        ).order_by(models.Message.created_at.desc()).first()

        # Count unread messages
        unread_count = db.query(func.count(models.Message.id)).filter(
            models.Message.conversation_id == conv.id,
            models.Message.sender_id != user.id,
            models.Message.is_read == False
        ).scalar() or 0

        result.append(schemas.ConversationResponse(
            **conv.__dict__,
            vendor_name=other_profile.business_name if conv.vendor_id == other_id else None,
            shopkeeper_name=other_profile.business_name if conv.shopkeeper_id == other_id else None,
            last_message=schemas.MessageResponse.model_validate(last_msg) if last_msg else None,
            unread_count=unread_count,
        ))

    return result


@router.get("/{conversation_id}", response_model=schemas.ConversationResponse)
async def get_conversation(
    conversation_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get conversation details."""
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id
    ).first()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    # Verify user is participant
    profile = db.query(models.BusinessProfile).filter(
        models.BusinessProfile.user_id == user.id
    ).first()

    if not profile or profile.id not in [conversation.shopkeeper_id, conversation.vendor_id]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a participant in this conversation"
        )

    other_id = conversation.vendor_id if conversation.shopkeeper_id == profile.id else conversation.shopkeeper_id
    other_profile = db.query(models.BusinessProfile).filter(
        models.BusinessProfile.id == other_id
    ).first()

    last_msg = db.query(models.Message).filter(
        models.Message.conversation_id == conversation_id
    ).order_by(models.Message.created_at.desc()).first()

    unread_count = db.query(func.count(models.Message.id)).filter(
        models.Message.conversation_id == conversation_id,
        models.Message.sender_id != user.id,
        models.Message.is_read == False
    ).scalar() or 0

    return schemas.ConversationResponse(
        **conversation.__dict__,
        vendor_name=other_profile.business_name if conversation.vendor_id == other_id else None,
        shopkeeper_name=other_profile.business_name if conversation.shopkeeper_id == other_id else None,
        last_message=schemas.MessageResponse.model_validate(last_msg) if last_msg else None,
        unread_count=unread_count,
    )


@router.post("/{conversation_id}/messages", response_model=schemas.MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    conversation_id: int,
    payload: schemas.MessageCreate,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send a message in a conversation."""
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id
    ).first()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    # Verify user is participant
    profile = db.query(models.BusinessProfile).filter(
        models.BusinessProfile.user_id == user.id
    ).first()

    if not profile or profile.id not in [conversation.shopkeeper_id, conversation.vendor_id]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a participant in this conversation"
        )

    if not payload.content.strip() and not payload.attachment_path:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Message cannot be empty"
        )

    message = models.Message(
        conversation_id=conversation_id,
        sender_id=user.id,
        content=payload.content.strip() if payload.content else "",
        attachment_path=payload.attachment_path,
        attachment_type=payload.attachment_type,
        attachment_size=payload.attachment_size,
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    return message


@router.get("/{conversation_id}/messages", response_model=List[schemas.MessageResponse])
async def get_messages(
    conversation_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get messages in a conversation with pagination."""
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id
    ).first()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    # Verify user is participant
    profile = db.query(models.BusinessProfile).filter(
        models.BusinessProfile.user_id == user.id
    ).first()

    if not profile or profile.id not in [conversation.shopkeeper_id, conversation.vendor_id]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a participant in this conversation"
        )

    stmt = select(models.Message).where(
        models.Message.conversation_id == conversation_id
    ).order_by(models.Message.created_at.asc())

    offset = (page - 1) * limit
    stmt = stmt.offset(offset).limit(limit)

    messages = db.scalars(stmt).all()
    return messages


@router.patch("/{conversation_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_messages_read(
    conversation_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark all messages in conversation as read by current user."""
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id
    ).first()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    # Verify user is participant
    profile = db.query(models.BusinessProfile).filter(
        models.BusinessProfile.user_id == user.id
    ).first()

    if not profile or profile.id not in [conversation.shopkeeper_id, conversation.vendor_id]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a participant in this conversation"
        )

    # Mark unread messages from other party as read
    db.query(models.Message).filter(
        models.Message.conversation_id == conversation_id,
        models.Message.sender_id != user.id,
        models.Message.is_read == False
    ).update({models.Message.is_read: True})

    db.commit()


@router.post("/{conversation_id}/attachments")
async def upload_attachment(
    conversation_id: int,
    file: UploadFile = File(...),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload attachment for chat.
    Returns file info for including in message.
    """
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id
    ).first()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    # Verify user is participant
    profile = db.query(models.BusinessProfile).filter(
        models.BusinessProfile.user_id == user.id
    ).first()

    if not profile or profile.id not in [conversation.shopkeeper_id, conversation.vendor_id]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a participant in this conversation"
        )

    # Validate file
    allowed_types = ["image/jpeg", "image/png", "image/webp", "application/pdf"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_types)}"
        )

    content = await file.read()
    if len(content) > 5 * 1024 * 1024:  # 5MB limit for chat
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 5MB limit"
        )

    # Determine file type
    file_type = "image" if file.content_type.startswith("image/") else "pdf"

    # TODO: Upload to Supabase Storage
    # storage_path = f"chat-attachments/{conversation_id}/{uuid.uuid4()}_{file.filename}"
    # supabase.storage.from_(settings.supabase_storage_bucket_chat).upload(storage_path, content)
    # signed_url = supabase.storage.from_(...).create_signed_url(storage_path, 3600)

    # For now, return mock response
    storage_path = f"chat-attachments/{conversation_id}/mock_{file.filename}"

    return {
        "file_path": storage_path,
        "file_type": file_type,
        "file_size": len(content),
        "original_name": file.filename,
        # "signed_url": signed_url["signedURL"],
    }