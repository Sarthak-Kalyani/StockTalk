# StockTalk Database Schema

**Version:** 1.0  
**Database:** PostgreSQL (Supabase)  
**ORM:** SQLAlchemy (FastAPI)

---

## 1. Entity Relationship Diagram

```
┌─────────────────┐       ┌──────────────────┐       ┌─────────────────┐
│     users       │       │  business_profiles│       │    products     │
├─────────────────┤       ├──────────────────┤       ├─────────────────┤
│ id (PK)         │◀──────│ user_id (FK, UK) │       │ id (PK)         │
│ email           │       │ business_name    │       │ business_id(FK) │
│ password_hash   │       │ address          │       │ name            │
│ role            │       │ latitude         │       │ sku             │
│ status          │       │ longitude        │       │ category        │
│ created_at      │       │ service_area     │       │ unit            │
│ updated_at      │       │ created_at       │       │ quantity        │
└─────────────────┘       │ updated_at       │       │ min_stock_level │
                          └──────────────────┘       │ cost_price      │
                                                     │ selling_price   │
                                                     │ vendor_id (FK)  │
                                                     │ is_active       │
                                                     │ created_at      │
                                                     │ updated_at      │
                                                     └────────┬────────┘
                                                              │
                    ┌────────────────────────────────────────┼────────────────┐
                    │                                        │                │
                    ▼                                        ▼                ▼
            ┌───────────────┐                        ┌───────────────┐ ┌───────────────┐
            │inventory_mov- │                        │ purchase_bills │ │vendor_catalogue│
            │   ements      │                        ├───────────────┤ ├───────────────┤
            ├───────────────┤                        │ id (PK)        │ │ id (PK)       │
            │ id (PK)       │                        │ business_idFK  │ │ vendor_id(FK) │
            │ product_idFK  │                        │ vendor_id (FK) │ │ product_name  │
            │ quantity_chg  │                        │ invoice_number │ │ description   │
            │ reason        │                        │ invoice_date   │ │ category      │
            │ source        │                        │ file_path      │ │ price         │
            │ actor_id (FK) │                        │ ocr_status     │ │ unit          │
            │ related_billFK│                        │ totals         │ │ avail_qty     │
            │ related_orderFK│                       │ confirmed      │ │ is_available  │
            │ created_at    │                        │ created_at     │ │ created_at    │
            └───────────────┘                        └───────┬────────┘ └───────────────┘
                                                             │
                    ┌────────────────────────────────────────┼────────────────┐
                    │                                        │                │
                    ▼                                        ▼                ▼
            ┌───────────────┐                        ┌───────────────┐ ┌───────────────┐
            │purchase_bill_ │                        │ price_records │ │vendor_locations│
            │   lines       │                        ├───────────────┤ ├───────────────┤
            ├───────────────┤                        │ id (PK)       │ │ id (PK)       │
            │ id (PK)       │                        │ product_idFK  │ │ vendor_idFKUK │
            │ bill_id (FK)  │                        │ vendor_id(FK) │ │ latitude      │
            │ product_idFK  │                        │ price         │ │ longitude     │
            │ extracted_name│                        │ unit          │ │ address       │
            │ quantity      │                        │ pack_size     │ │ city          │
            │ unit_price    │                        │ tax_included  │ │ service_radius│
            │ tax           │                        │ date          │ │ created_at    │
            │ line_total    │                        │ source        │ └───────────────┘
            └───────────────┘                        └───────────────┘

┌─────────────────┐       ┌──────────────────┐       ┌─────────────────┐
│  conversations  │       │    messages      │       │    orders       │
├─────────────────┤       ├──────────────────┤       ├─────────────────┤
│ id (PK)         │◀──────│ id (PK)          │       │ id (PK)         │
│ shopkeeper_idFK │       │ conversation_idFK│       │ buyer_id (FK)   │
│ vendor_id (FK)  │       │ sender_id (FK)   │       │ vendor_id (FK)  │
│ created_at      │       │ content          │       │ status          │
└─────────────────┘       │ is_read          │       │ total_amount    │
                          │ attachment_url   │       │ delivery_addr   │
                          │ created_at       │       │ created_at      │
                          └──────────────────┘       │ updated_at      │
                                                     └────────┬────────┘
                                                              │
                    ┌────────────────────────────────────────┼────────────────┐
                    │                                        │                │
                    ▼                                        ▼                ▼
            ┌───────────────┐                        ┌───────────────┐ ┌───────────────┐
            │  order_lines  │                        │   payments    │ │  attachments  │
            ├───────────────┤                        ├───────────────┤ ├───────────────┤
            │ id (PK)       │                        │ id (PK)       │ │ id (PK)       │
            │ order_id (FK) │                        │ order_id (FK) │ │ message_idFK  │
            │ product_idFK  │                        │ provider      │ │ file_path     │
            │ quantity      │                        │ provider_ref  │ │ file_type     │
            │ unit_price    │                        │ amount        │ │ file_size     │
            │ line_total    │                        │ currency      │ │ created_at    │
            └───────────────┘                        │ status        │ └───────────────┘
                                                     │ verified_at   │
                                                     │ created_at    │
                                                     └───────────────┘
```

