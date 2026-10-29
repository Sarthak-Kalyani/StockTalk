"""
Bills / OCR API Routes
"""
import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.auth import get_current_user, get_shopkeeper_profile
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/bills", tags=["Bills & OCR"])


@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_bill(
    file: UploadFile = File(...),
    vendor_id: Optional[int] = None,
    user: models.User = Depends(get_current_user),
    profile: models.BusinessProfile = Depends(get_shopkeeper_profile),
    db: Session = Depends(get_db),
):
    """
    Upload a bill image/PDF for OCR processing.
    Returns bill_id for status polling.
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp", "application/pdf"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_types)}"
        )

    # Validate file size (max 10MB)
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 10MB limit"
        )

    # Generate storage path
    file_ext = file.filename.split(".")[-1].lower()
    storage_path = f"bills/{profile.id}/{date.today().year}/{date.today().month:02d}/{uuid.uuid4()}.{file_ext}"

    # TODO: Upload to Supabase Storage
    # For now, simulate with local path
    # In production: supabase.storage.from_(settings.supabase_storage_bucket_bills).upload(storage_path, content)

    # Create bill record with pending OCR
    bill = models.PurchaseBill(
        business_id=profile.id,
        vendor_id=vendor_id or 0,  # Will be updated from OCR or review
        invoice_number="",  # Will be extracted
        invoice_date=date.today(),  # Will be extracted
        file_path=storage_path,
        ocr_status="processing",
    )
    db.add(bill)
    db.commit()
    db.refresh(bill)

    # TODO: Trigger OCR processing (async task)
    # For now, simulate OCR completion
    # In production: queue OCR job (Celery, background task, or Supabase Edge Function)

    return {
        "bill_id": bill.id,
        "status": "processing",
        "message": "Bill uploaded. OCR processing started."
    }


@router.get("/{bill_id}", response_model=schemas.PurchaseBillResponse)
async def get_bill(
    bill_id: int,
    profile: models.BusinessProfile = Depends(get_shopkeeper_profile),
    db: Session = Depends(get_db),
):
    """Get bill details with line items for review."""
    bill = db.query(models.PurchaseBill).filter(
        models.PurchaseBill.id == bill_id,
        models.PurchaseBill.business_id == profile.id
    ).first()

    if not bill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bill not found"
        )

    # Get line items
    line_items = db.query(models.PurchaseBillLine).filter(
        models.PurchaseBillLine.bill_id == bill_id
    ).all()

    # Build response with match confidence
    items_response = []
    for item in line_items:
        match_confidence = None
        if item.product_id:
            product = db.query(models.Product).filter(
                models.Product.id == item.product_id
            ).first()
            if product:
                # Simple name similarity for demo
                match_confidence = 0.9 if product.name.lower() == item.extracted_name.lower() else 0.7

        items_response.append(schemas.BillLineItemReview(
            id=item.id,
            extracted_name=item.extracted_name,
            quantity=item.quantity,
            unit=item.unit,
            unit_price=item.unit_price,
            tax=item.tax,
            line_total=item.line_total,
            product_id=item.product_id,
            match_confidence=match_confidence,
        ))

    return schemas.PurchaseBillResponse(
        **bill.__dict__,
        line_items=items_response
    )


@router.post("/{bill_id}/confirm", response_model=schemas.PurchaseBillResponse)
async def confirm_bill(
    bill_id: int,
    payload: schemas.BillConfirmRequest,
    user: models.User = Depends(get_current_user),
    profile: models.BusinessProfile = Depends(get_shopkeeper_profile),
    db: Session = Depends(get_db),
):
    """
    Confirm bill after review.
    Atomic transaction: saves bill, creates/updates products, creates stock movements, price records.
    """
    bill = db.query(models.PurchaseBill).filter(
        models.PurchaseBill.id == bill_id,
        models.PurchaseBill.business_id == profile.id
    ).first()

    if not bill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bill not found"
        )

    if bill.confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bill already confirmed"
        )

    # Check for duplicate (vendor + invoice_number + invoice_date)
    existing = db.query(models.PurchaseBill).filter(
        models.PurchaseBill.vendor_id == payload.vendor_id,
        models.PurchaseBill.invoice_number == payload.invoice_number,
        models.PurchaseBill.invoice_date == payload.invoice_date,
        models.PurchaseBill.id != bill_id,
        models.PurchaseBill.confirmed == True
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Duplicate bill detected. Bill #{existing.id} already confirmed with same vendor/invoice/date."
        )

    # Validate vendor exists
    vendor = db.query(models.BusinessProfile).filter(
        models.BusinessProfile.id == payload.vendor_id
    ).first()
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )

    # Process line items
    stock_movements_created = 0
    price_records_created = 0
    new_products_created = 0

    for line_item in payload.line_items:
        product = None

        if line_item.product_id:
            # Existing product
            product = db.query(models.Product).filter(
                models.Product.id == line_item.product_id,
                models.Product.business_id == profile.id
            ).first()
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product {line_item.product_id} not found"
                )
        else:
            # Create new product
            product = models.Product(
                business_id=profile.id,
                name=line_item.name,
                sku=line_item.sku,
                category=line_item.category,
                unit=line_item.unit,
                quantity=0,
                min_stock_level=0,
                cost_price=line_item.unit_price,
                selling_price=line_item.unit_price * Decimal("1.2"),  # Default 20% margin
                vendor_id=payload.vendor_id,
            )
            db.add(product)
            db.flush()  # Get ID
            new_products_created += 1

        # Update product with new cost price (WAC calculation)
        if product.quantity > 0:
            # Weighted Average Cost
            total_cost = (product.quantity * product.cost_price) + (line_item.quantity * line_item.unit_price)
            total_qty = product.quantity + line_item.quantity
            product.cost_price = total_cost / total_qty
        else:
            product.cost_price = line_item.unit_price

        # Update quantity
        product.quantity += line_item.quantity

        # Create stock movement
        movement = models.InventoryMovement(
            product_id=product.id,
            quantity_change=line_item.quantity,
            reason="bill",
            source="bill_upload",
            actor_id=user.id,
            related_bill_id=bill.id,
            notes=f"Bill {payload.invoice_number} from {vendor.business_name}",
        )
        db.add(movement)
        stock_movements_created += 1

        # Create price record
        price_record = models.PriceRecord(
            product_id=product.id,
            vendor_id=payload.vendor_id,
            price=line_item.unit_price,
            unit=line_item.unit,
            pack_size=Decimal("1"),
            tax_included=True,
            date=payload.invoice_date,
            source="bill",
            source_id=bill.id,
        )
        db.add(price_record)
        price_records_created += 1

        # Update bill line with matched product
        line = db.query(models.PurchaseBillLine).filter(
            models.PurchaseBillLine.bill_id == bill_id,
            models.PurchaseBillLine.extracted_name == line_item.extracted_name
        ).first()
        if line:
            line.product_id = product.id

    # Update bill
    bill.vendor_id = payload.vendor_id
    bill.invoice_number = payload.invoice_number
    bill.invoice_date = payload.invoice_date
    bill.confirmed = True
    bill.confirmed_at = datetime.utcnow()
    bill.confirmed_by = user.id
    bill.ocr_status = "completed"

    # Calculate totals
    subtotal = sum(item.quantity * item.unit_price for item in payload.line_items)
    tax_total = sum(item.tax for item in payload.line_items)
    bill.subtotal = subtotal
    bill.tax_total = tax_total
    bill.grand_total = subtotal + tax_total

    db.commit()
    db.refresh(bill)

    return {
        "bill_id": bill.id,
        "confirmed": True,
        "confirmed_at": bill.confirmed_at,
        "stock_movements_created": stock_movements_created,
        "price_records_created": price_records_created,
        "new_products_created": new_products_created,
    }


@router.get("", response_model=List[schemas.PurchaseBillResponse])
async def list_bills(
    status: Optional[str] = Query(None, pattern="^(pending|processing|completed|failed|review_needed)$"),
    confirmed: Optional[bool] = None,
    vendor_id: Optional[int] = Query(None, gt=0),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    profile: models.BusinessProfile = Depends(get_shopkeeper_profile),
    db: Session = Depends(get_db),
):
    """List bills with filtering."""
    stmt = select(models.PurchaseBill).where(
        models.PurchaseBill.business_id == profile.id
    )

    if status:
        stmt = stmt.where(models.PurchaseBill.ocr_status == status)
    if confirmed is not None:
        stmt = stmt.where(models.PurchaseBill.confirmed == confirmed)
    if vendor_id:
        stmt = stmt.where(models.PurchaseBill.vendor_id == vendor_id)
    if date_from:
        stmt = stmt.where(models.PurchaseBill.invoice_date >= date_from)
    if date_to:
        stmt = stmt.where(models.PurchaseBill.invoice_date <= date_to)

    stmt = stmt.order_by(models.PurchaseBill.created_at.desc())

    offset = (page - 1) * limit
    stmt = stmt.offset(offset).limit(limit)

    bills = db.scalars(stmt).all()

    # Load line items for each bill
    result = []
    for bill in bills:
        line_items = db.query(models.PurchaseBillLine).filter(
            models.PurchaseBillLine.bill_id == bill.id
        ).all()

        items_response = [
            schemas.BillLineItemReview(
                id=item.id,
                extracted_name=item.extracted_name,
                quantity=item.quantity,
                unit=item.unit,
                unit_price=item.unit_price,
                tax=item.tax,
                line_total=item.line_total,
                product_id=item.product_id,
            )
            for item in line_items
        ]

        result.append(schemas.PurchaseBillResponse(
            **bill.__dict__,
            line_items=items_response
        ))

    return result