# StockTalk API Contracts

**Version:** 1.0  
**Base URL:** `/api/v1`  
**Auth:** `Authorization: Bearer <supabase_jwt>`  
**Content-Type:** `application/json`

---

## 1. Common Patterns

### 1.1 Response Format

```json
// Success (single object)
{
  "data": { ... },
  "meta": { "timestamp": "2026-01-15T10:30:00Z" }
}

// Success (list with pagination)
{
  "data": [ ... ],
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "total_pages": 8,
    "timestamp": "2026-01-15T10:30:00Z"
  }
}

// Error
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input",
    "details": [
      { "field": "email", "message": "Invalid email format" }
    ]
  }
}
```

### 1.2 Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| `VALIDATION_ERROR` | 400 | Request body/query validation failed |
| `UNAUTHORIZED` | 401 | Missing or invalid token |
| `FORBIDDEN` | 403 | Token valid but insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Duplicate resource (e.g., duplicate bill) |
| `INTERNAL_ERROR` | 500 | Unexpected server error |
| `SERVICE_UNAVAILABLE` | 503 | External service (OCR, payment) unavailable |

### 1.3 Pagination

Query params: `?page=1&limit=20` (default page=1, limit=20, max limit=100)

### 1.4 Filtering & Sorting

- Filter: `?field=value` (exact), `?field__ilike=value` (partial), `?field__gte=value`, `?field__lte=value`
- Sort: `?sort=created_at:desc` or `?sort=-created_at`
- Search: `?search=term` (searches configured text fields)

---

## 2. Authentication Endpoints

### 2.1 Register (handled by Supabase Auth client-side)
```http
POST /auth/v1/signup
Content-Type: application/json

{
  "email": "shop@example.com",
  "password": "securepassword",
  "data": {
    "role": "shopkeeper",
    "business_name": "My Shop"
  }
}
```

### 2.2 Login (handled by Supabase Auth client-side)
```http
POST /auth/v1/token?grant_type=password
Content-Type: application/json

{
  "email": "shop@example.com",
  "password": "securepassword"
}
```

Response:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "expires_in": 3600,
  "token_type": "bearer",
  "user": { "id": "...", "email": "...", "role": "shopkeeper" }
}
```

### 2.3 Get Current User Profile
```http
GET /api/v1/auth/me
Authorization: Bearer <token>
```

Response:
```json
{
  "data": {
    "id": 1,
    "email": "shop@example.com",
    "role": "shopkeeper",
    "status": "active",
    "business_profile": {
      "id": 1,
      "business_name": "My Shop",
      "address": "123 Main St",
      "latitude": 28.6139,
      "longitude": 77.2090,
      "service_area": "Delhi",
      "phone": "+91-9876543210"
    }
  }
}
```

### 2.4 Update Profile
```http
PATCH /api/v1/auth/me
Authorization: Bearer <token>
Content-Type: application/json

{
  "business_name": "Updated Shop Name",
  "address": "456 New St",
  "phone": "+91-9876543210"
}
```

---

## 3. Inventory Endpoints

### 3.1 Create Product
```http
POST /api/v1/products
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Red Onions",
  "sku": "ONION-RED-1KG",
  "category": "Vegetables",
  "unit": "kg",
  "quantity": 100,
  "min_stock_level": 10,
  "cost_price": 25.00,
  "selling_price": 35.00,
  "vendor_id": 5
}
```

Response: `201 Created`
```json
{
  "data": {
    "id": 10,
    "business_id": 1,
    "name": "Red Onions",
    "sku": "ONION-RED-1KG",
    "category": "Vegetables",
    "unit": "kg",
    "quantity": 100,
    "min_stock_level": 10,
    "cost_price": "25.00",
    "selling_price": "35.00",
    "vendor_id": 5,
    "is_active": true,
    "created_at": "2026-01-15T10:30:00Z",
    "updated_at": "2026-01-15T10:30:00Z"
  }
}
```

### 3.2 List Products
```http
GET /api/v1/products?page=1&limit=20&search=onion&category=Vegetables&low_stock=false
Authorization: Bearer <token>
```

Query params:
- `search` — name/SKU partial match
- `category` — exact category
- `is_active` — true/false
- `low_stock` — true (quantity <= min_stock_level)
- `vendor_id` — filter by vendor
- `sort` — `name`, `quantity`, `cost_price`, `selling_price`, `created_at` (prefix `-` for desc)

Response: `200 OK` with paginated list

### 3.3 Get Product
```http
GET /api/v1/products/{id}
Authorization: Bearer <token>
```

### 3.4 Update Product
```http
PATCH /api/v1/products/{id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "quantity": 120,
  "selling_price": 38.00
}
```

### 3.5 Deactivate Product
```http
DELETE /api/v1/products/{id}
Authorization: Bearer <token>
```
Soft delete: sets `is_active = false`

### 3.6 Adjust Stock (Manual)
```http
POST /api/v1/products/{id}/stock-adjustment
Authorization: Bearer <token>
Content-Type: application/json

