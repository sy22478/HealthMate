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