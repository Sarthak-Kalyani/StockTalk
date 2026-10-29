# StockTalk Architecture Document

**Version:** 1.0  
**Project:** StockTalk — B2B Inventory and Supplier Communication Platform  
**Institute:** G.L. Bajaj Institute of Technology & Management, Greater Noida  
**Department:** Computer Science & Engineering  
**Group ID:** GC_2026_018  
**Session:** 2026–27

---

## 1. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            STOCKTALK SYSTEM                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐     ┌──────────────┐     ┌────────────────────────────┐  │
│  │   FRONTEND   │────▶│   BACKEND    │────▶│       DATABASE             │  │
│  │  (React.js)  │     │  (FastAPI)   │     │   (PostgreSQL/Supabase)    │  │
│  │              │     │              │     │                            │  │
│  │  - Dashboard │     │  - REST API  │     │  - Users & Profiles        │  │
│  │  - Inventory │     │  - Auth      │     │  - Products & Inventory    │  │
│  │  - OCR Bills │     │  - Business  │     │  - Bills & Line Items      │  │
│  │  - Vendors   │     │    Logic     │     │  - Vendors & Catalogue     │  │
│  │  - Chat      │     │  - OCR       │     │  - Conversations/Messages  │  │
│  │  - Orders    │     │  - Payments  │     │  - Orders & Payments       │  │
│  └──────────────┘     └──────────────┘     └────────────────────────────┘  │
│         │                    │                    ▲                         │
│         │                    │                    │                         │
│         ▼                    ▼                    │                         │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      EXTERNAL SERVICES                                │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │  │
│  │  │   OCR       │  │  Supabase   │  │  File       │  │  Payment   │  │  │
│  │  │  (Google    │  │  Auth       │  │  Storage    │  │  (Razorpay)│  │  │
│  │  │   Vision)   │  │             │  │  (Supabase) │  │  Test Mode │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | React.js + Tailwind CSS | Responsive UI, dashboards, forms |
| **Backend** | Python + FastAPI | REST APIs, business logic, validation |
| **Database** | PostgreSQL (Supabase) | Persistent structured data |
| **Auth** | Supabase Auth (JWT) | Sign-in, role-based access |
| **OCR** | Google Cloud Vision API | Extract text from purchase bills |
| **File Storage** | Supabase Storage | Bills, chat attachments, catalogue files |
| **Realtime** | Supabase Realtime | Live message updates |
| **Nearby Search** | PostgreSQL + PostGIS | Vendor proximity queries |
| **Payments** | Razorpay (Test Mode) | Payment checkout & verification |
| **Charts** | Recharts | Price history, dashboard summaries |
| **Testing** | Postman, pytest | API checks, unit/integration tests |
| **Deployment** | Vercel (FE), Render/Railway (BE) | Hosting for demo |

---

## 3. Module Breakdown

### 3.1 Authentication & Authorization (`auth`)
- **Supabase Auth** for email/password registration & login
- **JWT tokens** issued by Supabase, validated in FastAPI middleware
- **Roles**: `shopkeeper`, `vendor`, `admin`
- **Row Level Security (RLS)** policies in Supabase for data isolation

### 3.2 Inventory Management (`inventory`)
- **Product CRUD** — create, read, update, deactivate
- **Stock Movements** — audit trail (quantity change, reason, source, actor)
- **Low Stock Alerts** — threshold-based notifications
- **Price Tracking** — cost price, selling price, profit estimates

### 3.3 OCR Bill Processing (`ocr`)
- **Upload** — image/PDF to Supabase Storage (private)
- **OCR** — Google Cloud Vision API extraction
- **Review** — editable confirmation screen with field validation
- **Duplicate Detection** — vendor + invoice number + date matching
- **Confirmation** — atomic transaction: save bill + create stock movements

### 3.4 Vendor Discovery (`vendors`)
- **Vendor Profiles** — business info, location (lat/lng), service radius
- **Catalogue** — vendor products with prices, units, availability
- **Search** — by product name, category, area/city, GPS proximity
- **Price History** — purchase prices per vendor/date/unit for comparison

