# Procurement AI MVP

AI-powered procurement request management system with automated document parsing and commodity classification.

## Project Status

**Day 1 - Project Setup & Authentication**: ✅ Complete
- Project structure created
- Docker Compose configuration ready
- Backend (FastAPI) with full authentication system
- User model with role-based access (Requestor & Procurement Team)
- JWT authentication with bcrypt password hashing
- Rate limiting on auth endpoints
- Comprehensive test suite (30+ tests)
- Frontend (Next.js) initialized
- Development tools configured

**See [TESTING.md](TESTING.md) for instructions on testing the implementation.**

## Features

- **User Authentication**: Role-based access (Requestor & Procurement Team)
- **AI Document Parsing**: Automatic vendor offer extraction from PDFs
- **Smart Classification**: AI-powered commodity group suggestions
- **Request Management**: Complete workflow with status tracking
- **Production-Grade**: Sentry error tracking, rate limiting, security measures

## 🛠 Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Relational database
- **SQLAlchemy 2.0** - ORM with Alembic migrations
- **LangChain + OpenAI** - AI integration with TOON optimization
- **Pydantic v2** - Data validation
- **Sentry** - Error tracking

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **TailwindCSS** - Styling
- **React Query** - Server state management
- **React Hook Form + Zod** - Form handling
- **shadcn/ui** - UI components

### Infrastructure
- **Docker + Docker Compose** - Containerization
- **PostgreSQL** - Database in Docker
- **Uvicorn** - ASGI server

## 🏗 Project Structure

```
procurement-ai-mvp/
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── main.py            # FastAPI app entry point
│   │   ├── config.py          # Configuration management
│   │   ├── database.py        # Database setup
│   │   ├── auth/              # Authentication module
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── routers/           # API endpoints
│   │   ├── services/          # Business logic
│   │   └── utils/             # Utilities
│   ├── tests/                 # Backend tests
│   ├── requirements.txt       # Python dependencies
│   ├── pyproject.toml         # Tool configuration
│   └── Dockerfile             # Backend container
│
├── frontend/                   # Next.js application
│   ├── app/                   # Next.js App Router
│   ├── components/            # React components
│   ├── lib/                   # Utilities
│   ├── hooks/                 # Custom hooks
│   ├── contexts/              # React contexts
│   ├── package.json           # Node dependencies
│   └── Dockerfile             # Frontend container
│
├── uploads/                    # File upload storage
├── docker-compose.yml          # Container orchestration
└── implementation-plan.md      # 7-day implementation plan
```

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Git
- OpenAI API Key

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd procurement-ai-mvp
   ```

2. **Set up environment variables**
   ```bash
   # Backend
   cp backend/.env.example backend/.env
   # Edit backend/.env and add your OPENAI_API_KEY

   # Frontend
   cp frontend/.env.example frontend/.env
   ```

3. **Start Docker Desktop**
   - Ensure Docker Desktop is running

4. **Start with Docker Compose**
   ```bash
   docker compose up --build
   ```

5. **Run database migrations**
   ```bash
   docker compose exec backend alembic upgrade head
   ```

6. **Access the applications**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

7. **Test the implementation**
   - See [TESTING.md](TESTING.md) for comprehensive testing instructions
   - Try the authentication endpoints at http://localhost:8000/docs

## Development

### Backend Development

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload

# Run tests
pytest

# Format code
black .
ruff .

# Type checking
mypy app
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Run linter
npm run lint

# Format code
npm run format

# Type check
npm run type-check
```

## Implementation Progress

- [x] Day 1: Project Setup & Authentication ✅ **COMPLETE**
- [ ] Day 2: Database Schema & Core Models
- [ ] Day 3: AI Integration (TOON + LangChain)
- [ ] Day 4: API Endpoints & Frontend Setup
- [ ] Day 5: Frontend Request Management
- [ ] Day 6: Testing, Security & Polish
- [ ] Day 7: Documentation & Demo Prep

See [implementation-plan.md](implementation-plan.md) for detailed daily tasks.

## Security Features

- JWT authentication with bcrypt password hashing
- Rate limiting on API endpoints
- CORS configuration
- Input validation at all boundaries
- SQL injection protection
- XSS protection
- File upload validation

## Documentation

- **API Docs**: Available at `/docs` when running backend
- **Implementation Plan**: See [implementation-plan.md](implementation-plan.md)
- **Architecture Details**: See `.claude/plans/` directory

## 🤝 Contributing

This is a case study project. See implementation plan for development roadmap.

## 📄 License

MIT License - This is a demo project for interview purposes.

---

**Built with ❤️ for production-grade MVP demonstration**
