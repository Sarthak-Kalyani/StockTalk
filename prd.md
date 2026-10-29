STOCKTALK --- Product Requirements Document (PRD)
B.Tech Final Year Project · Session 2026--27
Institute: G.L. Bajaj Institute of Technology & Management, Greater
Noida
Department: Computer Science & Engineering
Group ID: GC_2026_018
Project type: Application
Project guide: Mr. Kuldeep Singh
Version: 1.0 --- Initial product scope
A unified B2B platform for inventory, bill scanning, nearby vendors,
communication, and payments.

1. Executive Summary
StockTalk is a B2B application for small and medium businesses that
brings inventory management and supplier interactions into one platform.
Shopkeepers can scan purchase bills using OCR, review extracted data,
update stock, track purchase and selling prices, discover nearby
vendors, communicate through text and file sharing, place orders, and
record payments.

The initial release should prioritize a reliable end-to-end workflow
over advanced features. OCR results must be reviewed before inventory is
changed, and payment status must be verified by the backend.
2. Problem Statement
Small businesses often maintain stock in notebooks or spreadsheets,
receive supplier information over messaging apps, compare prices
manually, and pay through separate services. This fragmented process can
cause data-entry errors, poor visibility into price changes, missed
reordering, and difficulty tracking orders.
3. Product Vision and Goals
- Provide one place to manage products, quantities, cost prices,
  selling prices, and vendor details.
- Reduce manual purchase-bill entry through OCR-assisted data
  extraction.
- Help shopkeepers discover relevant vendors in their nearby area and
  compare offers.
- Enable shopkeepers and vendors to exchange messages, images, and
  documents.
- Support a traceable order and payment workflow suitable for a
  student project demonstration.
4. Users and Roles
  Role                                Primary responsibilities
  Shopkeeper / Buyer              Manage shop profile and inventory;
                                      scan bills; find vendors; compare
                                      prices; chat; place orders; view
                                      payment and purchase history.

  Vendor / Supplier               Manage vendor profile and location;
                                      maintain product catalogue and
                                      prices; respond to messages;
                                      receive and update orders; view
                                      transaction status.

  Administrator (basic)           Manage user access and review
                                      reports or problematic records if
                                      an admin panel is included in the
                                  MVP.
5. Scope and Functional Requirements
5.1 Authentication and Profiles
- Users can register, log in, log out, and select or be assigned a
  Shopkeeper or Vendor role.
- Profiles store name, phone/email, business name, address, and
  relevant business details.
- Users can update their profile and access only features permitted
  for their role.
5.2 Inventory Management
- Create, view, edit, search, and deactivate product records.
- Store product name, SKU or code, category, unit, quantity, minimum
  stock level, cost price, selling price, and vendor association.
- Record stock movements with date, quantity change, source (manual
  entry, bill, sale/adjustment), and user.
- Show low-stock alerts and calculate stock value using a clearly
  defined cost-price method.
- Keep cost price and selling price distinct; profit figures are
  estimates and depend on the selected cost method.
5.3 OCR Bill Scanning and Inventory Connection
- Allow a user to upload or capture an invoice image or PDF, subject
  to supported file formats.
- Send the bill to an OCR service and extract available fields such as
  vendor, invoice number/date, line-item names, quantities, unit
  prices, taxes, and total.
- Display an editable review screen; uncertain or missing fields must
  be corrected by the user.
- On confirmation, save the bill and line items, link products to
  existing inventory items or allow creation of new items, and update
  quantities.
- Detect likely duplicate bills using vendor/invoice number and other
  available fields; do not silently apply the same bill twice.
- Retain the original bill file and a record of the resulting stock
  changes.
5.4 Vendor Discovery and Location
- Allow vendors to save business address and location, with explicit
  permission for device location where used.
- Allow shopkeepers to search vendors by area, product/category,
  vendor name, and proximity.
- Display available business information and distance where location
  data is available.
- Provide manual area or city search if the user declines
  device-location permission.
