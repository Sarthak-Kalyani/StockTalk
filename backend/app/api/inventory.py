"""
Inventory API Routes
"""
import math
from decimal import Decimal
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, func

from app.auth import get_current_user, get_shopkeeper_profile
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/products", tags=["Inventory"])


@router.post("", response_model=schemas.ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: schemas.ProductCreate,
    profile: models.BusinessProfile = Depends(get_shopkeeper_profile),
    db: Session = Depends(get_db),
):
    """Create a new product."""
    # Check SKU uniqueness within business
    if payload.sku:
        existing = db.query(models.Product).filter(
            models.Product.business_id == profile.id,
            models.Product.sku == payload.sku
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="SKU already exists for this business"
            )

    product = models.Product(
        business_id=profile.id,
        **payload.model_dump()
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("", response_model=List[schemas.ProductResponse])
async def list_products(
    search: Optional[str] = Query(None, max_length=200),
    category: Optional[str] = Query(None, max_length=100),
    is_active: Optional[bool] = Query(None),
    low_stock: Optional[bool] = Query(None),
    vendor_id: Optional[int] = Query(None, gt=0),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort: str = Query("name"),
    profile: models.BusinessProfile = Depends(get_shopkeeper_profile),
    db: Session = Depends(get_db),
):
    """List products with filtering and pagination."""
    stmt = select(models.Product).where(models.Product.business_id == profile.id)

    if search:
        stmt = stmt.where(
            or_(
                models.Product.name.ilike(f"%{search}%"),
                models.Product.sku.ilike(f"%{search}%")
            )
        )

    if category:
        stmt = stmt.where(models.Product.category.ilike(f"%{category}%"))

    if is_active is not None:
        stmt = stmt.where(models.Product.is_active == is_active)

    if low_stock:
        stmt = stmt.where(
            models.Product.quantity <= models.Product.min_stock_level
        )

    if vendor_id:
        stmt = stmt.where(models.Product.vendor_id == vendor_id)

    # Sorting
    sort_field = sort.lstrip("-")
    sort_desc = sort.startswith("-")
    sort_column = getattr(models.Product, sort_field, models.Product.name)
    if sort_desc:
        stmt = stmt.order_by(sort_column.desc())
    else:
        stmt = stmt.order_by(sort_column.asc())

    # Pagination
    offset = (page - 1) * limit
    stmt = stmt.offset(offset).limit(limit)

    products = db.scalars(stmt).all()
    return products


@router.get("/low-stock", response_model=List[schemas.ProductResponse])
async def get_low_stock_products(
    profile: models.BusinessProfile = Depends(get_shopkeeper_profile),
    db: Session = Depends(get_db),
):
    """Get products at or below minimum stock level."""
    stmt = select(models.Product).where(
        models.Product.business_id == profile.id,
        models.Product.is_active == True,
        models.Product.quantity <= models.Product.min_stock_level
    ).order_by(models.Product.quantity.asc())

    return db.scalars(stmt).all()


@router.get("/{product_id}", response_model=schemas.ProductResponse)
async def get_product(
    product_id: int,
    profile: models.BusinessProfile = Depends(get_shopkeeper_profile),
    db: Session = Depends(get_db),
):
    """Get a single product."""
    product = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.business_id == profile.id
    ).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    return product


@router.patch("/{product_id}", response_model=schemas.ProductResponse)
async def update_product(
    product_id: int,
    payload: schemas.ProductUpdate,
    profile: models.BusinessProfile = Depends(get_shopkeeper_profile),
    db: Session = Depends(get_db),
):
    """Update a product."""
    product = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.business_id == profile.id
    ).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    update_data = payload.model_dump(exclude_unset=True)

    # Check SKU uniqueness if being updated
    if "sku" in update_data and update_data["sku"]:
        existing = db.query(models.Product).filter(
            models.Product.business_id == profile.id,
            models.Product.sku == update_data["sku"],
            models.Product.id != product_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="SKU already exists for this business"
            )

    for key, value in update_data.items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_product(
    product_id: int,
    profile: models.BusinessProfile = Depends(get_shopkeeper_profile),
    db: Session = Depends(get_db),
):
    """Soft delete (deactivate) a product."""
    product = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.business_id == profile.id
    ).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    product.is_active = False
    db.commit()


@router.post("/{product_id}/stock-adjustment", response_model=schemas.InventoryMovementResponse, status_code=status.HTTP_201_CREATED)
async def adjust_stock(
    product_id: int,
    payload: schemas.StockAdjustment,
    user: models.User = Depends(get_current_user),
    profile: models.BusinessProfile = Depends(get_shopkeeper_profile),
    db: Session = Depends(get_db),
):
    """Manually adjust stock quantity."""
    product = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.business_id == profile.id
    ).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    new_quantity = product.quantity + payload.quantity_change
    if new_quantity < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient stock for this adjustment"
        )

    # Create movement record
    movement = models.InventoryMovement(
        product_id=product.id,
        quantity_change=payload.quantity_change,
        reason=payload.reason,
        source="manual",
        actor_id=user.id,
        notes=payload.notes,
    )
    db.add(movement)

    # Update product quantity
    product.quantity = new_quantity

    db.commit()
    db.refresh(movement)
    return movement


@router.get("/{product_id}/movements", response_model=List[schemas.InventoryMovementResponse])
async def get_stock_movements(
    product_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    profile: models.BusinessProfile = Depends(get_shopkeeper_profile),
    db: Session = Depends(get_db),
):
    """Get stock movement history for a product."""
    product = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.business_id == profile.id
    ).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    stmt = select(models.InventoryMovement).where(
        models.InventoryMovement.product_id == product_id
    ).order_by(models.InventoryMovement.created_at.desc())

    offset = (page - 1) * limit
    stmt = stmt.offset(offset).limit(limit)

    return db.scalars(stmt).all()


@router.get("/{product_id}/price-history", response_model=List[schemas.PriceRecordResponse])
async def get_price_history(
    product_id: int,
    vendor_id: Optional[int] = Query(None, gt=0),
    profile: models.BusinessProfile = Depends(get_shopkeeper_profile),
    db: Session = Depends(get_db),
):
    """Get purchase price history for a product."""
    product = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.business_id == profile.id
    ).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    stmt = select(models.PriceRecord).where(
        models.PriceRecord.product_id == product_id
    )

    if vendor_id:
        stmt = stmt.where(models.PriceRecord.vendor_id == vendor_id)

    stmt = stmt.order_by(models.PriceRecord.date.desc())

    records = db.scalars(stmt).all()

    # Enrich with vendor name
    result = []
    for record in records:
        vendor = db.query(models.BusinessProfile).filter(
            models.BusinessProfile.id == record.vendor_id
        ).first()
        result.append(schemas.PriceRecordResponse(
            **record.__dict__,
            vendor_name=vendor.business_name if vendor else "Unknown"
        ))

    return result