# Feature Specification: WhatsApp Integration

**Feature Branch**: `007-whatsapp-integration`  
**Created**: 2026-06-20  
**Status**: Draft  
**Input**: User description: "i want to add whatsapp integration using Baileys as telegram integration in my project and integrate this feature in backend ,frontendand docker and all project"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Connect WhatsApp Account (Priority: P1)

As a company admin, I want to connect my WhatsApp account to the platform so that it can act as a customer support bot.

**Why this priority**: Without connecting an account, the WhatsApp integration cannot function. This is the foundation of the feature.

**Independent Test**: Can be fully tested by navigating to the integrations page, clicking "Add WhatsApp Bot", and successfully authenticating a WhatsApp account (e.g., by scanning a QR code).

**Acceptance Scenarios**:

1. **Given** the admin is on the integrations page, **When** they choose to add a WhatsApp bot, **Then** the system displays authentication instructions (like a QR code).
2. **Given** the authentication QR code is displayed, **When** the admin scans it with their WhatsApp mobile app, **Then** the system confirms the connection and marks the integration as active.

---

### User Story 2 - Automated Knowledge Base Replies (Priority: P1)

As a customer, I want to send a question to the company's WhatsApp number and receive an instant AI-generated answer based on their knowledge base.

**Why this priority**: This delivers the core value of automated customer support over the WhatsApp channel.

**Independent Test**: Can be tested by sending a message from a personal WhatsApp account to the connected business number and verifying that a correct AI reply is received.

**Acceptance Scenarios**:

1. **Given** an active WhatsApp integration, **When** a customer sends a text question, **Then** the system processes the question, retrieves knowledge base context, and replies on WhatsApp.
2. **Given** a customer asking an out-of-scope question, **When** the AI cannot find an answer, **Then** it replies with a configured fallback message.

---

### User Story 3 - Human Handoff (Priority: P2)

As a company agent, I want to view WhatsApp conversations in the dashboard and take over from the bot when human intervention is needed.

**Why this priority**: Complex queries require human intervention to maintain high customer satisfaction.

**Independent Test**: Can be tested by having the AI escalate a conversation, then the human agent replying via the dashboard, and the customer receiving the message on WhatsApp.

**Acceptance Scenarios**:

1. **Given** an escalated WhatsApp conversation, **When** a human agent types a reply in the dashboard, **Then** the customer receives the agent's message on WhatsApp.

### Edge Cases

- What happens when the WhatsApp session expires or the admin revokes the session from their phone? (System should mark integration as disconnected and alert the admin).
- How does the system handle media (images, audio, documents) sent by the customer?
- What happens if the Baileys service crashes or restarts? (Sessions should be persisted to survive restarts).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow admins to initiate a WhatsApp connection session, displaying a QR code for authentication.
- **FR-002**: System MUST persist WhatsApp session state so it survives service restarts.
- **FR-003**: System MUST receive incoming WhatsApp messages and route them to the central conversation processing pipeline (similar to Telegram).
- **FR-004**: System MUST be able to send text replies back to the customer's WhatsApp chat.
- **FR-005**: System MUST support displaying WhatsApp conversations in the unified admin dashboard alongside Telegram conversations.
- **FR-006**: System MUST gracefully handle WhatsApp disconnection events and update the integration status accordingly.

### Key Entities

- **WhatsAppIntegration**: Represents a connected WhatsApp account, linked to a specific Project/Knowledge Base.
- **WhatsAppCustomer**: Represents an end-user interacting via WhatsApp (identifiable by phone number).
- **Conversation**: An existing entity that MUST be extended to support `channel_type` (e.g., Telegram vs WhatsApp).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Admins can successfully link a WhatsApp account in under 2 minutes.
- **SC-002**: The system successfully receives incoming WhatsApp messages and queues them for processing within 2 seconds of the message hitting the server.
- **SC-003**: AI replies are delivered back to the WhatsApp customer within 5 seconds of the message being processed.
- **SC-004**: The Node.js Baileys service maintains a stable connection without crashing for at least 99% of uptime.

## Assumptions

- A new Node.js microservice will be introduced to run the `Baileys` library, as Baileys is a TypeScript/Node.js library and the main backend is Python.
- This new microservice will communicate with the Python FastAPI backend via internal HTTP APIs (webhooks).
- The Baileys session data (auth keys) will be stored in a persistent volume or the database to ensure connection continuity.
- WhatsApp media processing (images/audio) is out of scope for v1; the bot will only respond to text messages.
