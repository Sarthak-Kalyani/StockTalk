"""
Dashboard API Routes
"""
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_

from app.auth import get_current_user, get_shopkeeper_profile, get_vendor_profile
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/shopkeeper", response_model=schemas.ShopkeeperDashboardResponse)
async def shopkeeper_dashboard(
    profile: models.BusinessProfile = Depends(get_shopkeeper_profile),
    db: Session = Depends(get_db),
):
    """Get shopkeeper dashboard summary."""
    # Total products
    total_products = db.query(func.count(models.Product.id)).filter(
        models.Product.business_id == profile.id,
        models.Product.is_active == True
    ).scalar() or 0

    # Low stock count
    low_stock_count = db.query(func.count(models.Product.id)).filter(
        models.Product.business_id == profile.id,
        models.Product.is_active == True,
        models.Product.quantity <= models.Product.min_stock_level
    ).scalar() or 0

    # Total stock value (quantity * cost_price)
    stock_value = db.query(func.sum(models.Product.quantity * models.Product.cost_price)).filter(
        models.Product.business_id == profile.id,
        models.Product.is_active == True
    ).scalar() or Decimal("0")

    # Recent bills (last 7 days)
    week_ago = date.today() - timedelta(days=7)
    recent_bills = db.query(func.count(models.PurchaseBill.id)).filter(
        models.PurchaseBill.business_id == profile.id,
        models.PurchaseBill.confirmed == True,
        models.PurchaseBill.invoice_date >= week_ago
    ).scalar() or 0

    # Pending orders (sent, accepted, processing)
    pending_orders = db.query(func.count(models.Order.id)).filter(
        models.Order.buyer_id == profile.id,
        models.Order.status.in_(["sent", "accepted", "processing", "shipped"])
    ).scalar() or 0

    # Unread messages
    # Get conversations for this shopkeeper
    conversations = db.query(models.Conversation.id).filter(
        models.Conversation.shopkeeper_id == profile.id
    ).subquery()

    unread_messages = db.query(func.count(models.Message.id)).filter(
        models.Message.conversation_id.in_(select(conversations)),
        models.Message.sender_id != profile.user_id,
        models.Message.is_read == False
    ).scalar() or 0

    # Price changes today (price records from bills today)
    price_changes_today = db.query(func.count(models.PriceRecord.id)).filter(
        models.PriceRecord.product_id.in_(
            select(models.Product.id).where(models.Product.business_id == profile.id)
        ),
        models.PriceRecord.date == date.today(),
        models.PriceRecord.source == "bill"
    ).scalar() or 0

    return schemas.ShopkeeperDashboardResponse(
        total_products=total_products,
        low_stock_count=low_stock_count,
        total_stock_value=stock_value,
        recent_bills=recent_bills,
        pending_orders=pending_orders,
        unread_messages=unread_messages,
        price_changes_today=price_changes_today,
    )


@router.get("/vendor", response_model=schemas.VendorDashboardResponse)
async def vendor_dashboard(
    profile: models.BusinessProfile = Depends(get_vendor_profile),
    db: Session = Depends(get_db),
):
    """Get vendor dashboard summary."""
    # Catalogue products
    catalogue_products = db.query(func.count(models.VendorCatalogue.id)).filter(
        models.VendorCatalogue.vendor_id == profile.id
    ).scalar() or 0

    # Active products
    active_products = db.query(func.count(models.VendorCatalogue.id)).filter(
        models.VendorCatalogue.vendor_id == profile.id,
        models.VendorCatalogue.is_available == True
    ).scalar() or 0

    # Incoming orders (sent, accepted)
    incoming_orders = db.query(func.count(models.Order.id)).filter(
        models.Order.vendor_id == profile.id,
        models.Order.status.in_(["sent", "accepted"])
    ).scalar() or 0

    # Pending orders (processing, shipped)
    pending_orders = db.query(func.count(models.Order.id)).filter(
        models.Order.vendor_id == profile.id,
        models.Order.status.in_(["processing", "shipped"])
    ).scalar() or 0

    # Unread messages
    conversations = db.query(models.Conversation.id).filter(
        models.Conversation.vendor_id == profile.id
    ).subquery()

    unread_messages = db.query(func.count(models.Message.id)).filter(
        models.Message.conversation_id.in_(select(conversations)),
        models.Message.sender_id != profile.user_id,
        models.Message.is_read == False
    ).scalar() or 0

    # Total sales this month (delivered orders)
    month_start = date.today().replace(day=1)
    total_sales = db.query(func.sum(models.Order.total_amount)).filter(
        models.Order.vendor_id == profile.id,
        models.Order.status == "delivered",
        models.Order.created_at >= month_start
    ).scalar() or Decimal("0")

    return schemas.VendorDashboardResponse(
        catalogue_products=catalogue_products,
        active_products=active_products,
        incoming_orders=incoming_orders,
        pending_orders=pending_orders,
        unread_messages=unread_messages,
        total_sales_this_month=total_sales,
    )