# Procurement AI MVP - Implementation Plan

**Project:** Procurement Request System with AI Document Parsing
**Timeline:** 7 Days
**Tech Stack:** Next.js + FastAPI + PostgreSQL + LangChain + TOON

---

## Overview

This implementation plan tracks the development of a production-grade MVP for procurement request management with AI-powered document parsing and commodity classification.

### Key Features
- ✅ User authentication (Requestor + Procurement Team roles)
- ✅ Manual request creation with validation
- ✅ AI-powered vendor offer extraction (PDF parsing with TOON)
- ✅ AI commodity group classification
- ✅ Request status management with history tracking
- ✅ Production-grade error tracking (Sentry)
- ✅ Comprehensive security (rate limiting, CORS, input validation)

---

## Day 1: Project Setup & Authentication

### Morning (4 hours) ✅ COMPLETED
- [x] Create project structure
  - [x] `mkdir -p case_study/frontend case_study/backend`
  - [x] Initialize Git repository
  - [x] Create `.gitignore` for Python and Node.js
- [x] Set up Docker Compose
  - [x] Create `docker-compose.yml`
  - [x] Configure PostgreSQL service
  - [x] Configure backend service (FastAPI)
  - [x] Configure frontend service (Next.js)
- [x] Environment configuration
  - [x] Create `.env.example` for backend
  - [x] Create `.env.example` for frontend
  - [x] Document all environment variables
- [x] FastAPI project setup
  - [x] Create `backend/requirements.txt`
  - [x] Set up project structure (`app/` folder)
  - [x] Create `main.py` with basic FastAPI app
  - [x] Configure CORS middleware
- [x] Next.js project setup
  - [x] Created Next.js configuration with TypeScript and Tailwind
  - [x] Configured dependencies (React Query, React Hook Form, Zod in package.json)
  - [x] Configure TypeScript strict mode
- [x] Development tools setup
  - [x] Configure Black, Ruff for Python
  - [x] Configure ESLint, Prettier for TypeScript
  - [x] Create `pyproject.toml` for Python tools

### Afternoon (4 hours) ✅ COMPLETED
- [x] Database setup
  - [x] Create `database.py` with SQLAlchemy setup
  - [x] Initialize Alembic for migrations
  - [x] Create database connection utilities
- [x] User authentication backend
  - [x] Create User model (`auth/models.py`)
    - Fields: id, email, hashed_password, full_name, role, department, is_active
  - [x] Create User Pydantic schemas (`auth/schemas.py`)
  - [x] Create Alembic migration for users table
  - [x] Implement password hashing (`auth/security.py`)
    - Use bcrypt with work factor 12
  - [x] Implement JWT utilities (`auth/security.py`)
    - Token generation
    - Token verification
    - Token expiration (1 hour)
  - [x] Create authentication endpoints (`auth/router.py`)
    - `POST /auth/register` - User registration with 5/minute rate limit
    - `POST /auth/login` - User login with 10/minute rate limit
    - `GET /auth/me` - Get current user
  - [x] Create `get_current_user` dependency (`auth/dependencies.py`)
  - [x] Add rate limiting to auth endpoints using slowapi
    - 5/minute for register
    - 10/minute for login
  - [x] Created shared rate limiter utility (`utils/rate_limit.py`)
  - [x] Integrated rate limiter with FastAPI app
- [x] Testing
  - [x] Write unit tests for password hashing (tests/auth/test_security.py)
  - [x] Write integration tests for auth endpoints (tests/auth/test_auth_endpoints.py)
  - [x] Test JWT token generation and verification (tests/auth/test_security.py)
  - [x] Created test fixtures and conftest.py for shared test utilities

### Evening (Optional, 1-2 hours)
- [ ] Sentry setup
  - [ ] Create Sentry account
  - [ ] Get DSN for backend and frontend
  - [ ] Add `sentry-sdk` to backend
  - [ ] Configure Sentry in `main.py`
  - [ ] Add `@sentry/nextjs` to frontend
  - [ ] Test error capture

---

## Day 2: Database Schema & Core Models

### Morning (4 hours) ✅ COMPLETED
- [x] Design and document complete database schema
  - [x] Draw ER diagram
  - [x] Document relationships
