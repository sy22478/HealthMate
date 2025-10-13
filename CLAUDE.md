# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HealthMate is a conversational AI health assistant built with FastAPI, combining personal health data with authoritative medical sources using Retrieval-Augmented Generation (RAG), OpenAI Agent SDK, and PostgreSQL/Pinecone vector databases. The application targets healthcare ML engineering with JWT-based authentication, real-time WebSocket communication, and a Streamlit frontend.

## Core Architecture

### Application Entry Points

The application has **three main entry points** in `healthchat-rag/app/`:
- **`main_simple.py`**: Minimal API with mock authentication (for testing/development)
- **`main.py`**: Full production application with all features
- **`main_debug.py`**: Debug version with additional logging

Environment variable `APP_VERSION` controls which entry point is used (`simple`, `main`, or `debug`).

### Key Architectural Patterns

**1. RAG-Based AI Service Layer** (`app/services/`)
- `openai_agent.py`: OpenAI GPT-4 chat completion with function calling (check_symptoms, calculate_bmi, check_drug_interactions)
- `vector_store.py`: Pinecone vector search with OpenAI embeddings and spaCy-based chunking
- `knowledge_base.py`: Medical knowledge retrieval and context augmentation

**2. Database Architecture** (`app/models/`)
- PostgreSQL via SQLAlchemy with connection pooling (pool_size=5, max_overflow=2)
- Core models: `User`, `Conversation`, health data models, notification models
- Uses Alembic for migrations (run from `healthchat-rag/` directory)

**3. Authentication & Security**
- JWT tokens with refresh mechanism (see `app/services/auth.py`, `app/utils/jwt_utils.py`)
- Password hashing via `passlib[bcrypt]` (see `app/utils/password_utils.py`)
- RBAC system with roles: patient, doctor, admin (see `app/utils/rbac.py`)
- Audit logging for sensitive operations (see `app/utils/audit_logging.py`)
- Encryption utilities for sensitive data (see `app/utils/encryption_utils.py`)

**4. Real-time Communication** (`app/websocket/`)
- WebSocket connection manager with state tracking and pooling
- Channels: chat messaging, health updates, notifications
- Authentication happens on connection with JWT validation

**5. Configuration System** (`app/config.py`)
- All settings use `HEALTHMATE_` prefix (e.g., `HEALTHMATE_OPENAI_API_KEY`)
- Reads from `.env` file via `pydantic-settings`
- Key settings: API keys, database URI, CORS origins, security headers, notification providers

### Router Organization

The FastAPI routers in `app/routers/` are organized by domain:
- `auth.py`: Registration, login, password reset
- `chat.py` / `enhanced_chat.py`: AI chat endpoints
- `health.py` / `health_data.py`: Health metrics and data management
- `websocket.py`: WebSocket endpoint registration
- `mobile.py`: Mobile-specific API endpoints
- `analytics.py` / `advanced_analytics.py` / `visualization.py`: Data analytics
- `admin.py`: Administrative functions
- Other specialized routers for compliance, ML, webhooks, etc.

## Development Commands

### Running the Application

**Backend (from repository root):**
```bash
# Using startup script (recommended)
./start_healthmate.sh                    # Simple version on port 8004
APP_VERSION=main ./start_healthmate.sh   # Full version
APP_VERSION=debug ./start_healthmate.sh  # Debug version

# Or manually from healthchat-rag/
cd healthchat-rag
uvicorn app.main_simple:app --host 0.0.0.0 --port 8004 --reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend:**
```bash
./start_frontend.sh
# Or manually:
cd healthchat-rag/frontend
streamlit run streamlit_app.py
```

**Important**: Frontend expects backend on `HEALTHMATE_API_URL` environment variable (defaults to `http://localhost:8000`).

### Testing

**Run all tests:**
```bash
cd healthchat-rag
pytest
```

**Run with coverage:**
```bash
pytest --cov=app --cov-report=term-missing tests/
```

**Run specific test types (using markers):**
```bash
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m auth          # Authentication tests
pytest -m chat          # Chat/AI tests
pytest -m health        # Health data tests
```

**Run single test file:**
```bash
pytest tests/test_enhanced_chat_ai.py -v
```

**Configuration**: See `pytest.ini` for test configuration (80% coverage requirement, parallel execution with `-n auto`).

### Database Migrations

**Run migrations (from healthchat-rag/):**
```bash
cd healthchat-rag
alembic upgrade head
```

**Create new migration:**
```bash
alembic revision --autogenerate -m "Description of changes"
```

**Rollback migration:**
```bash
alembic downgrade -1
```

**Important**: Always run Alembic commands from the `healthchat-rag/` directory, not the root.

### Linting and Code Quality

No explicit linter configuration found in repository. Follow Python PEP 8 conventions.

## Critical Implementation Details

### Environment Variables