- Treat location as approximate discovery data; do not expose a user's
  live location to other users.
5.5 Price History and Comparison
- Store each purchase price with product, vendor, date, unit, and
  source bill/order.
- Display previous versus latest purchase price and absolute or
  percentage change.
- Compare prices from different vendors only when product identity,
  unit, pack size, and relevant taxes are comparable.
- Keep vendor catalogue/quoted prices distinct from the actual price
  paid on a completed purchase.
5.6 B2B Chat and File Sharing
- Provide one-to-one conversations between shopkeepers and vendors.
- Support text messages and sharing/receiving images, PDFs, and
  permitted business files.
- Show sender, timestamp, upload state, and file preview/download
  where supported.
- Restrict conversations and files to authorized participants;
  validate file type and size and use private storage.
- Allow users to start a conversation from a vendor or product
  listing.
5.7 Orders and Payments
- Allow a shopkeeper to create an order containing vendor, items,
  quantities, agreed prices, totals, and delivery/contact details.
- Allow the vendor to accept, reject, or update the order status.
- Maintain order statuses separately from payment statuses.
- Integrate a payment provider in test mode first; the final payment
  method depends on provider support and merchant eligibility.
- Verify payment results server-side using provider
  verification/webhooks and store transaction references; never trust
  a frontend success screen alone.
- Show order history, payment status, and a basic receipt/transaction
  summary.
5.8 Dashboards and Notifications
Shopkeeper dashboard - Stock summary, low-stock products, recent
bills, price changes, nearby vendors, orders, and payments.

Vendor dashboard - Catalogue, listed prices, incoming orders,
enquiries/messages, and transaction status.

Provide in-app indicators for low stock, new messages, and order status
changes; push notifications are optional for the first release.
6. Non-Functional Requirements
  Area                                Requirement
  Security                        Hash passwords if managed locally;
                                      protect APIs by role; validate
                                      input; keep secrets on the server;
                                      restrict access to private files.

  Privacy                         Request location permission only
                                      when needed; collect minimal data;
                                      provide a manual location
                                      alternative.

  Reliability                     Use database transactions for bill
                                      confirmation, stock updates, and
                                      order changes where appropriate.

  Usability                       Responsive, clear interface for
                                      desktop and mobile browsers; simple
                                      workflows and readable error
                                      messages.

  Performance                     Paginate larger lists; show
                                      progress for OCR and uploads; avoid
                                      blocking the UI during long
                                      operations.

  Auditability                    Record stock movements, bill
                                      processing, order status changes,
                                      and payment references.

  Maintainability                 Use modular frontend/backend code,
                                      shared API contracts,
                                      environment-based configuration,
                                  and Git branches.
7. Recommended Technology Stack
  Layer                   Recommended choice      Purpose
  Frontend                React.js + Tailwind CSS Responsive user
                                                  interface and
                                                  dashboards.

  Backend                 Python + FastAPI        REST APIs, business
                                                  rules, validation, and
                                                  integrations.

  Database                PostgreSQL (managed     Persistent structured
                          through Supabase if     business data.
                          desired)                

  Authentication          Supabase Auth or secure Sign-in and
                          JWT-based               role-protected access;
                          authentication          choose one approach.

  OCR                     Google Cloud Vision     Extract text from
                          API; Tesseract as an    purchase bills.
                          alternative             

  File storage            Supabase Storage or     Bills, chat
                          equivalent private      attachments, and
                          object storage          catalogue files.

  Realtime chat           Supabase Realtime or    Live message updates;
                          FastAPI WebSockets      choose one for MVP.

  Nearby search           PostgreSQL location     Search vendors by area
                          fields; PostGIS if      and distance.
                          proximity queries
                          require it              

  Payments                Razorpay test mode,     Payment checkout and
                          subject to available    status verification.
                          UPI/payment support     

  Charts                  Recharts                Price history and
                                                  dashboard summaries.

  Testing and             Postman, Git, GitHub    API checks, source
  collaboration                                   control, and team
                                                  collaboration.

  Deployment              Vercel for frontend;    Hosting and
                          Render/Railway for API; demonstration
                          managed                 environment.
                      PostgreSQL/storage      