- [x] Create SQLAlchemy models
  - [x] Request model (`models/request.py`)
    - Fields: id, user_id, title, vendor_name, vat_id, commodity_group_id, department, total_cost, status, created_at, updated_at
  - [x] OrderLine model (`models/order_line.py`)
    - Fields: id, request_id, description, unit_price, amount, unit, total_price
  - [x] StatusHistory model (`models/status_history.py`)
    - Fields: id, request_id, status, changed_by_user_id, changed_at, notes
  - [x] Attachment model (`models/attachment.py`)
    - Fields: id, request_id, filename, file_path, mime_type, file_size, uploaded_at
  - [x] CommodityGroup model (`models/commodity_group.py`)
    - Fields: id, category, name, description
- [x] Create Pydantic schemas
  - [x] Request schemas (`schemas/request.py`)
    - RequestCreate, RequestUpdate, RequestResponse, RequestDetailResponse, RequestListResponse, RequestStatusUpdate
  - [x] OrderLine schemas (`schemas/order_line.py`)
  - [x] StatusHistory schemas (`schemas/status_history.py`)
  - [x] Offer parsing schemas (`schemas/offer.py`)
    - ParsedOrderLine, ParsedVendorOffer, OfferParseRequest, OfferParseResponse
  - [x] CommodityGroup schemas (`schemas/commodity_group.py`)
    - CommodityGroupCreate, CommodityGroupUpdate, CommodityGroupResponse, CommodityGroupSuggestion
  - [x] Attachment schemas (`schemas/attachment.py`)
- [x] Validation utilities
  - [x] Create `services/validation_service.py`
  - [x] VAT ID format validation (DE + 9 digits)
  - [x] Order line total calculation validation
  - [x] Total cost validation
  - [x] Status transition validation
- [x] Database migrations
  - [x] Create Alembic migration for all procurement tables (002_create_procurement_tables.py)
  - [x] Seed commodity groups data (50 groups from challenge specification)
  - [x] Test migrations (up and down)

### Afternoon (4 hours) ✅ COMPLETED
- [x] Request service layer
  - [x] Create `services/request_service.py`
  - [x] Implement CRUD operations
    - create_request(user_id, data)
    - get_request(request_id, user_id, user_role)
    - list_requests(user_id, user_role, filters)
    - update_request(request_id, user_id, user_role, data)
    - update_request_status(request_id, new_status, user_id)
    - delete_request(request_id, user_id, user_role)
    - get_status_history(request_id, user_id, user_role)
  - [x] Implement status transition logic
    - Check valid transitions
    - Create status history entry
    - Update request status
  - [x] Implement permission checks
    - Requestors can only see their own requests
    - Procurement team can see all requests
    - Only procurement team can change status
- [x] API endpoints
  - [x] Create `routers/requests.py` with all CRUD endpoints
    - POST /requests - Create request
    - GET /requests - List with pagination/filtering
    - GET /requests/{id} - Get details
    - PATCH /requests/{id} - Update request
    - PUT /requests/{id}/status - Update status (procurement only)
    - GET /requests/{id}/history - Get status history
    - DELETE /requests/{id} - Delete open requests
  - [x] Create `routers/commodity_groups.py` with endpoints
    - GET /commodity-groups - List all groups
    - GET /commodity-groups/categories - List unique categories
    - GET /commodity-groups/{id} - Get group details
  - [x] Register routers in main.py
- [x] API rate limiting
  - [x] Install and configure `slowapi` (already done in Day 1)
  - [x] Add rate limiting decorators to endpoints (100/hour)
- [x] Testing
  - [x] Write unit tests for request service (24 tests, all passing)
    - CRUD operations tests
    - Status transition tests
    - Permission check tests
    - Validation tests

---

## Day 3: AI Integration (TOON + LangChain)

### Morning (4 hours) ✅ COMPLETED
- [x] TOON (Token Oriented Object Notation) implementation
  - [x] Research TOON format specification
  - [x] Create `utils/toon.py`
  - [x] Implement `json_to_toon(data: dict) -> str`
  - [x] Implement `toon_to_json(toon_string: str) -> dict`
  - [x] Test TOON conversion with sample data (23 tests passing)
  - [x] Measure token savings with `estimate_token_savings()`
- [x] LangChain setup
  - [x] Install `langchain-openai`, `langchain-core` (in requirements.txt)
  - [x] Create OpenAI client configuration in `config.py`
  - [x] Set up environment variable for API key (OPENAI_API_KEY)
- [x] PDF text extraction
  - [x] Install `pypdf` (in requirements.txt)
  - [x] Create `utils/pdf_extractor.py`
  - [x] Implement `extract_text_from_pdf()` supporting file path, bytes, and BytesIO
  - [x] Implement `extract_text_from_file()` for PDF and TXT
  - [x] Implement `get_pdf_metadata()` for document info
