"""
Orders API Routes
"""
from decimal import Decimal
from typing import Optional, List
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, func

from app.auth import get_current_user, get_shopkeeper_profile, get_vendor_profile
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/orders", tags=["Orders"])


# -----------------------------
# Shopkeeper Endpoints
# -----------------------------

@router.post("", response_model=schemas.OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: schemas.OrderCreate,
    user: models.User = Depends(get_current_user),
    profile: models.BusinessProfile = Depends(get_shopkeeper_profile),
    db: Session = Depends(get_db),
):
    """Create a new purchase order."""
    # Verify vendor exists
    vendor = db.query(models.BusinessProfile).filter(
        models.BusinessProfile.id == payload.vendor_id
    ).first()

    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )

    # Calculate totals and validate items
    total_amount = Decimal("0")
    order_lines = []

    for item in payload.items:
        product = db.query(models.Product).filter(
            models.Product.id == item.product_id
        ).first()

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {item.product_id} not found"
            )

        line_total = item.quantity * item.unit_price
        total_amount += line_total

        order_lines.append({
            "product_id": product.id,
            "product_name": product.name,
            "quantity": item.quantity,
            "unit": item.unit,
            "unit_price": item.unit_price,
            "line_total": line_total,
        })

    # Create order
    order = models.Order(
        buyer_id=profile.id,
        vendor_id=payload.vendor_id,
        status="sent",
        total_amount=total_amount,
        delivery_address=payload.delivery_address,
        contact_phone=payload.contact_phone,
        notes=payload.notes,
    )
    db.add(order)
    db.flush()

    # Create order lines
    for line_data in order_lines:
        line = models.OrderLine(
            order_id=order.id,
            **line_data
        )
        db.add(line)

    db.commit()
    db.refresh(order)

    # Load lines for response
    lines = db.query(models.OrderLine).filter(
        models.OrderLine.order_id == order.id
    ).all()

    return schemas.OrderResponse(
        **order.__dict__,
        items=[schemas.OrderLineResponse.model_validate(l) for l in lines]
    )


@router.get("", response_model=List[schemas.OrderResponse])
async def list_my_orders(
    status: Optional[str] = Query(None, pattern="^(draft|sent|accepted|rejected|processing|shipped|delivered|cancelled)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    profile: models.BusinessProfile = Depends(get_shopkeeper_profile),
    db: Session = Depends(get_db),
):
    """List orders placed by current shopkeeper."""
    stmt = select(models.Order).where(models.Order.buyer_id == profile.id)

    if status:
        stmt = stmt.where(models.Order.status == status)

    stmt = stmt.order_by(models.Order.created_at.desc())

    offset = (page - 1) * limit
    stmt = stmt.offset(offset).limit(limit)

    orders = db.scalars(stmt).all()

    result = []
    for order in orders:
        lines = db.query(models.OrderLine).filter(
            models.OrderLine.order_id == order.id
        ).all()
        result.append(schemas.OrderResponse(
            **order.__dict__,
            items=[schemas.OrderLineResponse.model_validate(l) for l in lines]
        ))

    return result


@router.get("/{order_id}", response_model=schemas.OrderResponse)
async def get_order(
    order_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get order details (buyer or vendor)."""
    order = db.query(models.Order).filter(models.Order.id == order_id).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    # Verify user is buyer or vendor
    profile = db.query(models.BusinessProfile).filter(
        models.BusinessProfile.user_id == user.id
    ).first()

    if not profile or profile.id not in [order.buyer_id, order.vendor_id]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this order"
        )

    lines = db.query(models.OrderLine).filter(
        models.OrderLine.order_id == order.id
    ).all()

    return schemas.OrderResponse(
        **order.__dict__,
        items=[schemas.OrderLineResponse.model_validate(l) for l in lines]
    )


@router.patch("/{order_id}/cancel", response_model=schemas.OrderResponse)
async def cancel_order(
    order_id: int,
    profile: models.BusinessProfile = Depends(get_shopkeeper_profile),
    db: Session = Depends(get_db),
):
    """Cancel an order (shopkeeper only, only if sent/accepted)."""
    order = db.query(models.Order).filter(
        models.Order.id == order_id,
        models.Order.buyer_id == profile.id
    ).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    if order.status not in ["sent", "accepted"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel order in status: {order.status}"
        )

    order.status = "cancelled"
    db.commit()
    db.refresh(order)

    lines = db.query(models.OrderLine).filter(
        models.OrderLine.order_id == order.id
    ).all()

    return schemas.OrderResponse(
        **order.__dict__,
        items=[schemas.OrderLineResponse.model_validate(l) for l in lines]
    )


# -----------------------------
# Vendor Endpoints
# -----------------------------

@router.get("/vendor", response_model=List[schemas.OrderResponse])
async def list_vendor_orders(
    status: Optional[str] = Query(None, pattern="^(draft|sent|accepted|rejected|processing|shipped|delivered|cancelled)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    profile: models.BusinessProfile = Depends(get_vendor_profile),
    db: Session = Depends(get_db),
):
    """List orders received by current vendor."""
    stmt = select(models.Order).where(models.Order.vendor_id == profile.id)

    if status:
        stmt = stmt.where(models.Order.status == status)

    stmt = stmt.order_by(models.Order.created_at.desc())

    offset = (page - 1) * limit
    stmt = stmt.offset(offset).limit(limit)

    orders = db.scalars(stmt).all()

    result = []
    for order in orders:
        lines = db.query(models.OrderLine).filter(
            models.OrderLine.order_id == order.id
        ).all()
        result.append(schemas.OrderResponse(
            **order.__dict__,
            items=[schemas.OrderLineResponse.model_validate(l) for l in lines]
        ))

    return result


@router.patch("/vendor/{order_id}/status", response_model=schemas.OrderResponse)
async def update_order_status(
    order_id: int,
    payload: schemas.OrderStatusUpdate,
    profile: models.BusinessProfile = Depends(get_vendor_profile),
    db: Session = Depends(get_db),
):
    """Update order status (vendor only)."""
    order = db.query(models.Order).filter(
        models.Order.id == order_id,
        models.Order.vendor_id == profile.id
    ).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    # Validate status transition
    valid_transitions = {
        "sent": ["accepted", "rejected"],
        "accepted": ["processing", "rejected"],
        "processing": ["shipped", "rejected"],
        "shipped": ["delivered"],
        "delivered": [],
        "rejected": [],
        "cancelled": [],
    }

    if payload.status not in valid_transitions.get(order.status, []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status transition from {order.status} to {payload.status}"
        )

    order.status = payload.status
    db.commit()
    db.refresh(order)

    lines = db.query(models.OrderLine).filter(
        models.OrderLine.order_id == order.id
    ).all()

    return schemas.OrderResponse(
        **order.__dict__,
        items=[schemas.OrderLineResponse.model_validate(l) for l in lines]
    )