{
  "quantity_change": -5,
  "reason": "sale",
  "notes": "Sold to walk-in customer"
}
```
Creates `InventoryMovement` record, updates product quantity.

### 3.7 Stock Movements History
```http
GET /api/v1/products/{id}/movements?page=1&limit=50
Authorization: Bearer <token>
```

### 3.8 Low Stock Alerts
```http
GET /api/v1/inventory/low-stock
Authorization: Bearer <token>
```
Returns products where `quantity <= min_stock_level`

---

## 4. OCR & Bill Processing Endpoints

### 4.1 Upload Bill
```http
POST /api/v1/bills/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <image/pdf>
vendor_id: 5  (optional, for pre-association)
```

Response: `202 Accepted`
```json
{
  "data": {
    "bill_id": 25,
    "status": "processing",
    "message": "Bill uploaded, OCR started"
  }
}
```

### 4.2 Get Bill Status
```http
GET /api/v1/bills/{id}
Authorization: Bearer <token>
```

Response:
```json
{
  "data": {
    "id": 25,
    "business_id": 1,
    "vendor_id": 5,
    "invoice_number": "INV-2026-001",
    "invoice_date": "2026-01-10",
    "file_path": "bills/1/2026/01/inv-001.jpg",
    "ocr_status": "review_needed",
    "ocr_raw_json": { ... },
    "subtotal": "2500.00",
    "tax_total": "450.00",
    "grand_total": "2950.00",
    "confirmed": false,
    "line_items": [
      {
        "id": 1,
        "extracted_name": "Red Onions",
        "quantity": "100.000",
        "unit": "kg",
        "unit_price": "25.00",
        "tax": "4.50",
        "line_total": "2950.00",
        "matched_product_id": 10,
        "match_confidence": 0.92
      }
    ],
    "created_at": "2026-01-15T10:30:00Z"
  }
}
```

### 4.3 Review & Confirm Bill
```http
POST /api/v1/bills/{id}/confirm
Authorization: Bearer <token>
Content-Type: application/json

{
  "line_items": [
    {
      "id": 1,
      "product_id": 10,  // existing product ID or null for new
      "name": "Red Onions",
      "quantity": "100.000",
      "unit": "kg",
      "unit_price": "25.00",
      "tax": "4.50",
      "category": "Vegetables",
      "sku": "ONION-RED-1KG"
    }
  ],
  "vendor_id": 5,
  "invoice_number": "INV-2026-001",
  "invoice_date": "2026-01-10"
}
```

**Validation:**
- Duplicate check: same `vendor_id` + `invoice_number` + `invoice_date` → `409 CONFLICT`
- All line items must have valid data
- Atomic transaction: bill + line items + stock movements + price records

Response: `200 OK`
```json
{
  "data": {
    "bill_id": 25,
    "confirmed": true,
    "confirmed_at": "2026-01-15T10:35:00Z",
    "stock_movements_created": 1,
    "price_records_created": 1,
    "new_products_created": 0
  }
}
```

### 4.4 List Bills
```http
GET /api/v1/bills?page=1&limit=20&status=confirmed&vendor_id=5&date_from=2026-01-01&date_to=2026-01-31
Authorization: Bearer <token>
```

---

## 5. Vendor Discovery Endpoints

### 5.1 Vendor Profile (Vendor role)
```http
GET /api/v1/vendors/me
Authorization: Bearer <token>  // vendor role
```

### 5.2 Update Vendor Profile
```http
PATCH /api/v1/vendors/me
Authorization: Bearer <token>  // vendor role
Content-Type: application/json

{
  "business_name": "Fresh Veggies Co",
  "address": "Mandi Road",
  "latitude": 28.6562,
  "longitude": 77.2410,
  "service_area": "South Delhi",
  "service_radius_km": 15,
  "phone": "+91-9876543210",
  "gst_number": "07AAACF1234A1Z5"
}
```

### 5.3 Vendor Catalogue - Create Product
```http
POST /api/v1/vendors/catalogue
Authorization: Bearer <token>  // vendor role
Content-Type: application/json

