# Testing Guide

This guide explains how to test the Procurement AI MVP implementation.

## Prerequisites

1. **Docker Desktop** must be running
2. Environment files must be configured (`.env` files created from `.env.example`)

## Quick Start - Testing with Docker

### 1. Start Docker Desktop

Make sure Docker Desktop is running on your system.

### 2. Start the Services

```bash
cd c:/Users/User/PycharmProjects/case_study

# Start all services
docker compose up -d
```

### 3. Run Database Migrations

```bash
# Run Alembic migrations to create the database schema
docker compose exec backend alembic upgrade head
```

### 4. Test the API Endpoints

#### Option A: Using FastAPI Swagger UI (Recommended)

1. Open your browser and navigate to: `http://localhost:8000/docs`
2. You'll see the interactive API documentation
3. Try the following endpoints:

**Register a new user:**
- Click on `POST /auth/register`
- Click "Try it out"
- Use this example request body:
```json
{
  "email": "test@example.com",
  "password": "SecurePass123!",
  "full_name": "Test User",
  "role": "requestor",
  "department": "Engineering"
}
```
- Click "Execute"
- You should receive a 201 response with user data and an access token

**Login:**
- Click on `POST /auth/login`
- Click "Try it out"
- Use:
```json
{
  "email": "test@example.com",
  "password": "SecurePass123!"
}
```
- Click "Execute"
- You should receive a 200 response with user data and access token

**Get Current User:**
- Click on `POST /auth/me`
- Click "Authorize" button (top right)
- Paste the access token from the login response
- Click "Authorize"
- Click "Try it out" then "Execute"
- You should see your user information

#### Option B: Using curl

```bash
# Register a user
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!",
    "full_name": "Test User",
    "role": "requestor",
    "department": "Engineering"
  }'

# Login
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'

# Get current user (replace TOKEN with the access_token from login response)
curl -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer TOKEN"
```

### 5. Run the Test Suite

Run the comprehensive pytest test suite:

```bash
# Run all tests
docker compose exec backend pytest

# Run with verbose output
docker compose exec backend pytest -v

# Run only authentication tests
docker compose exec backend pytest tests/auth/

# Run with coverage report
docker compose exec backend pytest --cov=app --cov-report=term-missing
```

### 6. Test Rate Limiting

The authentication endpoints have rate limiting enabled:
- `/auth/register` - 5 requests per minute
- `/auth/login` - 10 requests per minute

To test rate limiting, try making more than 5 registration requests in a minute from the same IP. You should receive a 429 (Too Many Requests) response.

### 7. Check Logs

View service logs:

```bash
# All services
docker compose logs

# Backend only
docker compose logs backend

# Follow logs in real-time
docker compose logs -f backend
```

## Testing Checklist

- [ ] Docker Desktop is running
- [ ] Services started successfully (`docker compose up -d`)
- [ ] Database migrations ran successfully (`alembic upgrade head`)
- [ ] Can register a new user via API
- [ ] Can login with registered user
- [ ] Can access protected endpoint (`/auth/me`) with token
- [ ] Invalid credentials are rejected
- [ ] Weak passwords are rejected
- [ ] Rate limiting works (try exceeding limits)
- [ ] All pytest tests pass

## Expected Test Results

When running `pytest`, you should see:
- Tests for password hashing (5+ tests)
- Tests for password validation (5+ tests)
- Tests for JWT token generation (5+ tests)
- Tests for registration endpoint (6+ tests)
- Tests for login endpoint (5+ tests)
- Tests for /auth/me endpoint (5+ tests)

**Total: 30+ tests should PASS**

## Troubleshooting

### Docker Desktop not running
**Error:** `open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified`
**Solution:** Start Docker Desktop and wait for it to fully initialize

### Port already in use
**Error:** `Bind for 0.0.0.0:8000 failed: port is already allocated`
**Solution:** Stop other services using port 8000 or change the port in `docker-compose.yml`

### Database connection error
**Error:** `sqlalchemy.exc.OperationalError`
**Solution:** Ensure PostgreSQL container is running: `docker compose ps`

### Module not found errors
**Error:** `ModuleNotFoundError: No module named 'fastapi'`
**Solution:** This should not happen when using Docker. Rebuild the image: `docker compose build backend`

## Next Steps

Once all tests pass, you can proceed with:
- Day 2: Database Schema & Core Models
- Frontend development
- Additional features

## Stopping the Services

```bash
# Stop all services
docker compose down

# Stop and remove volumes (fresh start)
docker compose down -v
```