---

## 2. Table Definitions

### 2.1 Core Tables

#### `users`
```sql
CREATE TABLE users (
    id              BIGSERIAL PRIMARY KEY,
    email           VARCHAR(255) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,  -- Supabase handles this
    role            VARCHAR(20) NOT NULL CHECK (role IN ('shopkeeper', 'vendor', 'admin')),
    status          VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'pending')),
    supabase_uid    UUID UNIQUE,  -- Link to Supabase Auth
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
```

#### `business_profiles`
```sql
CREATE TABLE business_profiles (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    business_name   VARCHAR(200) NOT NULL,
    address         TEXT,
    latitude        DOUBLE PRECISION,
    longitude       DOUBLE PRECISION,
    service_area    VARCHAR(100),  -- city/area for manual search
    phone           VARCHAR(20),
    gst_number      VARCHAR(20),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_business_profiles_user ON business_profiles(user_id);
CREATE INDEX idx_business_profiles_location ON business_profiles(latitude, longitude);
```

#### `products`
```sql
CREATE TABLE products (
    id                  BIGSERIAL PRIMARY KEY,
    business_id         BIGINT NOT NULL REFERENCES business_profiles(id) ON DELETE CASCADE,
    name                VARCHAR(200) NOT NULL,
    sku                 VARCHAR(50) UNIQUE,
    category            VARCHAR(100),
    unit                VARCHAR(30) NOT NULL DEFAULT 'piece',
    quantity            INTEGER NOT NULL DEFAULT 0,
    min_stock_level     INTEGER NOT NULL DEFAULT 0,
    cost_price          DECIMAL(12,2) NOT NULL DEFAULT 0,
    selling_price       DECIMAL(12,2) NOT NULL DEFAULT 0,
    vendor_id           BIGINT REFERENCES business_profiles(id) ON DELETE SET NULL,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_products_business ON products(business_id);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_vendor ON products(vendor_id);
CREATE INDEX idx_products_low_stock ON products(business_id, quantity) WHERE quantity <= min_stock_level;
```

#### `inventory_movements`
```sql
CREATE TABLE inventory_movements (
    id                  BIGSERIAL PRIMARY KEY,
    product_id          BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    quantity_change     INTEGER NOT NULL,  -- positive = in, negative = out
    reason              VARCHAR(50) NOT NULL CHECK (reason IN ('manual', 'bill', 'sale', 'adjustment', 'order', 'return')),
    source              VARCHAR(50) NOT NULL,  -- 'manual', 'bill_upload', 'order_fulfillment', etc.
    actor_id            BIGINT NOT NULL REFERENCES users(id),
    related_bill_id     BIGINT REFERENCES purchase_bills(id) ON DELETE SET NULL,
    related_order_id    BIGINT REFERENCES orders(id) ON DELETE SET NULL,
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_inventory_movements_product ON inventory_movements(product_id);
CREATE INDEX idx_inventory_movements_created ON inventory_movements(created_at DESC);
```

---

### 2.2 OCR & Bills