{
  "product_name": "Red Onions",
  "description": "Fresh red onions from Nashik",
  "category": "Vegetables",
  "price": 22.00,
  "unit": "kg",
  "pack_size": 1,
  "available_quantity": 500,
  "is_available": true
}
```

### 5.4 Vendor Catalogue - List Own Products
```http
GET /api/v1/vendors/catalogue?page=1&limit=20&search=onion
Authorization: Bearer <token>  // vendor role
```

### 5.5 Vendor Location - Save/Update
```http
POST /api/v1/vendors/location
Authorization: Bearer <token>  // vendor role
Content-Type: application/json

{
  "latitude": 28.6562,
  "longitude": 77.2410,
  "address": "Mandi Road, Azadpur",
  "city": "Delhi",
  "service_radius_km": 15
}
```

### 5.6 Search Vendors (Shopkeeper) - By Area/City
```http
GET /api/v1/vendors/search?city=Delhi&product=onion&category=Vegetables&max_price=30
Authorization: Bearer <token>  // shopkeeper role
```

### 5.7 Search Vendors (Shopkeeper) - Nearby (GPS)
```http
GET /api/v1/vendors/nearby?latitude=28.6139&longitude=77.2090&radius_km=10&product=onion&max_price=30
Authorization: Bearer <token>  // shopkeeper role
```

Response:
```json
{
  "data": [
    {
      "vendor_id": 5,
      "business_name": "Fresh Veggies Co",
      "address": "Mandi Road, Azadpur",
      "city": "Delhi",
      "distance_km": 3.2,
      "service_radius_km": 15,
      "products": [
        {
          "id": 1,
          "name": "Red Onions",
          "category": "Vegetables",
          "price": "22.00",
          "unit": "kg",
          "available_quantity": 500
        }
      ]
    }
  ]
}
```

### 5.8 Price History for Product
```http
GET /api/v1/products/{product_id}/price-history?vendor_id=5
Authorization: Bearer <token>
```

Response:
```json
{
  "data": [
    {
      "id": 1,
      "vendor_id": 5,
      "vendor_name": "Fresh Veggies Co",
      "price": "25.00",
      "unit": "kg",
      "pack_size": 1,
      "tax_included": true,
      "date": "2026-01-10",
      "source": "bill",
      "source_id": 25
    },
    {
      "id": 2,
      "vendor_id": 5,
      "vendor_name": "Fresh Veggies Co",
      "price": "22.00",
      "unit": "kg",
      "pack_size": 1,
      "tax_included": true,
      "date": "2026-01-15",
      "source": "catalogue",
      "source_id": 1
    }
  ]
}
```

---

## 6. Chat Endpoints

### 6.1 Create/Get Conversation
```http
POST /api/v1/conversations
Authorization: Bearer <token>
Content-Type: application/json

{
  "vendor_id": 5  // shopkeeper initiates with vendor
}
```
If conversation exists, returns existing.

Response:
```json
{
  "data": {
    "id": 3,
    "shopkeeper_id": 1,
    "vendor_id": 5,
    "created_at": "2026-01-15T10:30:00Z",
    "vendor_name": "Fresh Veggies Co",
    "shopkeeper_name": "My Shop"
  }
}
```

### 6.2 List Conversations
```http
GET /api/v1/conversations
Authorization: Bearer <token>
```

### 6.3 Send Message
```http
POST /api/v1/conversations/{id}/messages
Authorization: Bearer <token>
Content-Type: application/json

{
  "content": "Hi, what's the price for 100kg onions?",
  "attachment_path": null  // or file upload handled separately
}
```

### 6.4 Get Messages
```http
GET /api/v1/conversations/{id}/messages?page=1&limit=50
Authorization: Bearer <token>
```

### 6.5 Upload Attachment
```http
POST /api/v1/conversations/{id}/attachments
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <image/pdf>
```
Returns signed URL for the uploaded file.

### 6.6 Mark Messages Read
```http
PATCH /api/v1/conversations/{id}/read
Authorization: Bearer <token>
```

---

## 7. Orders Endpoints

### 7.1 Create Order (Shopkeeper)
```http
POST /api/v1/orders
Authorization: Bearer <token>  // shopkeeper
Content-Type: application/json

