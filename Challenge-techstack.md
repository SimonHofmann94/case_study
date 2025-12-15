# Procurement AI Request System – Tech Stack Overview

This document summarizes the proposed **production-oriented** tech stack for the hackathon project in the area of *agentic AI in procurement*.

---

## 1. High-Level Architecture

The system consists of three main layers:

1. **Frontend (Web UI)** – Built with React & Next.js, used by requestors and procurement staff. IMPORTANT: check for latest exploits of Next.js and React. Use a safe version of them.
2. **Backend For Frontend (BFF)** – Next.js API routes acting as a server-side layer tailored to the frontend.
3. **Core Backend & AI Services** – FastAPI application handling business logic, persistence, and agentic AI workflows.

Data is persisted in a relational database (PostgreSQL) accessed via SQLAlchemy ORM.

---

## 2. Frontend

**Technologies**

- **React** (via Next.js)
- **Next.js (App Router, TypeScript)** IMPORTANT: when using TypeScript try not to use the any type. Use interfaces or types instead.
- Optional UI library (e.g., MUI / Chakra / shadcn/ui) to accelerate layout & components. Use a clean and modern UI library. Main colors should be subtle and not too bold (use black, brown, gray, darker green and turquoise, etc.)

**Responsibilities**

- Render all user-facing pages:
  - Create/edit procurement request form.
  - Request overview and detail view 
  - Upload vendor offer documents.
- Interact only with the BFF (Next.js API routes) for data fetching and actions.
- Perform lightweight client-side validation and UX enhancements (e.g., inline form validation, progress indicators).

---

## 3. Backend For Frontend (BFF)

**Technologies**

- **Next.js API routes** (Node.js, TypeScript)

**Purpose & Responsibilities**

- Serve as a **Backend For Frontend** tailored to the UI.
- Expose **simplified endpoints** for the frontend, such as:
  - `POST /api/requests`
  - `POST /api/requests/from-offer`
  - `GET /api/requests`
  - `GET /api/requests/:id`
  - `POST /api/requests/:id/status`
- Orchestrate calls to the **FastAPI backend** and other services from the server side.
- Centralize:
  - Authentication & session handling (if added).
  - Response shaping specifically for frontend needs.
  - Hiding internal services and credentials from the browser.

The BFF is a thin layer: it should contain minimal business logic and primarily delegate to FastAPI.

---

## 4. Core Backend (Business Logic & API)

**Technologies**

- **FastAPI** (Python)
- **Uvicorn** as the ASGI server (for development and basic production setup).
- **Pydantic** for request/response models and validation.
- **SQLAlchemy (ORM)** for database access.

**Responsibilities**

- Expose RESTful endpoints for core domain operations (consumed by the BFF):
  - CRUD operations for procurement requests.
  - Management of order lines.
  - Request status transitions (Open → In Progress → Closed) with history tracking.
  - Handling vendor offer file uploads and returning AI-extracted drafts.
- Implement business rules and validations:
  - Ensuring only valid requests are persisted.
  - Validating consistency of order lines and totals.
- Coordinate interactions with the agentic AI layer (LangGraph/LangChain workflows).

**Process Model**

- Run the FastAPI application using **Uvicorn** as the ASGI server.
- For a true production setup, this could be extended later with a process manager such as **Gunicorn + Uvicorn workers**, but this is intentionally out of scope for the initial implementation.

---

## 5. Agentic AI Layer

**Technologies**

- **LangGraph** – primary orchestration engine for agentic workflows.
- **LangChain** – toolkit for LLMs, tools, structured output, and integrations.
- One or more **LLM providers** (e.g., OpenAI, etc.), configurable via environment variables.

**Responsibilities & Flows**

1. **Vendor Offer Parsing & Auto-Fill**
   - Accept a document (PDF/text) from the FastAPI backend.
   - Extract structured fields: vendor, VAT ID, order lines (description, quantity, unit price, total), currency, and totals.
   - Return a structured draft that can pre-fill the request form.

2. **Commodity Group Suggestion**
   - Use request context (title/description, line items) and the known commodity group catalog.
   - Suggest the most suitable commodity group, possibly with:
     - Confidence scores.
     - Alternative suggestions.
     - Short explanation for the choice.

3. **Validation & Normalization**
   - Optionally verify and normalize extracted data (e.g., numeric fields, currency formats).
   - Provide a clean, typed structure back to FastAPI.

These workflows are modeled as a **graph** in LangGraph, with nodes such as:
- `parse_offer_document`
- `normalize_and_validate_fields`
- `suggest_commodity_group`
- `finalize_request_draft`

FastAPI acts as the entry point and calls into these workflows.

---

## 6. Database & Persistence

**Technologies**

- **PostgreSQL** – primary relational database for production.
- **SQLAlchemy ORM** (optionally with SQLModel or similar) for mapping Python classes to database tables.
- **Alembic** (or similar) for schema migrations.

**Data Model (Conceptual)**

Core entities:

- `Request`
  - Request metadata (requestor, department, vendor, VAT ID, total cost, currency, commodity group, created/updated timestamps).
- `OrderLine`
  - FK to `Request`, item description, quantity, unit price, calculated line total, etc.
- `StatusHistory`
  - FK to `Request`, status value (Open/In Progress/Closed), timestamp, optional actor/user.
- `Attachment` (optional, but useful)
  - FK to `Request`, file metadata (filename, MIME type, storage location / URL).

**Environment Flexibility**

- Use **PostgreSQL** for production deployments.
- For local development or constrained hackathon setups, **SQLite** can be used as a drop-in replacement, as long as the schema remains portable (no SQLite-specific features).

---

## 7. Infrastructure & Deployment Considerations

**Containerization**

- Package both Next.js and FastAPI apps in separate Docker images.
- Configure environment variables for:
  - Database connection strings.
  - LLM / AI provider API keys.
  - Any service URLs (FastAPI endpoint, etc.).

**Deployment Sketch**

- **Frontend + BFF (Next.js)** – can be deployed to a platform like Vercel or any container platform.
- **Backend (FastAPI + Uvicorn)** – deployed to a container hosting platform (e.g., Render, Fly.io, Kubernetes cluster, etc.).
- **Database (PostgreSQL)** – managed DB instance in the same region as the FastAPI backend.

**Non-Functional Aspects (Conceptual Targets)**

- Input validation on all external interfaces (BFF and FastAPI).
- Basic logging & error handling in FastAPI (including AI-related failures).
- Clear separation of concerns:
  - UI in the frontend.
  - Thin BFF layer for UI-oriented APIs.
  - Business logic and AI workflows encapsulated in the FastAPI + LangGraph stack.

---

## 8. Summary

This stack is designed to be:

- **Hackathon-friendly** – fast to develop with, thanks to Next.js, FastAPI, and Python’s AI ecosystem.
- **Production-oriented** – incorporates patterns like BFF, an ASGI server (Uvicorn), PostgreSQL with an ORM, and explicit agentic workflows via LangGraph.
- **Extensible** – can scale from a single-node demo to a more robust deployment with minimal architectural changes.