#### `purchase_bills`
```sql
CREATE TABLE purchase_bills (
    id                  BIGSERIAL PRIMARY KEY,
    business_id         BIGINT NOT NULL REFERENCES business_profiles(id) ON DELETE CASCADE,
    vendor_id           BIGINT NOT NULL REFERENCES business_profiles(id) ON DELETE CASCADE,
    invoice_number      VARCHAR(100) NOT NULL,
    invoice_date        DATE NOT NULL,
    file_path           TEXT NOT NULL,  -- Supabase Storage path
    ocr_status          VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (ocr_status IN ('pending', 'processing', 'completed', 'failed', 'review_needed')),
    ocr_raw_json        JSONB,  -- Raw OCR response
    subtotal            DECIMAL(12,2),
    tax_total           DECIMAL(12,2),
    grand_total         DECIMAL(12,2),
    confirmed           BOOLEAN NOT NULL DEFAULT FALSE,
    confirmed_at        TIMESTAMPTZ,
    confirmed_by        BIGINT REFERENCES users(id),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE (vendor_id, invoice_number, invoice_date)
);

CREATE INDEX idx_purchase_bills_business ON purchase_bills(business_id);
CREATE INDEX idx_purchase_bills_vendor ON purchase_bills(vendor_id);
CREATE INDEX idx_purchase_bills_status ON purchase_bills(ocr_status);
CREATE INDEX idx_purchase_bills_confirmed ON purchase_bills(confirmed);
```

#### `purchase_bill_lines`
```sql
CREATE TABLE purchase_bill_lines (
    id                  BIGSERIAL PRIMARY KEY,
    bill_id             BIGINT NOT NULL REFERENCES purchase_bills(id) ON DELETE CASCADE,
    product_id          BIGINT REFERENCES products(id) ON DELETE SET NULL,  -- NULL if new product
    extracted_name      VARCHAR(200) NOT NULL,
    quantity            DECIMAL(10,3) NOT NULL,
    unit                VARCHAR(30) NOT NULL,
    unit_price          DECIMAL(12,2) NOT NULL,
    tax                 DECIMAL(12,2) NOT NULL DEFAULT 0,
    line_total          DECIMAL(12,2) NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_purchase_bill_lines_bill ON purchase_bill_lines(bill_id);
CREATE INDEX idx_purchase_bill_lines_product ON purchase_bill_lines(product_id);
```

---

### 2.3 Price History

#### `price_records`
```sql
CREATE TABLE price_records (
    id                  BIGSERIAL PRIMARY KEY,
    product_id          BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    vendor_id           BIGINT NOT NULL REFERENCES business_profiles(id) ON DELETE CASCADE,
    price               DECIMAL(12,2) NOT NULL,
    unit                VARCHAR(30) NOT NULL,
    pack_size           DECIMAL(10,3) NOT NULL DEFAULT 1,  -- e.g., 1kg, 500g
    tax_included        BOOLEAN NOT NULL DEFAULT TRUE,
    date                DATE NOT NULL,
    source              VARCHAR(20) NOT NULL CHECK (source IN ('bill', 'order', 'catalogue', 'manual')),
    source_id           BIGINT,  -- bill_id or order_id
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_price_records_product ON price_records(product_id, date DESC);
CREATE INDEX idx_price_records_vendor ON price_records(vendor_id, date DESC);
CREATE INDEX idx_price_records_comparison ON price_records(product_id, vendor_id, unit, pack_size);
```

---

### 2.4 Vendor Discovery

#### `vendor_catalogue`
```sql
CREATE TABLE vendor_catalogue (
    id                      BIGSERIAL PRIMARY KEY,
    vendor_id               BIGINT NOT NULL REFERENCES business_profiles(id) ON DELETE CASCADE,
    product_name            VARCHAR(200) NOT NULL,
    description             TEXT,
    category                VARCHAR(100),
    price                   DECIMAL(12,2) NOT NULL,
    unit                    VARCHAR(30) NOT NULL DEFAULT 'piece',
    pack_size               DECIMAL(10,3) NOT NULL DEFAULT 1,
    available_quantity      INTEGER NOT NULL DEFAULT 0,
    is_available            BOOLEAN NOT NULL DEFAULT TRUE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_vendor_catalogue_vendor ON vendor_catalogue(vendor_id);
CREATE INDEX idx_vendor_catalogue_name ON vendor_catalogue(product_name);
CREATE INDEX idx_vendor_catalogue_category ON vendor_catalogue(category);
CREATE INDEX idx_vendor_catalogue_available ON vendor_catalogue(vendor_id, is_available) WHERE is_available = TRUE;
```