All environment variables must use the `HEALTHMATE_` prefix:
- `HEALTHMATE_OPENAI_API_KEY`: OpenAI API key for GPT-4
- `HEALTHMATE_PINECONE_API_KEY`: Pinecone vector DB key
- `HEALTHMATE_PINECONE_ENVIRONMENT`: Pinecone environment
- `HEALTHMATE_PINECONE_INDEX_NAME`: Pinecone index name
- `HEALTHMATE_POSTGRES_URI`: PostgreSQL connection string
- `HEALTHMATE_SECRET_KEY`: JWT signing key
- `HEALTHMATE_ENVIRONMENT`: `development` or `production`
- `HEALTHMATE_CORS_ALLOW_ORIGINS`: CORS origins (use `*` for dev, specific domains for prod)

See `app/config.py` for complete list.

### Authentication Flow

1. User registers via `/auth/register` → receives JWT access token
2. All authenticated endpoints require `Authorization: Bearer <token>` header
3. Token validation in `app/utils/auth_middleware.py` via `get_current_user` dependency
4. Refresh tokens supported via `/auth/refresh` endpoint
5. WebSocket connections authenticate via token in initial message

### Frontend-Backend Integration

- Frontend (`streamlit_app.py`) uses `auth_manager` for session management
- Session state stores token, user info, chat history
- API calls include `Authorization` header from session state
- Frontend auto-refreshes tokens on 401 responses

### Function Calling in AI Agent

The `HealthAgent` class in `app/services/openai_agent.py` implements OpenAI function calling:
- Functions registered: `check_symptoms`, `calculate_bmi`, `check_drug_interactions`
- Business logic in `app/services/health_functions.py`
- Agent automatically calls functions based on user input and returns results

### Vector Store RAG Pattern

1. Medical documents chunked using spaCy sentence boundaries (fallback to RecursiveCharacterTextSplitter)
2. Chunks embedded via OpenAI embeddings and stored in Pinecone
3. User query → vector similarity search → top-k results retrieved
4. Retrieved context passed to GPT-4 as system message alongside user query
5. GPT-4 generates contextualized response

### WebSocket Connection Management

- `ConnectionManager` in `app/websocket/connection_manager.py` tracks all active connections
- Connection states: CONNECTING → CONNECTED → AUTHENTICATED
- Supports subscriptions to channels (e.g., user-specific notifications)
- Automatic reconnection handling with retry logic

## Deployment

**Docker**: Primary deployment uses Docker (see `healthchat-rag/Dockerfile`)
- Base image: `python:3.11-slim`
- Uses start script for uvicorn launch
- Health check on `/health` endpoint
- Runs as non-root user `healthmate`

**Railway**: Configured for Railway deployment with Docker build
- `PORT` environment variable auto-injected by Railway
- Uses simple version (`main_simple.py`) by default for faster cold starts

**CI/CD**: GitHub Actions workflow (`.github/workflows/ci-cd.yml`)
- Runs tests on push/PR to `main` and `develop` branches
- PostgreSQL service container for integration tests
- Coverage reporting included

## Branch Strategy

- **`main`**: Stable production branch
- **`develop`**: Development branch (if used)
- Feature branches: `feature/feature-name`
- Bugfix branches: `fix/bug-description`

Always create PRs to `main`. Delete feature branches after merge.

## Common Patterns

**Adding a new API endpoint:**
1. Create route in appropriate router file in `app/routers/`
2. Add Pydantic schema in `app/schemas/` if needed
3. Implement business logic in `app/services/` (not in router)
4. Add authentication via `Depends(get_current_user)` if protected
5. Write tests in `tests/` with appropriate marker

**Adding a new database model:**
1. Define model in `app/models/` inheriting from `Base`
2. Create Alembic migration: `alembic revision --autogenerate -m "Add model"`
3. Run migration: `alembic upgrade head`
4. Add model to `__init__.py` exports if needed

**Modifying authentication:**
- Core logic in `app/services/auth.py` (AuthService)
- JWT utilities in `app/utils/jwt_utils.py`
- Middleware in `app/utils/auth_middleware.py`
- Never modify password hashing directly; use `password_manager` from `password_utils.py`

**Adding AI capabilities:**
- Function definitions go in `openai_agent.py` functions list
- Implementation goes in `health_functions.py`
- Update system prompts to guide when functions should be called

## Important Notes

- **CORS**: Default allows all origins (`*`) for development. Must restrict in production via `HEALTHMATE_CORS_ALLOW_ORIGINS`.
- **Security**: Never commit `.env` files or API keys. Use environment variables.
- **Port Configuration**: Backend typically runs on port 8000 (full version) or 8004 (simple version). Frontend auto-detects via environment.
- **Database Connections**: Uses connection pooling optimized for serverless databases (Neon, etc.)
- **Notification System**: Supports email (SendGrid/SMTP), SMS (Twilio), and push notifications (FCM/APNS). Configure via environment variables.
- **Test Coverage**: Minimum 80% coverage enforced in pytest configuration.
