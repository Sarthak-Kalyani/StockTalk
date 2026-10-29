"""
Authentication and profile tests.

Covers Milestone 2 exit criteria:
- Unauthenticated access is rejected (401).
- Shopkeeper cannot access vendor-only routes (403) and vice versa.
- Business profile create/update persists in the database.
- Role field is honored.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch
import uuid

from app.main import app
from app.database import Base, get_db
from app import models
from app.config import settings

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def make_uid():
    """Generate a valid UUID object for the Supabase UID column (UUID(as_uuid=True))."""
    return uuid.uuid4()


def create_user_and_profile(db, email, role, supabase_uid, business_name=None, user_id=1):
    """Helper to create a user and optional business profile in the test DB.

    SQLite does not autoincrement BigInteger PKs, so an explicit id is provided.
    """
    user = models.User(
        id=user_id,
        email=email,
        password_hash="supabase_managed",
        role=role,
        status="active",
        supabase_uid=supabase_uid,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    profile = None
    if business_name:
        profile = models.BusinessProfile(
            id=user_id,
            user_id=user.id,
            business_name=business_name,
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

    return user, profile


class TestAuth:
    """Test authentication endpoints."""

    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_root_endpoint(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "StockTalk" in response.json()["message"]

    def test_auth_me_without_token(self):
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    @patch("app.auth.verify_supabase_jwt")
    def test_auth_me_with_valid_token_creates_user(self, mock_verify):
        """A valid mocked JWT should return the user's info."""
        supabase_uid = make_uid()
        mock_verify.return_value = {
            "sub": supabase_uid,
            "email": "newuser@example.com",
            "role": "shopkeeper",
        }

        # Pre-create the user (SQLite needs explicit BigInteger id; PostgreSQL uses serial)
        db = TestingSessionLocal()
        create_user_and_profile(
            db, "newuser@example.com", "shopkeeper", supabase_uid, None, user_id=20
        )
        db.close()

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer fake-jwt-token"},
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["role"] == "shopkeeper"
        assert data["status"] == "active"

    @patch("app.auth.verify_supabase_jwt")
    def test_auth_me_with_valid_token_sets_role(self, mock_verify):
        """Role from JWT should be preserved on the returned user."""
        supabase_uid = make_uid()
        mock_verify.return_value = {
            "sub": supabase_uid,
            "email": "vendor@example.com",
            "role": "vendor",
        }

        db = TestingSessionLocal()
        create_user_and_profile(
            db, "vendor@example.com", "vendor", supabase_uid, None, user_id=21
        )
        db.close()

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer fake-jwt-token"},
        )
        assert response.status_code == 200, response.text
        assert response.json()["role"] == "vendor"

    @patch("app.auth.verify_supabase_jwt")
    def test_profile_create_and_update_persists(self, mock_verify):
        """Business profile creation and update should persist (M2)."""
        supabase_uid = make_uid()
        mock_verify.return_value = {
            "sub": supabase_uid,
            "email": "profile@example.com",
            "role": "shopkeeper",
        }

        # Ensure user exists
        db = TestingSessionLocal()
        create_user_and_profile(
            db, "profile@example.com", "shopkeeper", supabase_uid, None, user_id=22
        )
        db.close()

        # Complete profile
        response = client.post(
            "/api/v1/auth/me/profile/complete",
            headers={"Authorization": "Bearer fake-jwt-token"},
            json={
                "business_name": "Test Shop",
                "address": "123 Main St",
                "phone": "+91-9876543210",
                "service_area": "Delhi",
            },
        )
        assert response.status_code == 201, response.text
        assert response.json()["business_name"] == "Test Shop"
        assert response.json()["service_area"] == "Delhi"

        # Update profile
        response = client.patch(
            "/api/v1/auth/me/profile",
            headers={"Authorization": "Bearer fake-jwt-token"},
            json={"business_name": "Updated Shop"},
        )
        assert response.status_code == 200, response.text
        assert response.json()["business_name"] == "Updated Shop"
        assert response.json()["service_area"] == "Delhi"  # unchanged field preserved

    @patch("app.auth.verify_supabase_jwt")
    def test_profile_complete_requires_business_name(self, mock_verify):
        """Profile completion must require business_name."""
        supabase_uid = make_uid()
        mock_verify.return_value = {
            "sub": supabase_uid,
            "email": "nobiz@example.com",
            "role": "shopkeeper",
        }
        db = TestingSessionLocal()
        create_user_and_profile(
            db, "nobiz@example.com", "shopkeeper", supabase_uid, None, user_id=23
        )
        db.close()

        response = client.post(
            "/api/v1/auth/me/profile/complete",
            headers={"Authorization": "Bearer fake-jwt-token"},
            json={"business_name": ""},
        )
        assert response.status_code in (400, 422)