#### `vendor_locations`
```sql
CREATE TABLE vendor_locations (
    id                      BIGSERIAL PRIMARY KEY,
    vendor_id               BIGINT NOT NULL UNIQUE REFERENCES business_profiles(id) ON DELETE CASCADE,
    latitude                DOUBLE PRECISION NOT NULL,
    longitude               DOUBLE PRECISION NOT NULL,
    address                 TEXT,
    city                    VARCHAR(100),
    service_radius_km       DECIMAL(6,2) NOT NULL DEFAULT 10.0,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- PostGIS extension for proximity queries
-- CREATE EXTENSION IF NOT EXISTS postgis;
-- ALTER TABLE vendor_locations ADD COLUMN geom GEOGRAPHY(POINT);
-- CREATE INDEX idx_vendor_locations_geom ON vendor_locations USING GIST (geom);
```

---

### 2.5 Chat

#### `conversations`
```sql
CREATE TABLE conversations (
    id                      BIGSERIAL PRIMARY KEY,
    shopkeeper_id           BIGINT NOT NULL REFERENCES business_profiles(id) ON DELETE CASCADE,
    vendor_id               BIGINT NOT NULL REFERENCES business_profiles(id) ON DELETE CASCADE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE (shopkeeper_id, vendor_id)
);

CREATE INDEX idx_conversations_shopkeeper ON conversations(shopkeeper_id);
CREATE INDEX idx_conversations_vendor ON conversations(vendor_id);
```

#### `messages`
```sql
CREATE TABLE messages (
    id                      BIGSERIAL PRIMARY KEY,
    conversation_id         BIGINT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender_id               BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content                 TEXT NOT NULL,
    is_read                 BOOLEAN NOT NULL DEFAULT FALSE,
    attachment_path         TEXT,  -- Supabase Storage path
    attachment_type         VARCHAR(50),  -- 'image', 'pdf', 'document'
    attachment_size         INTEGER,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at);
CREATE INDEX idx_messages_sender ON messages(sender_id);
```

#### `attachments` (optional, for richer metadata)
```sql
CREATE TABLE attachments (
    id                      BIGSERIAL PRIMARY KEY,
    message_id              BIGINT NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    file_path               TEXT NOT NULL,
    file_type               VARCHAR(50) NOT NULL,
    file_size               INTEGER NOT NULL,
    original_name           VARCHAR(255),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

### 2.6 Orders & Payments

#### `orders`
```sql
CREATE TABLE orders (
    id                      BIGSERIAL PRIMARY KEY,
    buyer_id                BIGINT NOT NULL REFERENCES business_profiles(id) ON DELETE CASCADE,
    vendor_id               BIGINT NOT NULL REFERENCES business_profiles(id) ON DELETE CASCADE,
    status                  VARCHAR(20) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'sent', 'accepted', 'rejected', 'processing', 'shipped', 'delivered', 'cancelled')),
    total_amount            DECIMAL(12,2) NOT NULL DEFAULT 0,
    delivery_address        TEXT,
    contact_phone           VARCHAR(20),
    notes                   TEXT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_orders_buyer ON orders(buyer_id, created_at DESC);
CREATE INDEX idx_orders_vendor ON orders(vendor_id, created_at DESC);
CREATE INDEX idx_orders_status ON orders(status);
```

#### `order_lines`
```sql
CREATE TABLE order_lines (
    id                      BIGSERIAL PRIMARY KEY,
    order_id                BIGINT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id              BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    product_name            VARCHAR(200) NOT NULL,  -- Snapshot at order time
    quantity                DECIMAL(10,3) NOT NULL,
    unit                    VARCHAR(30) NOT NULL,
    unit_price              DECIMAL(12,2) NOT NULL,
    line_total              DECIMAL(12,2) NOT NULL,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_order_lines_order ON order_lines(order_id);
```

#### `payments`
```sql
CREATE TABLE payments (
    id                      BIGSERIAL PRIMARY KEY,
    order_id                BIGINT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    provider                VARCHAR(30) NOT NULL DEFAULT 'razorpay',
    provider_order_id       VARCHAR(100),  -- Razorpay order_id
    provider_payment_id     VARCHAR(100),  -- Razorpay payment_id
    provider_signature      VARCHAR(255),  -- For verification
    amount                  DECIMAL(12,2) NOT NULL,
    currency                VARCHAR(3) NOT NULL DEFAULT 'INR',
    status                  VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'success', 'failed', 'refunded')),
    verified                BOOLEAN NOT NULL DEFAULT FALSE,
    verified_at             TIMESTAMPTZ,
    webhook_payload         JSONB,  -- Full webhook for audit
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_payments_order ON payments(order_id);
CREATE INDEX idx_payments_provider_ref ON payments(provider_payment_id);
CREATE INDEX idx_payments_status ON payments(status);
```

---

## 3. Row Level Security (RLS) Policies (Supabase)

```sql
-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE business_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE inventory_movements ENABLE ROW LEVEL SECURITY;
ALTER TABLE purchase_bills ENABLE ROW LEVEL SECURITY;
ALTER TABLE purchase_bill_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE price_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE vendor_catalogue ENABLE ROW LEVEL SECURITY;
ALTER TABLE vendor_locations ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE order_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;