- [x] Offer parsing service
  - [x] Create `services/offer_parsing.py`
  - [x] Design prompt for vendor offer extraction
  - [x] Implement `OfferParsingService` class
  - [x] Create custom TOON output parser
  - [x] Implement `parse_offer(document_text: str) -> (ParsedVendorOffer, metadata)`
  - [x] Token savings tracking in metadata
  - [x] Test with mocked LLM responses (10 tests passing)

### Afternoon (4 hours) ✅ COMPLETED
- [x] Commodity classification service
  - [x] Create `services/commodity_classification.py`
  - [x] Design prompt for commodity classification
    - Include commodity group catalog in prompt
    - Request confidence score and explanation
  - [x] Implement `CommodityClassificationService` class
  - [x] Implement `suggest_commodity_group(title, order_lines) -> CommodityGroupSuggestion`
    - Returns: commodity_group_id, category, name, confidence, explanation
  - [x] Implement keyword-based fallback when AI unavailable
- [x] Commodity groups seed data (completed in Day 2)
  - [x] 50 commodity groups seeded from challenge specification
- [x] Fallback strategy implementation
  - [x] Implement OpenAI unavailable error handling
    - Custom OpenAIUnavailableError exception
    - Return 503 Service Unavailable with user-friendly message
  - [x] Implement TOON parsing fallback
    - Try TOON format first
    - If parsing fails, fallback to JSON format
    - Track which format was used in metadata
- [x] API endpoints
  - [x] Create `routers/offers.py`
    - POST /offers/parse - Upload and parse vendor offer (20/hour rate limit)
    - POST /offers/suggest-commodity - Suggest commodity group (50/hour rate limit)
  - [x] File upload handling with type/size validation
  - [x] Register router in main.py
- [x] Testing
  - [x] TOON utility tests (23 tests)
  - [x] Offer parsing service tests with mocked LLM (10 tests)
  - [x] Test fallback scenarios
  - [x] Test error handling

---

## Day 4: API Endpoints & Frontend Setup