Implementation note: Avoid using multiple competing services for the
same responsibility. For example, choose one authentication approach and
one real-time messaging approach for the MVP.
8. Core Data Entities
  Entity                              Important fields / relationships
  User                            ID, role, name, contact,
                                      authentication reference, status.

  BusinessProfile                 User ID, business name, address,
                                      latitude/longitude where permitted,
                                      service area.

  Product                         ID, owner/business ID, name, SKU,
                                      category, unit, quantity, minimum
                                      stock.

  VendorProduct / Offer           Vendor ID, product identity,
                                      catalogue price, unit/pack size,
                                      availability, updated date.

  InventoryMovement               Product ID, quantity change,
                                      reason/source, timestamp, actor,
                                      related bill/order.

  PurchaseBill                    Business ID, vendor ID, invoice
                                      number/date, file reference, OCR
                                      state, totals, confirmation status.

  PurchaseBillLine                Bill ID, product ID or extracted
                                      name, quantity, unit price, tax,
                                      line total.

  PriceRecord                     Product identity, vendor ID,
                                      observed/purchased price, unit,
                                      date, source.

  Conversation / Message          Participants, message text/type,
                                      timestamp, attachment reference,
                                      delivery metadata if supported.

  Order / OrderLine               Buyer, vendor, items, quantities,
                                      agreed unit prices, total, order
                                      status.

  Payment                         Order ID, provider reference,
                                      amount, currency, payment status,
                                  verification timestamp.
The final schema should be reviewed before implementation. A product
sold by multiple vendors needs a shared product identity or a mapping
mechanism; otherwise, price comparisons may compare unlike items.
9. Main User Workflows
Workflow A --- Bill to Inventory
1. Shopkeeper logs in and uploads a bill.
2. OCR extracts invoice and line-item data.
3. Shopkeeper reviews and corrects the extracted values.
4. System matches or creates inventory products and checks for
   duplicate bills.
5. Shopkeeper confirms; the system saves the bill and applies stock
   movements.
6. Dashboard and price history reflect the confirmed purchase.
Workflow B --- Find Vendor to Pay
1. Shopkeeper searches by product and nearby area.
2. System shows relevant vendors and comparable catalogue/quoted
   prices.
3. Shopkeeper opens a conversation, shares files if needed, and agrees
   on terms.
4. Shopkeeper submits an order; vendor accepts or updates it.
5. Shopkeeper completes the supported payment flow.
6. Backend verifies the result and updates payment records; order
   status is updated according to the agreed workflow.
10. Development Phases and Deliverables
  Phase                   Build                   Exit criteria
  1. Foundation       Repository, environment Frontend and backend
                          configuration,          run; database
                          database, API           connection and shared
                          conventions, basic UI   Git workflow work.
                          shell.                  

  2. Accounts         Registration/login,     Shopkeeper and vendor
                          roles, business         can sign in and see the
                          profiles, protected     correct dashboard.
                          routes.                 

  3. Inventory        Products, quantities,   Manual stock operations
                          cost/selling prices,    are persisted and
                          stock movements,        validated.
                          low-stock alerts.       

  4. OCR              Bill upload, OCR,       A sample bill can be
                          review/correction,      processed end-to-end
                          duplicate checks,       without silently
                          confirmed inventory     duplicating stock.
                          update.                 

  5. Vendor and         Vendor                  A shopkeeper can find
  prices                profile/catalogue, area vendors and view
                          search, price history   grounded price changes.
                          and comparison.         

  6. Chat/files       Conversations, realtime Only conversation
                          text, private image/PDF participants can access
                          sharing.                messages and
                                                  attachments.

  7. Orders/payments  Order lifecycle,        A test order and
                          payment test            payment can be tracked
                          integration, backend    through their statuses.
                          verification.           

  8. Finalization     Integration tests,      Critical user journeys
                          responsive polish,      pass and the project is
                          deployment, demo data,  demonstrable.
                          report and
                      presentation.           
