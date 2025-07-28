# HealthChat RAG

## Project Overview
Build a conversational AI health assistant that combines personal health data with authoritative medical sources using Retrieval-Augmented Generation (RAG), OpenAI Agent SDK, and modern Python technologies. This project targets a Machine Learning Engineer role at ClosedLoopAI.

## Tech Stack
- **Language**: Python
- **Backend**: FastAPI
- **Database**: PostgreSQL + Pinecone (vector DB)
- **Frontend**: Streamlit
- **AI/ML**: OpenAI Agent SDK, Function Calling, RAG
- **Protocol**: Model Context Protocol (MCP)
- **Auth**: JWT tokens

## Project Structure
```
healthchat-rag/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── models/                 # Database models
│   ├── routers/                # API endpoints
│   ├── services/               # Business logic
│   ├── utils/                  # Utilities
│   └── config.py               # Configuration
├── frontend/
│   ├── streamlit_app.py        # Streamlit UI
│   └── components/             # UI components
├── data/
│   ├── medical_knowledge/      # Medical data sources
│   └── embeddings/             # Vector embeddings
├── tests/
├── requirements.txt
├── .env.example
└── README.md
```

## Setup Instructions

### 1. Create virtual environment
```bash
python -m venv healthchat-env
source healthchat-env/bin/activate  # Linux/Mac
# healthchat-env\Scripts\activate  # Windows
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment variables
- Copy `.env.example` to `.env` and fill in required values (API keys, DB URIs, etc.)

### 4. Run the backend
```bash
uvicorn app.main:app --reload
```

### 5. Run the frontend
```bash
streamlit run frontend/streamlit_app.py
```

---

For detailed development steps, see `Context.md`.

## Running Tests with Coverage

To run all tests and see a code coverage report locally:

```bash
pytest --cov=healthchat-rag/app --cov-report=term-missing healthchat-rag/tests/
```

Coverage is also reported automatically in CI (see the Actions tab on GitHub).

## Feature Branch Workflow

To keep the `main` branch stable and enable easy code review:

- **Create a new branch for each feature or bugfix**
  - Use descriptive names, e.g., `feature/emergency-routing`, `fix/login-bug`
- **Push your branch and open a Pull Request (PR) to `main`**
- **Merge via PR after review and CI pass**
- **Delete the feature branch after merging**

### Example
```bash
git checkout main
git pull origin main
git checkout -b feature/your-feature-name
# ... work, commit ...
git push origin feature/your-feature-name
# Open a PR on GitHub
```

After merging:
```bash
git checkout main
git pull origin main
git branch -d feature/your-feature-name
git push origin --delete feature/your-feature-name
```

## Testing Policy

- All new features and bugfixes must include appropriate unit and/or integration tests.
- Pull requests without tests for new code will not be merged.
- Run all tests locally with `pytest` before pushing.
- Aim to increase or maintain overall test coverage with every change.

## Enabling HTTPS/TLS (Secure Communication)

### Local Development (Self-Signed Certificates)
To run the backend with HTTPS locally:

1. Generate a self-signed certificate (if you don't have one):
   ```bash
   openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout key.pem -out cert.pem -subj "/CN=localhost"
   ```
2. Start the backend with SSL enabled:
   ```bash
   uvicorn app.main:app --reload --ssl-keyfile=key.pem --ssl-certfile=cert.pem
   ```
3. Your API will now be available at `https://localhost:8000` (browser will warn about self-signed cert).

> **Note:** Add `key.pem` and `cert.pem` to your `.gitignore` to avoid committing them.

### Production (Recommended)
- Run FastAPI/uvicorn behind a reverse proxy (e.g., Nginx, Caddy, Traefik) that handles HTTPS/TLS termination.
- The reverse proxy should forward requests to your FastAPI app over HTTP (or HTTPS if desired).
- This is more secure and flexible for real deployments.

For more details, see the FastAPI docs: https://fastapi.tiangolo.com/deployment/

## CORS (Cross-Origin Resource Sharing)

The backend uses CORS middleware to control which web origins can access the API.

### Current Configuration (Development)
In `app/main.py` and `app/main_simple.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (development only)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
This allows requests from any origin, which is convenient for local development and testing.

### Best Practices for Production
- **Restrict allowed origins**: Replace `allow_origins=["*"]` with a list of trusted frontend URLs, e.g.:
  ```python
  allow_origins=["https://your-frontend.com", "https://admin.your-frontend.com"]
  ```
- **Why restrict?**
  - Prevents unauthorized web apps from making requests to your API.
  - Reduces risk of CSRF and data leaks.
- **How to change?**
  - Edit the `allow_origins` parameter in your FastAPI app configuration.

> **Note:** Never use `allow_origins=["*"]` in production for sensitive APIs.

## CORS Configuration (Cross-Origin Resource Sharing)

By default, the backend allows all origins (CORS_ALLOW_ORIGINS="*") for development. **For production, you should restrict CORS to trusted domains.**

- To restrict CORS, set the `CORS_ALLOW_ORIGINS` environment variable to a comma-separated list of allowed origins:
  ```bash
  export CORS_ALLOW_ORIGINS="https://yourdomain.com,https://app.yourdomain.com"
  ```
- The backend will then only accept requests from these origins.
- Leaving `CORS_ALLOW_ORIGINS="*"` is insecure for production and should only be used for local development/testing.
