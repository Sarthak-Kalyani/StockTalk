
# StockTalk Backend Integration Contract

## Module ownership

- Person 1: Authentication, users, profiles, roles, authorization
- Person 2: Inventory, OCR, pricing
- Person 3: Vendor discovery, catalogues, B2B chat,
  attachments, notifications
- Person 4: Orders, payments, reports

## Decisions required before integration

1. User ID format: integer or UUID
2. Authentication: JWT, secure session cookie, or agreed alternative
3. Current-user dependency: shared FastAPI authentication dependency
4. User roles: shopkeeper and vendor
5. Database: shared PostgreSQL/Supabase configuration
6. Schema ownership and migration process
7. Shared API response and error conventions

## Person 3 endpoints currently implemented

### Vendor discovery
- POST /vendors/catalogue
- GET /vendors/catalogue
- GET /vendors/catalogue/{product_id}
- POST /vendors/location
- GET /vendors/nearby

### Conversations and messages
- POST /conversations
- GET /conversations
- POST /conversations/{conversation_id}/messages
- GET /conversations/{conversation_id}/messages
- POST /conversations/{conversation_id}/read
- GET /conversations/unread-counts

### Attachments
- POST /conversations/{conversation_id}/attachments
- GET /conversations/{conversation_id}/attachments
- GET /conversations/{conversation_id}/attachments/{attachment_id}/download

### Real-time chat
- WebSocket /ws/conversations/{conversation_id}

## Current prototype limitations

- Uses SQLite locally.
- Uses demo user IDs 100 and 1.
- Some endpoints accept user IDs from request bodies or query parameters.
- WebSocket connections use a user_id query parameter.
- Database tables are currently created using SQLAlchemy
  create_all during application startup.

These are prototype limitations, not production authentication.

## Integration requirements

- Use the shared authenticated identity instead of trusting
  client-supplied sender or user IDs.
- Reference the agreed shared users table and ID format.
- Add foreign keys and migrations for shared database tables.
- Verify conversation participation for messages and attachments.
- Authorize vendor catalogue and location updates.
- Protect private file downloads and WebSocket connections.
- Keep credentials in environment variables, never source code.