{
  "vendor_id": 5,
  "items": [
    {
      "product_id": 10,
      "quantity": 50,
      "unit": "kg",
      "unit_price": 22.00
    }
  ],
  "delivery_address": "123 Main St, Delhi",
  "contact_phone": "+91-9876543210",
  "notes": "Deliver by Friday"
}
```

Response: `201 Created`
```json
{
  "data": {
    "id": 15,
    "buyer_id": 1,
    "vendor_id": 5,
    "status": "sent",
    "total_amount": "1100.00",
    "delivery_address": "123 Main St, Delhi",
    "contact_phone": "+91-9876543210",
    "items": [
      {
        "id": 1,
        "product_id": 10,
        "product_name": "Red Onions",
        "quantity": "50.000",
        "unit": "kg",
        "unit_price": "22.00",
        "line_total": "1100.00"
      }
    ],
    "created_at": "2026-01-15T11:00:00Z"
  }
}
```

### 7.2 List Orders (Shopkeeper)
```http
GET /api/v1/orders?status=sent&page=1&limit=20
Authorization: Bearer <token>  // shopkeeper
```

### 7.3 List Orders (Vendor)
```http
GET /api/v1/vendor/orders?status=sent&page=1&limit=20
Authorization: Bearer <token>  // vendor
```

### 7.4 Get Order Details
```http
GET /api/v1/orders/{id}
Authorization: Bearer <token>
```

### 7.5 Update Order Status (Vendor)
```http
PATCH /api/v1/vendor/orders/{id}/status
Authorization: Bearer <token>  // vendor
Content-Type: application/json

{
  "status": "accepted"  // accepted, rejected, processing, shipped, delivered
}
```

### 7.6 Cancel Order (Shopkeeper)
```http
PATCH /api/v1/orders/{id}/cancel
Authorization: Bearer <token>  // shopkeeper
```
Only if status is `sent` or `accepted`.

---

## 8. Payments Endpoints

### 8.1 Initiate Payment (Shopkeeper)
```http
POST /api/v1/orders/{id}/payment
Authorization: Bearer <token>  // shopkeeper
```

Response: `200 OK` — Returns Razorpay order details for frontend checkout
```json
{
  "data": {
    "razorpay_order_id": "order_ABC123",
    "amount": 110000,  // in paise
    "currency": "INR",
    "key_id": "rzp_test_...",
    "callback_url": "https://api.stocktalk.com/api/v1/payments/callback"
  }
}
```

### 8.2 Payment Callback (Razorpay Webhook)
```http
POST /api/v1/payments/callback
Content-Type: application/json
X-Razorpay-Signature: <signature>

{
  "event": "payment.captured",
  "payload": {
    "payment": {
      "entity": {
        "id": "pay_XYZ789",
        "order_id": "order_ABC123",
        "amount": 110000,
        "currency": "INR",
        "status": "captured"
      }
    }
  }
}
```
**Server-side verification** using webhook secret. Updates `payments` table, sets `verified=true`.

### 8.3 Get Payment Status
```http
GET /api/v1/orders/{id}/payment
Authorization: Bearer <token>
```

Response:
```json
{
  "data": {
    "id": 8,
    "order_id": 15,
    "provider": "razorpay",
    "provider_payment_id": "pay_XYZ789",
    "amount": "1100.00",
    "currency": "INR",
    "status": "success",
    "verified": true,
    "verified_at": "2026-01-15T11:05:00Z"
  }
}
```

---

## 9. Dashboard Endpoints

### 9.1 Shopkeeper Dashboard Summary
```http
GET /api/v1/dashboard/shopkeeper
Authorization: Bearer <token>  // shopkeeper
```

Response:
```json
{
  "data": {
    "total_products": 45,
    "low_stock_count": 3,
    "total_stock_value": "125000.00",
    "recent_bills": 5,
    "pending_orders": 2,
    "unread_messages": 4,
    "price_changes_today": 2
  }
}
```

### 9.2 Vendor Dashboard Summary
```http
GET /api/v1/dashboard/vendor
Authorization: Bearer <token>  // vendor
```

Response:
```json
{
  "data": {
    "catalogue_products": 30,
    "active_products": 28,
    "incoming_orders": 5,
    "pending_orders": 2,
    "unread_messages": 3,
    "total_sales_this_month": "45000.00"
  }
}
```

---

## 10. Webhooks (External)

### 10.1 Razorpay Payment Webhook
```http
POST /api/v1/webhooks/razorpay
X-Razorpay-Signature: <signature>
```
Handles: `payment.captured`, `payment.failed`, `order.paid`

### 10.2 Supabase Auth Webhook (if needed)
```http
POST /api/v1/webhooks/supabase-auth
```
Handles: user created, email confirmed, user deleted

---

## 11. Versioning & Deprecation

- **Current version**: v1 (in URL path)
- **Breaking changes** → new version (v2)
- **Deprecation notice**: 30 days via `Deprecation` header and docs
- **Backward compatibility**: Non-breaking additions (new optional fields, new endpoints) allowed in v1

---

*Update this document when API changes. Record decisions in `DECISIONS.md`.*