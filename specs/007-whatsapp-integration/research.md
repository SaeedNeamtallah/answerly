# Research & Decisions: WhatsApp Integration

## Architecture: Python Backend & Node.js Baileys Bridge

**Decision**: Introduce a `whatsapp-bridge` Node.js microservice.
**Rationale**: `Baileys` is a TypeScript/Node.js library that implements the WhatsApp Web API. Our main backend is Python/FastAPI. The cleanest architecture is to run a lightweight Node.js service that handles the raw Baileys sockets and QR codes, and communicates with the FastAPI backend via HTTP Webhooks (mirroring how the official Telegram webhook works).
**Alternatives considered**: 
- Using a Python WhatsApp Web library. *Rejected* because the user explicitly specified using `Baileys`.

## Session Storage

**Decision**: Store Baileys session states in the PostgreSQL database or a shared persistent volume so they survive restarts.
**Rationale**: WhatsApp Web requires scanning a QR code. If the session state is lost on container restart, the admin would have to re-scan the QR code, which is a poor user experience.

## System Prompts & Database Integration

**Decision**: Mirror the `BotIntegration` model to create `WhatsAppIntegration`.
**Rationale**: The user requested that each WhatsApp bot has its own system prompt and acts exactly like Telegram. We will create a `WhatsAppIntegration` model that links to a `Project` (Knowledge Base) and has `system_prompt`, `fallback_message`, `status`, etc.