### 3.5 B2B Chat (`chat`)
- **Conversations** — 1:1 shopkeeper↔vendor (unique constraint)
- **Messages** — text + file attachments (images, PDFs)
- **File Storage** — private Supabase Storage, signed URLs
- **Realtime** — Supabase Realtime subscriptions for live updates
- **Authorization** — participants only can read/write

### 3.6 Orders & Payments (`orders`)
- **Order Lifecycle** — create → vendor accept/reject → status updates
- **Order Lines** — items, quantities, agreed prices, totals
- **Payment** — Razorpay test mode checkout
- **Verification** — Server-side webhook validation, transaction records
- **Status Separation** — Order status ≠ Payment status

---

## 4. Data Flow Examples

### 4.1 Bill to Inventory Flow
```
Shopkeeper uploads bill image
       │
       ▼
Supabase Storage (private bucket)
       │
       ▼
Google Cloud Vision OCR
       │
       ▼
Backend parses OCR → structured line items
       │
       ▼
Review screen (editable)
       │
       ▼
Duplicate check (vendor + invoice_no + date)
       │
       ▼
Confirm → DB Transaction:
  - Save PurchaseBill + PurchaseBillLine
  - Create/Update Products
  - Create InventoryMovements
  - Create PriceRecords
       │
       ▼
Dashboard updates, price history reflects
```

### 4.2 Vendor Discovery Flow
```
Shopkeeper searches "onions near me"
       │
       ▼
Backend: GPS coords + radius OR manual city
       │
       ▼
PostGIS query: vendors within radius
       │
       ▼
Filter by product availability & price
       │
       ▼
Return: vendor info + distance + matching products
```

### 4.3 Chat Flow
```
User opens conversation with vendor
       │
       ▼
Get or create Conversation (unique pair)
       │
       ▼
Subscribe to Supabase Realtime channel
       │
       ▼
Send message → INSERT to messages table
       │
       ▼
Realtime pushes to other participant
       │
       ▼
File attachment → Upload to Supabase Storage → signed URL in message
```

---

## 5. API Design Conventions

- **Base Path**: `/api/v1`
- **Auth**: `Authorization: Bearer <jwt>`
- **Responses**:
  ```json
  // Success
  { "data": {...}, "meta": {...} }
  
  // Error
  { "error": { "code": "VALIDATION_ERROR", "message": "...", "details": [...] } }
  ```
- **Pagination**: `?page=1&limit=20` → `meta: { page, limit, total, total_pages }`
- **Filtering**: `?search=term&category=foo&min_price=10`
- **Sorting**: `?sort=created_at:desc`
- **Ids**: Integer primary keys (PostgreSQL serial)

---

## 6. Security Considerations

- **No secrets in code** — all via `.env` / Supabase dashboard
- **RLS policies** — users only see their business data
- **File access** — signed URLs with expiry, participant checks
- **Payment verification** — server-side webhook, never trust frontend
- **Input validation** — Pydantic schemas on all endpoints
- **Rate limiting** — on auth endpoints, OCR, payment webhooks

---

## 7. Deployment Topology

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Vercel    │     │  Render/    │     │  Supabase   │
│  (Frontend) │────▶│  Railway    │────▶│  (DB, Auth, │
│             │     │  (Backend)  │     │  Storage,   │
└─────────────┘     └─────────────┘     │  Realtime)  │
                                        └─────────────┘
```

- **Frontend**: Static build on Vercel, env vars for API URL
- **Backend**: Container on Render/Railway, health check at `/health`
- **Database**: Supabase managed PostgreSQL
- **CI/CD**: GitHub Actions (test → build → deploy)

---

## 8. Future Extensibility

- **Webhooks** for external integrations (accounting, ERP)
- **Multi-language OCR** support
- **Push notifications** (FCM/APNs)
- **Analytics dashboard** for vendors
- **Mobile app** (React Native) sharing API contracts

---

*This document should be updated when architectural decisions change. See `DECISIONS.md` for dated decision log.*