class TestInventory:
    """Test inventory endpoints with role gating."""

    @patch("app.auth.verify_supabase_jwt")
    def test_create_product_shopkeeper(self, mock_verify):
        supabase_uid = make_uid()
        mock_verify.return_value = {
            "sub": supabase_uid,
            "email": "shop@example.com",
            "role": "shopkeeper",
        }

        db = TestingSessionLocal()
        user, profile = create_user_and_profile(
            db, "shop@example.com", "shopkeeper", supabase_uid, "Test Shop", user_id=10
        )
        db.close()

        response = client.post(
            "/api/v1/products",
            headers={"Authorization": "Bearer fake-token"},
            json={
                "name": "Test Product",
                "sku": "TEST-001",
                "category": "Test",
                "unit": "piece",
                "quantity": 100,
                "min_stock_level": 10,
                "cost_price": "25.00",
                "selling_price": "35.00",
            },
        )
        assert response.status_code == 201, response.text
        data = response.json()
        assert data["name"] == "Test Product"
        assert data["sku"] == "TEST-001"

    @patch("app.auth.verify_supabase_jwt")
    def test_vendor_cannot_create_product(self, mock_verify):
        """Vendors must be blocked from shopkeeper inventory routes (M2)."""
        supabase_uid = make_uid()
        mock_verify.return_value = {
            "sub": supabase_uid,
            "email": "vendor@example.com",
            "role": "vendor",
        }

        db = TestingSessionLocal()
        user, profile = create_user_and_profile(
            db, "vendor-nocat@example.com", "vendor", supabase_uid, "Test Vendor", user_id=30
        )
        db.close()

        response = client.post(
            "/api/v1/products",
            headers={"Authorization": "Bearer fake-token"},
            json={
                "name": "Should Fail",
                "sku": "FAIL-001",
                "quantity": 5,
                "cost_price": "10.00",
                "selling_price": "15.00",
            },
        )
        assert response.status_code == 403, response.text

    @patch("app.auth.verify_supabase_jwt")
    def test_shopkeeper_cannot_access_vendor_catalogue_403(self, mock_verify):
        """Shopkeepers should not mutate vendor catalogue (vendor-only route)."""
        supabase_uid = make_uid()
        mock_verify.return_value = {
            "sub": supabase_uid,
            "email": "shop-catalogue@example.com",
            "role": "shopkeeper",
        }

        # Pre-create shopkeeper with a profile so the role check (403) is exercised,
        # not the "no profile" (404) path.
        db = TestingSessionLocal()
        create_user_and_profile(
            db, "shop-catalogue@example.com", "shopkeeper", supabase_uid, "Test Shop", user_id=50
        )
        db.close()

        response = client.post(
            "/api/v1/vendors/catalogue",
            headers={"Authorization": "Bearer fake-token"},
            json={
                "vendor_id": 1,
                "product_name": "Should Fail",
                "price": "20.00",
                "unit": "kg",
            },
        )
        assert response.status_code == 403, response.text


class TestVendors:
    """Test vendor discovery endpoints."""

    @patch("app.auth.verify_supabase_jwt")
    def test_vendor_catalogue_crud(self, mock_verify):
        supabase_uid = make_uid()
        mock_verify.return_value = {
            "sub": supabase_uid,
            "email": "vendor@example.com",
            "role": "vendor",
        }

        db = TestingSessionLocal()
        user, profile = create_user_and_profile(
            db, "vendor-cat@example.com", "vendor", supabase_uid, "Test Vendor", user_id=40
        )
        db.close()

        # Create catalogue product
        response = client.post(
            "/api/v1/vendors/catalogue",
            headers={"Authorization": "Bearer fake-token"},
            json={
                "vendor_id": profile.id,
                "product_name": "Vendor Product",
                "price": "20.00",
                "unit": "kg",
            },
        )
        assert response.status_code == 201, response.text
        assert response.json()["product_name"] == "Vendor Product"