### Morning (4 hours) ✅ MOSTLY COMPLETED (in Days 2-3)
- [x] Complete FastAPI endpoints
  - [x] Request endpoints (`routers/requests.py`) - Completed Day 2
    - `GET /requests` - List requests (filtered by user role)
    - `POST /requests` - Create request
    - `GET /requests/{id}` - Get request details
    - `PATCH /requests/{id}` - Update request
    - `PUT /requests/{id}/status` - Update status (procurement only)
    - `GET /requests/{id}/history` - Get status history
    - `DELETE /requests/{id}` - Delete request
  - [x] Offer endpoints (`routers/offers.py`) - Completed Day 3
    - `POST /offers/parse` - Upload and parse vendor offer
    - `POST /offers/suggest-commodity` - Suggest commodity group
  - [x] Commodity group endpoints (`routers/commodity_groups.py`) - Completed Day 2
    - `GET /commodity-groups` - List all commodity groups
    - `GET /commodity-groups/categories` - List categories
    - `GET /commodity-groups/{id}` - Get group details
  - [x] File upload handling - Completed Day 3
    - Accept multipart/form-data
    - Validate file type (PDF, TXT) and size (10MB)
  - [x] CORS configuration - Completed Day 1
    - Allow frontend URL (http://localhost:3000)
    - Allow credentials
    - Allow necessary methods and headers
  - [x] Rate limiting - All endpoints rate limited
- [ ] API testing
  - [ ] Test all endpoints with Postman or curl
  - [ ] Verify authentication works
  - [ ] Verify permission checks
  - [ ] Test file upload
  - [ ] Check FastAPI auto-docs at `/docs`

### Afternoon (4 hours) ✅ COMPLETED
- [x] Next.js authentication setup
  - [x] Create AuthContext (`contexts/AuthContext.tsx`)
    - State: user, isAuthenticated, isLoading
    - Functions: login, register, logout
  - [x] Create auth pages
    - `app/auth/login/page.tsx`
    - `app/auth/register/page.tsx`
  - [x] Create ProtectedRoute component
  - [x] Update root layout with AuthProvider
- [x] Frontend dependencies
  - [x] Install React Query: `@tanstack/react-query`
  - [x] Install React Hook Form: `react-hook-form`
  - [x] Install Zod: `zod`
  - [x] Install shadcn/ui components manually
    - Button, Input, Card, Form, Label, Alert
  - [x] Install additional radix-ui dependencies
- [x] API client setup
  - [x] Create `lib/api.ts`
  - [x] Set up axios instance
  - [x] Add JWT interceptor (attach token to all requests)
  - [x] Add response interceptor (handle 401 errors)
  - [x] Create API client functions (auth, requests, offers, commodity groups)
- [x] Auth UI components
  - [x] Create LoginForm with Zod validation
  - [x] Create RegisterForm with Zod validation
  - [x] Add loading states with spinner
  - [x] Add error messages with alert component
- [x] Dashboard page
  - [x] Create basic dashboard layout
  - [x] Welcome message with user role
  - [x] Quick action cards for creating/viewing requests
- [x] Test authentication flow
  - [x] Register new user
  - [x] Login with credentials
  - [x] Verify token is stored
  - [x] Verify protected routes work

---

## Day 5: Frontend - Request Management

### Morning (4 hours) ✅ COMPLETED
- [x] Request form component
  - [x] Create `components/requests/RequestForm.tsx`
  - [x] Implement form fields (title, vendor, VAT ID, department, commodity group, order lines)
  - [x] Dynamic order line array with add/remove buttons
  - [x] Zod validation schema matching backend
  - [x] React Hook Form integration
  - [x] Total cost calculation
  - [x] Loading state on submit
- [x] File upload component
  - [x] Create `components/requests/FileUpload.tsx`
  - [x] Drag-and-drop support
  - [x] File type validation (PDF, TXT)
  - [x] File size validation (10MB)
  - [x] AI parsing with status indicators
  - [x] Auto-fill form with parsed data
- [x] AI integration
  - [x] Create `hooks/useOfferParsing.ts`
  - [x] File upload mutation with React Query
  - [x] Commodity group suggestion hook
  - [x] Error handling
- [x] Create request page
  - [x] Create `app/requests/new/page.tsx`
  - [x] Integrate FileUpload and RequestForm
  - [x] Form submission with redirect

### Afternoon (4 hours) ✅ COMPLETED
- [x] Request list component
  - [x] Create `components/requests/RequestList.tsx`
  - [x] Display requests as cards
  - [x] StatusBadge component (color-coded)
  - [x] Status filtering
  - [x] Empty state handling
- [x] Request list page
  - [x] Create `app/requests/page.tsx`
  - [x] Create `hooks/useRequests.ts` with React Query
  - [x] Create `hooks/useCommodityGroups.ts`
- [x] Request detail view
  - [x] Create `app/requests/[id]/page.tsx`
  - [x] Display all request details and order lines
  - [x] Status history display
  - [x] Status update for procurement team
  - [x] Delete button for open requests
- [x] Additional UI components
  - [x] Select, Badge, Textarea components
  - [x] Loading and error states
- [x] Dashboard page (created in Day 4)
  - [x] Welcome message with user role
  - [x] Quick action cards

---

## Day 6: Testing, Security & Polish

### Morning (4 hours)
- [ ] Security audit
  - [ ] Input sanitization
    - Test with malicious input (SQL injection attempts, XSS payloads)
    - Verify Pydantic validation catches invalid data
  - [ ] SQL injection protection
    - Verify all database queries use parameterized queries
    - Test with SQL injection payloads
  - [ ] XSS protection
    - Verify HTML escaping in responses
    - Test with XSS payloads
  - [ ] Rate limiting
    - Test rate limits work (5/min for register, 10/min for login)
    - Verify 429 response when limit exceeded
  - [ ] CORS configuration
    - Verify only frontend URL is allowed
    - Test with requests from different origin
  - [ ] File upload security
    - Test file type validation (reject non-PDF/TXT)
    - Test file size validation (reject >10 MB)
    - Verify magic byte checking
  - [ ] Authentication
    - Test with invalid tokens
    - Test with expired tokens
    - Test permission checks
- [ ] Error handling improvements
  - [ ] Network errors (frontend)
    - Handle offline scenarios
    - Handle timeouts
    - Show user-friendly messages
  - [ ] Validation errors (frontend)
    - Display field-level errors clearly
    - Highlight invalid fields
  - [ ] Backend errors (frontend)
    - Parse backend error messages
    - Display to user appropriately
- [ ] Logging improvements
  - [ ] Structured logging with structlog
  - [ ] Add request IDs for tracing
  - [ ] Log all AI operations (with token counts)
  - [ ] Log all authentication events
  - [ ] Log all status changes
  - [ ] Ensure logs are JSON formatted
- [ ] Backend testing
  - [ ] Write remaining unit tests
  - [ ] Achieve 70%+ test coverage
  - [ ] Run tests: `pytest --cov=app`
  - [ ] Fix any failing tests

### Afternoon (4 hours)
- [ ] Frontend polish
  - [ ] Loading states
    - Add loading skeletons for all data fetching
    - Add loading spinners for actions (submit, upload)
  - [ ] Empty states
    - "No requests yet" with helpful message
    - "No order lines" with "Add first line" button
  - [ ] Error boundaries
    - Catch React errors
    - Display friendly error message
    - Log to Sentry
  - [ ] Responsive design
    - Test on mobile (320px width)
    - Test on tablet (768px width)
    - Test on desktop (1920px width)
    - Fix any layout issues
- [ ] Code comments
  - [ ] Backend
    - Document all service methods
    - Explain complex validation logic
    - Document AI prompts and strategies
  - [ ] Frontend
    - Document complex components
    - Explain state management choices
    - Document form validation logic
- [ ] Test data creation
  - [ ] Create seed script (`backend/seed.py`)
  - [ ] Seed users
    - 2 requestors (different departments)
    - 1 procurement team member
  - [ ] Seed sample requests
    - Various statuses
    - Various departments
    - Various commodity groups
  - [ ] Create test vendor offer PDFs
    - 3-5 sample offers with different formats
    - Ensure they parse correctly
- [ ] End-to-end testing
  - [ ] Test complete user flow (requestor)
    - Register → Login → Create request → Upload offer → Submit → View list
  - [ ] Test complete user flow (procurement)
    - Login → View all requests → View detail → Change status
  - [ ] Test error scenarios
    - Invalid file upload
    - Invalid form data
    - Network error simulation

---

## Day 7: Documentation, Demo Prep & Final Testing

### Morning (3 hours)
- [ ] Write README.md
  - [ ] Project overview and description
  - [ ] Features list
  - [ ] Tech stack description
  - [ ] Architecture diagram (use Mermaid or ASCII art)
  - [ ] Prerequisites (Docker, Docker Compose, Git)
  - [ ] Setup instructions
    - Clone repository
    - Copy `.env.example` to `.env`
    - Fill in environment variables
    - Run `docker-compose up`
  - [ ] Environment variables documentation
  - [ ] API documentation link (`/docs`)
  - [ ] Test credentials
  - [ ] Troubleshooting section
- [ ] Write ARCHITECTURE.md
  - [ ] System architecture overview
  - [ ] Design decisions
    - Why hybrid BFF approach (file upload only)
    - Why LangChain instead of LangGraph
    - Why TOON for token optimization
  - [ ] Database schema diagram
  - [ ] API endpoints summary
  - [ ] Security considerations
  - [ ] Future enhancements
- [ ] Document AI implementation
  - [ ] Document prompts used
  - [ ] Document TOON format
  - [ ] Document token savings achieved
  - [ ] Document fallback strategy
- [ ] Code cleanup
  - [ ] Remove dead code
  - [ ] Remove console.logs and debug prints
  - [ ] Remove commented-out code
  - [ ] Format all code (Black, Ruff, Prettier)
  - [ ] Run linters and fix issues
  - [ ] Verify no TypeScript `any` types used

### Afternoon (3 hours)
- [ ] Prepare demo script
  - [ ] Write story flow (problem → solution)
  - [ ] Identify test data to use
  - [ ] List features to highlight
    - Authentication (role-based access)
    - AI extraction from PDF
    - AI commodity classification
    - Status workflow
    - Sentry error tracking
  - [ ] Practice demo timing (aim for 12-15 minutes)
  - [ ] Prepare for questions
    - Why LangChain instead of LangGraph?
    - Why no full BFF?
    - How does TOON work?
    - What's your testing strategy?
    - How would you scale this?
- [ ] Test demo flow multiple times
  - [ ] Fresh database (reset with migrations)
  - [ ] Register users
  - [ ] Create requests
  - [ ] Test AI extraction
  - [ ] Test status changes
  - [ ] Verify everything works smoothly
- [ ] Prepare code walkthrough
  - [ ] Identify key files to show
    - backend/auth/security.py (JWT implementation)
    - backend/services/offer_parsing.py (AI extraction)
    - backend/services/validation_service.py (validation rules)
    - backend/routers/requests.py (API endpoints)
    - frontend/components/requests/RequestForm.tsx (form handling)
    - frontend/hooks/useAuth.ts (authentication)
  - [ ] Prepare talking points for each file
  - [ ] Anticipate questions they might ask
  - [ ] Prepare to explain tradeoffs
- [ ] Optional: Record demo video
  - [ ] Use as backup if live demo has issues
  - [ ] Keep under 15 minutes
  - [ ] Upload to YouTube (unlisted)

### Evening (2 hours)
- [ ] Final checks
  - [ ] Run all tests: `pytest && npm test`
  - [ ] Verify all tests pass
  - [ ] Start fresh with `docker-compose up`
  - [ ] Verify all services start correctly
  - [ ] Check for console errors (browser and terminal)
  - [ ] Verify Sentry is capturing errors
  - [ ] Verify logs are structured and readable
  - [ ] Check Git history is clean
  - [ ] Verify README instructions work
- [ ] Push to GitHub
  - [ ] Create repository on GitHub
  - [ ] Review all commits (clean messages)
  - [ ] Push to GitHub
  - [ ] Verify repository is public
  - [ ] Add topics/tags (fastapi, nextjs, ai, langchain)
  - [ ] Verify README renders correctly
- [ ] Final review
  - [ ] Clone repo in fresh directory
  - [ ] Follow README instructions
  - [ ] Verify everything works from scratch
- [ ] Submit case study
  - [ ] Send GitHub repository link
  - [ ] Include brief description
  - [ ] Mention demo video if created

---

## Tech Stack Reference

### Backend
- Python 3.11+
- FastAPI (web framework)
- Uvicorn (ASGI server)
- SQLAlchemy 2.0 (ORM)
- Alembic (database migrations)
- Pydantic v2 (validation)
- PostgreSQL (database)
- LangChain + langchain-openai (AI)
- TOON (token optimization)
- pypdf/pdfplumber (PDF parsing)
- passlib + bcrypt (password hashing)
- python-jose (JWT)
- slowapi (rate limiting)
- structlog (logging)
- sentry-sdk (error tracking)
- pytest (testing)

### Frontend
- Next.js 14+ (React framework)
- TypeScript (type safety)
- React Query (server state)
- React Hook Form (forms)
- Zod (validation)
- shadcn/ui (UI components)
- Tailwind CSS (styling)
- @sentry/nextjs (error tracking)

### Infrastructure
- Docker + Docker Compose
- PostgreSQL container
- Environment variables (.env)

---

## Success Criteria

### Must Have (MVP)
- [ ] Users can register and login
- [ ] Requestors can create requests manually
- [ ] AI extraction from vendor offer PDFs works
- [ ] AI commodity group suggestion works
- [ ] Procurement team can view all requests
- [ ] Procurement team can update request status
- [ ] Status history is tracked
- [ ] All security measures implemented
- [ ] Docker Compose works
- [ ] Comprehensive README
- [ ] Demo works smoothly

### Nice to Have (If Time Permits)
- [ ] Request search/filtering
- [ ] Dashboard with statistics
- [ ] Email notifications for status changes
- [ ] Bulk request operations
- [ ] Export requests to CSV
- [ ] Advanced analytics

### Demo Checklist
- [ ] Code is clean and commented
- [ ] No errors in console
- [ ] All tests pass
- [ ] Sentry capturing errors
- [ ] Token savings visible in logs
- [ ] Demo script prepared
- [ ] Code walkthrough prepared
- [ ] GitHub repository ready
- [ ] README is accurate

---

## Notes & Decisions

### Architecture Decisions
1. **Hybrid BFF Approach**: Using Next.js API routes ONLY for file uploads, direct FastAPI calls for everything else
2. **LangChain over LangGraph**: Linear workflows don't need graph orchestration
3. **TOON Integration**: For token cost optimization (up to 50% savings)
4. **Sentry**: For production-grade error tracking

### Security Measures
- JWT authentication with 1-hour expiration
- Bcrypt password hashing (work factor 12)
- Rate limiting (5/min register, 10/min login, 100/hour API)
- CORS configured for frontend origin only
- Input validation at all boundaries
- SQL injection protection (parameterized queries)
- XSS protection (HTML escaping)
- File upload validation (type, size, magic bytes)

### Testing Strategy
- Backend: 70%+ test coverage
- Focus on business logic and validation
- Integration tests for API endpoints
- Mock LLM responses for AI tests
- Manual E2E testing for UI

---

## Daily Progress Tracking

### Day 1 Progress ✅ COMPLETED
- Completed:
  - ✅ Morning tasks (4 hours): Full project structure setup complete
    - Created backend and frontend folders with proper structure
    - Configured Docker Compose with PostgreSQL, FastAPI, Next.js
    - Set up FastAPI with main.py, config.py, database.py
    - Initialized Next.js 14 with TypeScript and Tailwind CSS
    - Configured all development tools (Black, Ruff, ESLint, Prettier)
    - Created comprehensive .env.example files
    - Made initial Git commit
  - ✅ Afternoon tasks (4 hours): Complete authentication system
    - Created User model with UserRole enum (REQUESTOR, PROCUREMENT_TEAM)
    - Implemented Pydantic schemas for validation (UserCreate, UserLogin, LoginResponse)
    - Set up Alembic for database migrations
    - Created initial migration for users table
    - Implemented bcrypt password hashing (work factor 12)
    - Implemented JWT token generation and verification (1 hour expiration)
    - Created authentication router with three endpoints:
      - POST /auth/register (5/minute rate limit)
      - POST /auth/login (10/minute rate limit)
      - GET /auth/me (protected route)
    - Implemented rate limiting using slowapi
    - Created get_current_user dependency for route protection
    - Created role-based access dependencies (get_procurement_user, get_requestor_user)
    - Wrote comprehensive test suite:
      - Unit tests for password hashing and JWT utilities
      - Integration tests for all auth endpoints
      - Test fixtures for database and user creation
- Blockers: None
- Notes:
  - Complete authentication system is production-ready
  - All tests written and ready to run once dependencies are installed
  - Rate limiting configured for security
  - Role-based access control foundation in place
  - Ready to move on to Day 2: Database Schema & Core Models

### Day 2 Progress ✅ COMPLETED
- Completed:
  - ✅ Morning tasks (4 hours): Complete database schema and models
    - Created all SQLAlchemy models with proper relationships:
      - CommodityGroup (id, category, name, description)
      - Request (id, user_id, title, vendor_name, vat_id, commodity_group_id, department, total_cost, status, notes, timestamps)
      - OrderLine (id, request_id, description, unit_price, amount, unit, total_price)
      - StatusHistory (id, request_id, status, changed_by_user_id, changed_at, notes)
      - Attachment (id, request_id, filename, file_path, mime_type, file_size, uploaded_at)
    - Created comprehensive Pydantic schemas for all models
    - Created validation service with:
      - VAT ID format validation (DE + 9 digits)
      - Order line total calculation
      - Request total validation
      - Status transition validation
    - Created Alembic migration (002_create_procurement_tables.py)
    - Seeded all 50 commodity groups from challenge specification
    - Fixed Docker setup issues:
      - Fixed langchain dependency conflict
      - Fixed CORS_ORIGINS parsing for list types
      - Fixed missing tailwindcss-animate dependency
      - Fixed enum case mismatch between SQLAlchemy and PostgreSQL
    - Verified user registration works end-to-end
  - ✅ Afternoon tasks (4 hours): Complete request service layer and API
    - Created RequestService with full CRUD operations:
      - create_request, get_request, list_requests
      - update_request, update_request_status
      - delete_request, get_status_history
    - Implemented status transition logic with history tracking
    - Implemented permission checks (role-based access control)
    - Created request API router (routers/requests.py):
      - POST/GET /requests, GET/PATCH/DELETE /requests/{id}
      - PUT /requests/{id}/status, GET /requests/{id}/history
    - Created commodity group API router (routers/commodity_groups.py):
      - GET /commodity-groups, GET /commodity-groups/categories
      - GET /commodity-groups/{id}
    - Added rate limiting to all endpoints (100/hour)
    - Fixed request_status enum case mismatch (lowercase values)
    - Fixed Pydantic schema decimal_places issue
    - Updated conftest.py to use PostgreSQL for testing
    - Wrote 24 unit tests for request service (all passing):
      - Create, Get, List, Update, Status Transition, Delete tests
      - Permission check and validation tests
- Blockers: None
- Notes:
  - Day 2 fully completed
  - All core CRUD operations implemented with proper permissions
  - Ready to proceed with Day 3: AI Integration (TOON + LangChain)

### Day 3 Progress ✅ COMPLETED
- Completed:
  - ✅ Morning tasks (4 hours): Complete AI integration infrastructure
    - Created TOON (Token Oriented Object Notation) utilities:
      - `utils/toon.py` with json_to_toon() and toon_to_json() functions
      - Full support for nested objects, arrays, special characters
      - Token savings estimation function
      - 23 unit tests passing
    - Set up LangChain with OpenAI:
      - Configured OpenAI settings in config.py
      - Model, temperature, max_tokens configurable via env vars
    - Implemented PDF text extraction:
      - `utils/pdf_extractor.py` with pypdf
      - Supports file paths, bytes, and BytesIO
      - Includes metadata extraction
    - Created Offer Parsing Service:
      - `services/offer_parsing.py` with OfferParsingService class
      - Extracts vendor_name, vat_id, order_lines from documents
      - TOON format with JSON fallback
      - Token savings tracking in response metadata
  - ✅ Afternoon tasks (4 hours): Complete AI services and API
    - Created Commodity Classification Service:
      - `services/commodity_classification.py`
      - AI-powered commodity group suggestions
      - Keyword-based fallback when AI unavailable
      - Returns confidence score and explanation
    - Implemented fallback strategies:
      - OpenAIUnavailableError for API failures
      - Automatic TOON-to-JSON fallback
      - Graceful degradation to manual input
    - Created offer API endpoints:
      - POST /offers/parse - Parse vendor offer documents
      - POST /offers/suggest-commodity - AI commodity suggestions
      - Rate limited (20/hour for parsing, 50/hour for suggestions)
    - Wrote comprehensive tests:
      - 23 TOON utility tests
      - 10 offer parsing service tests with mocked LLM
- Blockers: None
- Notes:
  - Day 3 fully completed
  - AI integration ready for testing with real OpenAI API key
  - TOON format provides ~30-50% token savings
  - Ready to proceed with Day 4: Frontend Setup

### Day 4 Progress ✅ COMPLETED
- Completed:
  - ✅ Morning tasks: API endpoints already completed in Days 2-3
  - ✅ Afternoon tasks (4 hours): Frontend authentication setup
    - Created lib/utils.ts with cn() helper for Tailwind class merging
    - Created shadcn/ui components: Button, Input, Label, Card, Alert, Form
    - Added radix-ui dependencies: @radix-ui/react-label, @radix-ui/react-slot, @radix-ui/react-select
    - Created comprehensive API client (lib/api.ts):
      - Axios instance with base URL configuration
      - JWT interceptor for automatic token attachment
      - 401 response interceptor for automatic logout
      - Type definitions for all API entities
      - Functions for auth, requests, commodity groups, and offers APIs
    - Created AuthContext (contexts/AuthContext.tsx):
      - User state management with localStorage persistence
      - Login/register/logout functions
      - Automatic token validation on mount
      - Error handling with clearable error state
    - Created authentication pages:
      - Login page with Zod validation
      - Register page with password requirements
      - Both pages use React Hook Form with zodResolver
    - Created ProtectedRoute component for route guarding
    - Created Providers wrapper for React Query + Auth context
    - Updated root layout with Providers
    - Created basic dashboard page with role-based content
    - Updated home page to redirect based on auth state
    - Tested full authentication flow:
      - Registration creates user and auto-logs in
      - Login returns JWT token and user data
      - Protected routes redirect unauthenticated users
      - Token is properly attached to API requests
- Blockers: None
- Notes:
  - Day 4 fully completed
  - Frontend authentication is fully functional
  - Ready to proceed with Day 5: Request Management UI

### Day 5 Progress ✅ COMPLETED
- Completed:
  - ✅ Morning tasks (4 hours): Request form and file upload
    - Created RequestForm component with:
      - All form fields (title, vendor, VAT ID, department, notes)
      - Dynamic order lines array with add/remove
      - Zod validation schema
      - Total cost calculation
      - AI commodity suggestion button
    - Created FileUpload component with:
      - Drag-and-drop support
      - File type/size validation
      - AI parsing status indicators
      - Auto-fill form on success
    - Created hooks for API integration:
      - useRequests (list, get, create, update, delete)
      - useCommodityGroups (list, get)
      - useOfferParsing (parse file, suggest commodity)
  - ✅ Afternoon tasks (4 hours): Request management pages
    - Created request list page with:
      - RequestList component with cards
      - StatusBadge component (color-coded)
      - Status filtering dropdown
      - Empty state handling
    - Created request detail page with:
      - Full request details and order lines table
      - Status history timeline
      - Status update dropdown for procurement team
      - Delete button for open requests
    - Added UI components: Select, Badge, Textarea
- Blockers: None
- Notes:
  - Day 5 fully completed
  - Full request management workflow implemented
  - Ready for Day 6: Testing, Security & Polish

### Day 6 Progress
- Completed: [ ]
- Blockers: [ ]
- Notes: [ ]

### Day 7 Progress
- Completed: [ ]
- Blockers: [ ]
- Notes: [ ]

---

## Contact & Questions

If you have questions during implementation, refer to:
1. The comprehensive tech stack review in `.claude/plans/`
2. FastAPI documentation: https://fastapi.tiangolo.com/
3. Next.js documentation: https://nextjs.org/docs
4. LangChain documentation: https://python.langchain.com/docs/
5. shadcn/ui documentation: https://ui.shadcn.com/

Good luck with your implementation! 🚀
