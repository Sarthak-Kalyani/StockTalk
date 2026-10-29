"""
Authentication and Profile API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional

from app.auth import (
    get_current_user,
    get_business_profile,
    get_shopkeeper_profile,
    get_vendor_profile,
)
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/me", response_model=schemas.UserResponse)
async def get_me(
    user: models.User = Depends(get_current_user),
):
    """Get current authenticated user info."""
    return user


@router.get("/me/profile", response_model=schemas.BusinessProfileResponse)
async def get_my_profile(
    profile: models.BusinessProfile = Depends(get_business_profile),
):
    """Get current user's business profile."""
    return profile


@router.patch("/me/profile", response_model=schemas.BusinessProfileResponse)
async def update_my_profile(
    payload: schemas.UserProfileUpdate,
    profile: models.BusinessProfile = Depends(get_business_profile),
    db: Session = Depends(get_db),
):
    """Update current user's business profile."""
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(profile, key, value)

    db.commit()
    db.refresh(profile)
    return profile


@router.post("/me/profile/complete", response_model=schemas.BusinessProfileResponse, status_code=status.HTTP_201_CREATED)
async def complete_profile(
    payload: schemas.UserProfileUpdate,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Complete business profile setup after first login."""
    # Check if profile already exists
    existing = db.query(models.BusinessProfile).filter(
        models.BusinessProfile.user_id == user.id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile already exists. Use PATCH to update."
        )

    # Require minimum fields
    if not payload.business_name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="business_name is required"
        )

    profile = models.BusinessProfile(
        user_id=user.id,
        business_name=payload.business_name,
        address=payload.address,
        latitude=payload.latitude,
        longitude=payload.longitude,
        service_area=payload.service_area,
        phone=payload.phone,
        gst_number=payload.gst_number,
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/health")
async def auth_health():
    """Auth service health check."""
    return {"status": "ok", "service": "auth"}