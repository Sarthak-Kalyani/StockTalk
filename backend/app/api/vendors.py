"""
Vendor Discovery API Routes
"""
import math
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, or_

from app.auth import get_current_user, get_shopkeeper_profile, get_vendor_profile
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/vendors", tags=["Vendor Discovery"])


def calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates using Haversine formula."""
    earth_radius_km = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)
    a = max(0.0, min(1.0, a))
    return 2 * earth_radius_km * math.asin(math.sqrt(a))


# -----------------------------
# Vendor Profile (Vendor role)
# -----------------------------

@router.get("/me", response_model=schemas.BusinessProfileResponse)
async def get_vendor_profile_endpoint(
    profile: models.BusinessProfile = Depends(get_vendor_profile),
):
    """Get current vendor's profile."""
    return profile


@router.patch("/me", response_model=schemas.BusinessProfileResponse)
async def update_vendor_profile(
    payload: schemas.UserProfileUpdate,
    profile: models.BusinessProfile = Depends(get_vendor_profile),
    db: Session = Depends(get_db),
):
    """Update vendor profile."""
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return profile


# -----------------------------
# Vendor Catalogue (Vendor role)
# -----------------------------

@router.post("/catalogue", response_model=schemas.CatalogueResponse, status_code=status.HTTP_201_CREATED)
async def create_catalogue_product(
    payload: schemas.CatalogueCreate,
    profile: models.BusinessProfile = Depends(get_vendor_profile),
    db: Session = Depends(get_db),
):
    """Add a product to vendor's catalogue."""
    if payload.vendor_id != profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only add products to your own catalogue"
        )

    product = models.VendorCatalogue(
        vendor_id=profile.id,
        **{k: v for k, v in payload.model_dump().items() if k != "vendor_id"}
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/catalogue", response_model=List[schemas.CatalogueResponse])
async def list_my_catalogue(
    search: Optional[str] = Query(None, max_length=150),
    category: Optional[str] = Query(None, max_length=100),
    is_available: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    profile: models.BusinessProfile = Depends(get_vendor_profile),
    db: Session = Depends(get_db),
):
    """List vendor's own catalogue products."""
    stmt = select(models.VendorCatalogue).where(
        models.VendorCatalogue.vendor_id == profile.id
    )

    if search:
        stmt = stmt.where(models.VendorCatalogue.product_name.ilike(f"%{search}%"))
    if category:
        stmt = stmt.where(models.VendorCatalogue.category.ilike(f"%{category}%"))
    if is_available is not None:
        stmt = stmt.where(models.VendorCatalogue.is_available == is_available)

    stmt = stmt.order_by(models.VendorCatalogue.product_name)

    offset = (page - 1) * limit
    stmt = stmt.offset(offset).limit(limit)

    return db.scalars(stmt).all()


@router.get("/catalogue/{product_id}", response_model=schemas.CatalogueResponse)
async def get_catalogue_product(
    product_id: int,
    profile: models.BusinessProfile = Depends(get_vendor_profile),
    db: Session = Depends(get_db),
):
    """Get a catalogue product."""
    product = db.query(models.VendorCatalogue).filter(
        models.VendorCatalogue.id == product_id,
        models.VendorCatalogue.vendor_id == profile.id
    ).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Catalogue product not found"
        )
    return product


@router.patch("/catalogue/{product_id}", response_model=schemas.CatalogueResponse)
async def update_catalogue_product(
    product_id: int,
    payload: schemas.CatalogueUpdate,
    profile: models.BusinessProfile = Depends(get_vendor_profile),
    db: Session = Depends(get_db),
):
    """Update a catalogue product."""
    product = db.query(models.VendorCatalogue).filter(
        models.VendorCatalogue.id == product_id,
        models.VendorCatalogue.vendor_id == profile.id
    ).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Catalogue product not found"
        )

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)
    return product