-- Example policies (adapt to Supabase Auth UID mapping)

-- Users can read their own profile
CREATE POLICY "Users read own profile" ON users
    FOR SELECT USING (supabase_uid = auth.uid());

-- Business profiles: users can CRUD their own
CREATE POLICY "Business profile own access" ON business_profiles
    FOR ALL USING (user_id IN (SELECT id FROM users WHERE supabase_uid = auth.uid()));

-- Products: shopkeeper sees their products
CREATE POLICY "Products own business" ON products
    FOR ALL USING (business_id IN (SELECT id FROM business_profiles WHERE user_id IN (SELECT id FROM users WHERE supabase_uid = auth.uid())));

-- Vendors can see their own catalogue
CREATE POLICY "Vendor catalogue own" ON vendor_catalogue
    FOR ALL USING (vendor_id IN (SELECT id FROM business_profiles WHERE user_id IN (SELECT id FROM users WHERE supabase_uid = auth.uid())));

-- Conversations: participants only
CREATE POLICY "Conversation participants" ON conversations
    FOR ALL USING (
        shopkeeper_id IN (SELECT id FROM business_profiles WHERE user_id IN (SELECT id FROM users WHERE supabase_uid = auth.uid()))
        OR
        vendor_id IN (SELECT id FROM business_profiles WHERE user_id IN (SELECT id FROM users WHERE supabase_uid = auth.uid()))
    );

-- Messages: conversation participants only
CREATE POLICY "Messages participants" ON messages
    FOR ALL USING (
        conversation_id IN (
            SELECT id FROM conversations WHERE 
            shopkeeper_id IN (SELECT id FROM business_profiles WHERE user_id IN (SELECT id FROM users WHERE supabase_uid = auth.uid()))
            OR
            vendor_id IN (SELECT id FROM business_profiles WHERE user_id IN (SELECT id FROM users WHERE supabase_uid = auth.uid()))
        )
    );

-- Orders: buyer or vendor
CREATE POLICY "Orders buyer or vendor" ON orders
    FOR ALL USING (
        buyer_id IN (SELECT id FROM business_profiles WHERE user_id IN (SELECT id FROM users WHERE supabase_uid = auth.uid()))
        OR
        vendor_id IN (SELECT id FROM business_profiles WHERE user_id IN (SELECT id FROM users WHERE supabase_uid = auth.uid()))
    );
```

---

## 4. Migration Strategy

1. **Initial migration** — Core tables (users, business_profiles, products, inventory_movements)
2. **OCR migration** — purchase_bills, purchase_bill_lines
3. **Price history** — price_records
4. **Vendor discovery** — vendor_catalogue, vendor_locations (add PostGIS)
5. **Chat** — conversations, messages, attachments
6. **Orders/Payments** — orders, order_lines, payments

Use **Alembic** for versioned migrations. Each migration is reviewed before applying to shared database.

---

## 5. Naming Conventions

- **Tables**: snake_case, plural (`purchase_bills`)
- **Columns**: snake_case (`invoice_number`, `created_at`)
- **Primary Keys**: `id` (BIGSERIAL)
- **Foreign Keys**: `{table}_id` (`business_id`, `vendor_id`)
- **Indexes**: `idx_{table}_{column(s)}`
- **Unique Constraints**: `uq_{table}_{columns}`
- **Check Constraints**: `ck_{table}_{condition}`
- **Timestamps**: `created_at`, `updated_at` (TIMESTAMPTZ, default NOW())

---

*Update this document when schema changes. Record decisions in `DECISIONS.md`.*