"""
Payments API Routes
"""
import hmac
import hashlib
import json
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/orders/{order_id}/initiate", response_model=schemas.RazorpayOrderResponse)
async def initiate_payment(
    order_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Initiate Razorpay payment for an order.
    Returns Razorpay order details for frontend checkout.
    """
    order = db.query(models.Order).filter(models.Order.id == order_id).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    # Verify user is buyer
    profile = db.query(models.BusinessProfile).filter(
        models.BusinessProfile.user_id == user.id
    ).first()

    if not profile or order.buyer_id != profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the buyer can initiate payment"
        )

    if order.status not in ["accepted", "processing", "shipped"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot pay for order in status: {order.status}"
        )

    # Check if payment already exists and is successful
    existing_payment = db.query(models.Payment).filter(
        models.Payment.order_id == order_id,
        models.Payment.status == "success"
    ).first()

    if existing_payment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment already completed for this order"
        )

    # TODO: Create Razorpay order via Razorpay API
    # import razorpay
    # client = razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))
    # razorpay_order = client.order.create({
    #     "amount": int(order.total_amount * 100),  # Convert to paise
    #     "currency": "INR",
    #     "receipt": f"order_{order_id}",
    #     "payment_capture": 1
    # })

    # Mock response for development
    razorpay_order_id = f"order_mock_{order_id}"
    amount_paise = int(order.total_amount * 100)

    # Create payment record
    payment = models.Payment(
        order_id=order.id,
        provider="razorpay",
        provider_order_id=razorpay_order_id,
        amount=order.total_amount,
        currency="INR",
        status="pending",
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    return schemas.RazorpayOrderResponse(
        razorpay_order_id=razorpay_order_id,
        amount=amount_paise,
        currency="INR",
        key_id=settings.razorpay_key_id or "rzp_test_mock",
        callback_url=f"{settings.supabase_url}/api/v1/payments/callback" if settings.supabase_url else "http://localhost:8000/api/v1/payments/callback"
    )


@router.get("/orders/{order_id}", response_model=schemas.PaymentResponse)
async def get_payment_status(
    order_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get payment status for an order."""
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
            detail="Not authorized to view this payment"
        )

    payment = db.query(models.Payment).filter(
        models.Payment.order_id == order_id
    ).order_by(models.Payment.created_at.desc()).first()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No payment found for this order"
        )

    return payment


@router.post("/callback")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    Razorpay webhook endpoint for payment verification.
    Server-side verification - never trust frontend alone.
    """
    body = await request.body()
    payload = json.loads(body)

    # Verify webhook signature
    if settings.razorpay_webhook_secret and x_razorpay_signature:
        expected_signature = hmac.new(
            settings.razorpay_webhook_secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(expected_signature, x_razorpay_signature):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid webhook signature"
            )

    # Handle payment.captured event
    event = payload.get("event")
    if event == "payment.captured":
        payment_data = payload.get("payload", {}).get("payment", {}).get("entity", {})
        razorpay_payment_id = payment_data.get("id")
        razorpay_order_id = payment_data.get("order_id")
        amount = payment_data.get("amount", 0) / 100  # Convert from paise
        currency = payment_data.get("currency", "INR")
        payment_status = payment_data.get("status")

        # Find payment record
        payment = db.query(models.Payment).filter(
            models.Payment.provider_order_id == razorpay_order_id
        ).first()

        if payment:
            payment.provider_payment_id = razorpay_payment_id
            payment.amount = Decimal(str(amount))
            payment.currency = currency
            payment.status = "success" if payment_status == "captured" else "failed"
            payment.verified = True
            payment.verified_at = datetime.utcnow()
            payment.webhook_payload = payload

            # Update order status if payment successful
            if payment.status == "success":
                order = db.query(models.Order).filter(models.Order.id == payment.order_id).first()
                if order and order.status in ["accepted", "processing"]:
                    order.status = "processing"  # Ready for fulfillment

            db.commit()
            db.refresh(payment)

    elif event == "payment.failed":
        payment_data = payload.get("payload", {}).get("payment", {}).get("entity", {})
        razorpay_order_id = payment_data.get("order_id")

        payment = db.query(models.Payment).filter(
            models.Payment.provider_order_id == razorpay_order_id
        ).first()

        if payment:
            payment.status = "failed"
            payment.webhook_payload = payload
            db.commit()

    return {"status": "ok"}


@router.post("/verify-manual")
async def verify_payment_manual(
    order_id: int,
    razorpay_payment_id: str,
    razorpay_order_id: str,
    razorpay_signature: str,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Manual payment verification (fallback if webhook missed).
    Verifies Razorpay signature server-side.
    """
    order = db.query(models.Order).filter(models.Order.id == order_id).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    profile = db.query(models.BusinessProfile).filter(
        models.BusinessProfile.user_id == user.id
    ).first()

    if not profile or order.buyer_id != profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the buyer can verify payment"
        )

    # Verify signature
    if settings.razorpay_key_secret:
        payload = f"{razorpay_order_id}|{razorpay_payment_id}"
        expected_signature = hmac.new(
            settings.razorpay_key_secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(expected_signature, razorpay_signature):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid payment signature"
            )

    # Update payment record
    payment = db.query(models.Payment).filter(
        models.Payment.order_id == order_id,
        models.Payment.provider_order_id == razorpay_order_id
    ).first()

    if not payment:
        payment = models.Payment(
            order_id=order_id,
            provider="razorpay",
            provider_order_id=razorpay_order_id,
            provider_payment_id=razorpay_payment_id,
            provider_signature=razorpay_signature,
            amount=order.total_amount,
            currency="INR",
        )
        db.add(payment)

    payment.provider_payment_id = razorpay_payment_id
    payment.provider_signature = razorpay_signature
    payment.status = "success"
    payment.verified = True
    payment.verified_at = datetime.utcnow()

    # Update order status
    if order.status in ["accepted", "processing"]:
        order.status = "processing"

    db.commit()
    db.refresh(payment)

    return {"status": "verified", "payment_id": payment.id}