11. MVP Acceptance Criteria
- [ ] A user can register and access features for their assigned role.
- [ ] A shopkeeper can create a product, set cost and selling prices,
  and adjust quantity.
- [ ] A bill can be uploaded, OCR data reviewed, and confirmed entries
  linked to inventory.
- [ ] Duplicate bill submission is detected or blocked before
  duplicate stock is applied.
- [ ] The system can show historical purchase prices and a meaningful
  price change.
- [ ] A shopkeeper can find vendors by area or nearby search when
  location data is available.
- [ ] A shopkeeper and vendor can exchange text and permitted file
  attachments.
- [ ] A purchase order can be created and its status changed by the
  vendor.
- [ ] A payment test flow records a verified or clearly failed/pending
  status.
- [ ] Unauthorized users cannot access another business's private
  inventory, bills, messages, or files.
12. Out of Scope for the First Release
- Native Android/iOS apps; deliver a responsive web app unless the
  guide requires a native app.
- Automated delivery/logistics tracking and route optimization.
- AI-driven demand forecasting or automatic purchase recommendations.
- Full accounting, GST filing, invoicing compliance, or enterprise ERP
  features.
- Escrow, lending, credit scoring, or holding customer funds.
- Public marketplace ratings/reviews and advanced dispute resolution.
13. Key Risks and Mitigations
  Risk                                Mitigation
  OCR reads invoice incorrectly       Review/edit step, validation,
                                      confidence cues where available,
                                      and sample-bill testing.

  Duplicate stock updates             Duplicate bill checks, database
                                      transactions, and idempotent
                                      confirmation handling.

  Prices are not comparable           Normalize unit/pack size and record
                                      vendor, date, tax inclusion, and
                                      source.

  Location permission is denied       Provide manual area/city search.

  Private files leak                  Private storage, short-lived signed
                                      access where appropriate, file
                                      validation, and authorization
                                      checks.

  Payment status mismatch             Server-side provider
                                      verification/webhooks and
                                      reconciliation of pending states.

  Team integration delays             Agree API contracts and schema
                                      early; use mock responses and
                                  integrate each phase incrementally.
14. Suggested Team Responsibilities
  Workstream              Primary responsibility  Shared dependencies
  Backend and           FastAPI, schema, auth   All modules; publish
  database              integration,            API contracts early.
                          inventory/order APIs,
                          deployment.             

  OCR and bill          Upload flow, OCR        Inventory schema and
  processing            adapter, extraction     bill APIs.
                          parsing, review and
                          duplicate handling.     

  Frontend and          Responsive layout, auth API contracts and
  dashboard             screens, inventory,     sample/mock data.
                          dashboard, price
                          charts.                 

  Vendor, chat and      Vendor                  User roles, storage
  orders                catalogue/discovery UI, permissions, messaging
                          chat/file workflow,     and order APIs.
                          order and payment UI
                      integration.            
These are suggested ownership areas, not isolated tasks. All members
should review the schema, agree on API request/response formats, write
tests for their modules, and participate in end-to-end integration.
15. Decisions to Confirm with the Project Guide
- Is a responsive web application acceptable, or is a native mobile
  app mandatory?
- Which bill formats and languages must OCR support for the
  demonstration?
- Is a payment sandbox/test-mode demonstration sufficient?
- Should vendor discovery use GPS distance, manual locality search, or
  both?
- Are real vendor onboarding and real transactions required, or can
  seeded demo data be used?
16. Summary
StockTalk should be delivered as a set of connected modules, with
inventory accuracy and safe bill processing at its core. Build
authentication and manual inventory first, connect OCR with a
user-confirmation step, then add vendor discovery and price history,
chat/file sharing, and finally orders and payments. Keep sensitive data
private, verify payments on the backend, and demonstrate the complete
shopkeeper-to-vendor workflow.