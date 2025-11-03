# Product Service Documentation

## Overview

This directory contains framework-agnostic business requirements for the Product Service.

## Documents

### 📋 [PRD.md](./PRD.md) - Product Requirements Document

**Purpose**: Defines **WHAT** the Product Service must do from a business perspective.

**Contains**:

- Business requirements (REQ-1.x through REQ-6.x)
- Non-functional requirements (NFR-1.x through NFR-5.x)
- API contracts
- Event schemas (framework-agnostic)
- Success criteria
- Acceptance criteria

**Audience**: Product managers, business analysts, QA, developers

**Stability**: High - rarely changes unless business requirements change

**Key Point**: No mention of specific technologies (Dapr, RabbitMQ, MongoDB, etc.)

---

### 🔧 [../.github/copilot-instructions.md](../.github/copilot-instructions.md)

**Purpose**: Defines **HOW** to implement PRD requirements using our chosen tech stack.

**Contains**:

- Technology decisions (Python, FastAPI, MongoDB, Dapr)
- Implementation patterns and code examples
- Dapr configuration and setup
- Migration plan from message-broker-service to Dapr
- Copilot prompt templates
- Testing guidelines
- Performance optimization tips

**Audience**: Developers, GitHub Copilot

**Stability**: Medium - changes when tech decisions change

**Key Point**: All tech-specific details go here, not in PRD.md

---

## How to Use These Documents

### For Developers

**Starting a new feature**:

1. Read PRD.md to understand the business requirement (e.g., REQ-2.1: Text Search)
2. Read copilot-instructions.md for implementation approach (MongoDB text indexes)
3. Use Copilot with this prompt:
   ```
   "Implement PRD REQ-2.1 (text search) using the approach in
   .github/copilot-instructions.md. Match API contract in PRD.md."
   ```

**During Dapr migration**:

1. PRD.md stays unchanged (business requirements don't change)
2. copilot-instructions.md updated with Dapr patterns
3. Use Copilot:
   ```
   "Migrate event publishing to Dapr following .github/copilot-instructions.md.
   Maintain PRD REQ-3.x requirements."
   ```

### For GitHub Copilot Agent

**Prompt pattern**:

```
"Read docs/PRD.md [requirement section].
Implement using .github/copilot-instructions.md [tech pattern].
Ensure [specific validation/test]."
```

**Example**:

```
"Read docs/PRD.md REQ-3.1 (publish product.created event).
Implement using Dapr pub/sub pattern in .github/copilot-instructions.md.
Ensure event schema matches PRD Event Schemas section."
```

### For Code Reviews

**Checklist**:

- ✅ Does implementation meet PRD requirement?
- ✅ Does implementation follow copilot-instructions.md tech patterns?
- ✅ Does event schema match PRD specification exactly?
- ✅ Are all PRD NFR requirements met (performance, security, etc.)?

---

## Document Structure Philosophy

```
┌─────────────────────────────────────────────────────────┐
│                    PRD.md                                │
│             (WHAT - Business Requirements)               │
│                                                          │
│  "Product Service must publish events when              │
│   products are created, updated, or deleted"            │
│                                                          │
│  ✅ Framework-agnostic                                   │
│  ✅ Technology-agnostic                                  │
│  ✅ Long-term stable                                     │
└─────────────────────────────────────────────────────────┘
                        ▲
                        │ References
                        │
┌─────────────────────────────────────────────────────────┐
│          .github/copilot-instructions.md                 │
│             (HOW - Implementation Decisions)             │
│                                                          │
│  "Use Dapr Pub/Sub for event publishing                 │
│   with RabbitMQ backend. Here's the code pattern..."    │
│                                                          │
│  ✅ Tech-specific                                        │
│  ✅ Implementation details                               │
│  ✅ Can change without affecting PRD                     │
└─────────────────────────────────────────────────────────┘
```

---

## Migration Context

### Current State

- **Event Publishing**: HTTP to message-broker-service
- **File**: `src/services/message_broker_publisher.py`

### Target State (Documented in copilot-instructions.md)

- **Event Publishing**: Dapr Pub/Sub
- **New File**: `src/services/dapr_publisher.py` (to be created)
- **Components**: `dapr/components/pubsub-rabbitmq.yaml` (to be created)

### Migration Status

- ✅ PRD.md created (framework-agnostic requirements)
- ✅ copilot-instructions.md created (Dapr implementation guide)
- ❌ Dapr implementation not yet started
- ❌ Dapr components not yet created

---

## Next Steps

1. **Review Documents**

   - Read PRD.md to understand business requirements
   - Read copilot-instructions.md to understand tech approach

2. **Start Dapr Migration**

   - Create `src/services/dapr_publisher.py`
   - Create `dapr/components/pubsub-rabbitmq.yaml`
   - Update `src/controllers/product_controller.py`
   - Add Dapr sidecar to docker-compose

3. **Use Copilot for Implementation**

   - Follow prompt patterns in copilot-instructions.md
   - Reference both documents in prompts

4. **Validate Against PRD**
   - Ensure all REQ-\* requirements still met
   - Ensure all NFR-\* requirements still met
   - Event schemas must match exactly

---

## Benefits of This Approach

### ✅ Separation of Concerns

- Business requirements separate from tech decisions
- PRD readable by non-technical stakeholders
- Tech details in developer-focused document

### ✅ Flexibility

- Can switch from Dapr to another framework
- Only copilot-instructions.md needs updating
- PRD remains valid regardless of tech stack

### ✅ Maintainability

- Business requirements rarely change
- Tech decisions evolve more frequently
- Clear ownership of each document

### ✅ Better Copilot Results

- Clear context separation
- Specific prompts with both business + tech context
- Easier to verify compliance with requirements

---

## Questions?

**Q: What if business requirement changes?**
A: Update PRD.md. Implementation in copilot-instructions.md may need adjustment.

**Q: What if we switch from Dapr to something else?**
A: Update copilot-instructions.md only. PRD.md stays the same.

**Q: Where do I put API endpoint details?**
A: API contracts (request/response formats) → PRD.md
Implementation (FastAPI code) → copilot-instructions.md

**Q: Where do event schemas go?**
A: Event structure (JSON schema) → PRD.md (framework-agnostic)
Event publishing code → copilot-instructions.md (Dapr-specific)