@router.delete("/catalogue/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_catalogue_product(
    product_id: int,
    profile: models.BusinessProfile = Depends(get_vendor_profile),
    db: Session = Depends(get_db),
):
    """Delete a catalogue product."""
    product = db.query(models.VendorCatalogue).filter(
        models.VendorCatalogue.id == product_id,
        models.VendorCatalogue.vendor_id == profile.id
    ).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Catalogue product not found"
        )

    db.delete(product)
    db.commit()


# -----------------------------
# Vendor Location (Vendor role)
# -----------------------------

@router.post("/location", response_model=schemas.VendorLocationResponse, status_code=status.HTTP_201_CREATED)
async def save_vendor_location(
    payload: schemas.VendorLocationCreate,
    profile: models.BusinessProfile = Depends(get_vendor_profile),
    db: Session = Depends(get_db),
):
    """Save or update vendor location."""
    if payload.vendor_id != profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only save location for your own profile"
        )

    location = db.query(models.VendorLocation).filter(
        models.VendorLocation.vendor_id == profile.id
    ).first()

    if location is None:
        location = models.VendorLocation(**payload.model_dump())
        db.add(location)
    else:
        for key, value in payload.model_dump().items():
            setattr(location, key, value)

    db.commit()
    db.refresh(location)
    return location


@router.get("/location", response_model=schemas.VendorLocationResponse)
async def get_vendor_location(
    profile: models.BusinessProfile = Depends(get_vendor_profile),
    db: Session = Depends(get_db),
):
    """Get vendor's saved location."""
    location = db.query(models.VendorLocation).filter(
        models.VendorLocation.vendor_id == profile.id
    ).first()

    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not set"
        )
    return location


# -----------------------------
# Vendor Search (Shopkeeper role)
# -----------------------------

@router.get("/search", response_model=List[schemas.VendorSearchResult])
async def search_vendors(
    city: Optional[str] = Query(None, max_length=100),
    product: Optional[str] = Query(None, max_length=150),
    category: Optional[str] = Query(None, max_length=100),
    max_price: Optional[float] = Query(None, ge=0),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    profile: models.BusinessProfile = Depends(get_shopkeeper_profile),
    db: Session = Depends(get_db),
):
    """
    Search vendors by city/area and product.
    Manual search fallback when GPS not available.
    """
    # Join vendor_locations with vendor_catalogue and business_profiles
    stmt = select(
        models.VendorLocation,
        models.BusinessProfile,
    ).join(
        models.BusinessProfile,
        models.VendorLocation.vendor_id == models.BusinessProfile.id
    ).where(
        models.BusinessProfile.id != profile.id  # Exclude self
    )

    if city:
        stmt = stmt.where(models.VendorLocation.city.ilike(f"%{city}%"))

    locations = db.execute(stmt).all()

    results = []
    for location, vendor_profile in locations:
        # Get matching products
        product_stmt = select(models.VendorCatalogue).where(
            models.VendorCatalogue.vendor_id == vendor_profile.id,
            models.VendorCatalogue.is_available == True,
        )

        if product:
            product_stmt = product_stmt.where(
                models.VendorCatalogue.product_name.ilike(f"%{product}%")
            )
        if category:
            product_stmt = product_stmt.where(
                models.VendorCatalogue.category.ilike(f"%{category}%")
            )
        if max_price is not None:
            product_stmt = product_stmt.where(
                models.VendorCatalogue.price <= max_price
            )

        products = db.scalars(product_stmt).all()

        if product and not products:
            continue  # Skip vendors without matching product

        results.append(schemas.VendorSearchResult(
            vendor_id=vendor_profile.id,
            business_name=vendor_profile.business_name,
            address=location.address,
            city=location.city,
            distance_km=0.0,  # No GPS distance for manual search
            service_radius_km=location.service_radius_km,
            products=[
                {
                    "id": p.id,
                    "name": p.product_name,
                    "category": p.category,
                    "price": float(p.price),
                    "unit": p.unit,
                    "available_quantity": p.available_quantity,
                }
                for p in products
            ],
        ))

    # Paginate
    offset = (page - 1) * limit
    return results[offset:offset + limit]


