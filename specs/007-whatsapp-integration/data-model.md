# Data Model: WhatsApp Integration

## `WhatsAppIntegration` (SQLAlchemy Model)
- `id`: Integer, Primary Key
- `owner_id`: UUID, Foreign Key to User
- `project_id`: Integer, Foreign Key to Project
- `name`: String
- `phone_number`: String (Optional, extracted after QR scan)
- `session_id`: String (Unique identifier for Baileys session)
- `status`: String (pending, active, error, inactive)
- `system_prompt`: String (Custom prompt for this specific WhatsApp bot)
- `fallback_message`: String
- `human_handoff_enabled`: Boolean
- `show_sources_to_customer`: Boolean
- `created_at` / `updated_at`

## `WhatsAppCustomer` (SQLAlchemy Model)
- `id`: Integer, Primary Key
- `owner_id`: UUID
- `phone_number`: String (Unique constraint with owner_id)
- `name`: String
- `created_at` / `updated_at`

## `Conversation` (Update to existing Model)
- Add `channel`: Enum/String (e.g., `telegram`, `whatsapp`, `web`)
- Add `whatsapp_integration_id`: Integer, Foreign Key to WhatsAppIntegration
- Add `whatsapp_customer_id`: Integer, Foreign Key to WhatsAppCustomer