@router.get("/nearby", response_model=List[schemas.VendorSearchResult])
async def find_nearby_vendors(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(default=10, gt=0, le=500),
    product: Optional[str] = Query(None, max_length=150),
    category: Optional[str] = Query(None, max_length=100),
    max_price: Optional[float] = Query(None, ge=0),
    profile: models.BusinessProfile = Depends(get_shopkeeper_profile),
    db: Session = Depends(get_db),
):
    """
    Find nearby vendors using GPS coordinates.
    Filters by distance and vendor's service radius.
    """
    locations = db.scalars(select(models.VendorLocation)).all()

    results = []
    for location in locations:
        vendor_profile = db.query(models.BusinessProfile).filter(
            models.BusinessProfile.id == location.vendor_id
        ).first()

        if not vendor_profile or vendor_profile.id == profile.id:
            continue

        distance = calculate_distance_km(
            latitude, longitude,
            location.latitude, location.longitude
        )

        # Check search radius
        if distance > radius_km:
            continue

        # Check vendor's service radius
        if distance > location.service_radius_km:
            continue

        # Get matching products
        product_stmt = select(models.VendorCatalogue).where(
            models.VendorCatalogue.vendor_id == location.vendor_id,
            models.VendorCatalogue.is_available == True,
        )

        if product:
            product_stmt = product_stmt.where(
                models.VendorCatalogue.product_name.ilike(f"%{product}%")
            )
        if category:
            product_stmt = product_stmt.where(
                models.VendorCatalogue.category.ilike(f"%{category}%")
            )
        if max_price is not None:
            product_stmt = product_stmt.where(
                models.VendorCatalogue.price <= max_price
            )

        products = db.scalars(product_stmt).all()

        if product and not products:
            continue

        results.append(schemas.VendorSearchResult(
            vendor_id=vendor_profile.id,
            business_name=vendor_profile.business_name,
            address=location.address,
            city=location.city,
            distance_km=round(distance, 2),
            service_radius_km=location.service_radius_km,
            products=[
                {
                    "id": p.id,
                    "name": p.product_name,
                    "category": p.category,
                    "price": float(p.price),
                    "unit": p.unit,
                    "available_quantity": p.available_quantity,
                }
                for p in products
            ],
        ))

    # Sort by distance
    results.sort(key=lambda v: v.distance_km)
    return results


# -----------------------------
# Price Comparison
# -----------------------------

@router.get("/price-comparison/{product_name}", response_model=List[schemas.PriceRecordResponse])
async def compare_prices(
    product_name: str,
    unit: Optional[str] = Query(None, max_length=30),
    category: Optional[str] = Query(None, max_length=100),
    profile: models.BusinessProfile = Depends(get_shopkeeper_profile),
    db: Session = Depends(get_db),
):
    """
    Compare prices for a product across vendors.
    Searches vendor catalogues for comparable products.
    """
    stmt = select(
        models.VendorCatalogue,
        models.BusinessProfile,
    ).join(
        models.BusinessProfile,
        models.VendorCatalogue.vendor_id == models.BusinessProfile.id
    ).where(
        models.VendorCatalogue.is_available == True,
        models.VendorCatalogue.product_name.ilike(f"%{product_name}%"),
        models.BusinessProfile.id != profile.id,
    )

    if unit:
        stmt = stmt.where(models.VendorCatalogue.unit == unit)
    if category:
        stmt = stmt.where(models.VendorCatalogue.category.ilike(f"%{category}%"))

    results = db.execute(stmt).all()

    response = []
    for catalogue, vendor_profile in results:
        response.append(schemas.PriceRecordResponse(
            id=catalogue.id,
            product_id=0,  # Catalogue product, not inventory product
            vendor_id=vendor_profile.id,
            vendor_name=vendor_profile.business_name,
            price=catalogue.price,
            unit=catalogue.unit,
            pack_size=catalogue.pack_size,
            tax_included=True,  # Assume catalogue prices include tax
            date=date.today(),
            source="catalogue",
            source_id=catalogue.id,
        ))

    return response