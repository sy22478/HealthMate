# HealthChat RAG - Capstone Project Context

## Project Overview
Build a conversational AI health assistant that combines personal health data with authoritative medical sources using RAG, OpenAI Agent SDK, and modern Python technologies. This project targets a Machine Learning Engineer role at ClosedLoopAI.

## Tech Stack Requirements
- **Language**: Python only
- **Backend**: FastAPI
- **Database**: PostgreSQL + Pinecone (vector DB)
- **Frontend**: Streamlit
- **AI/ML**: OpenAI Agent SDK, Function Calling, RAG
- **Protocol**: Model Context Protocol (MCP)
- **Auth**: JWT tokens
- **Development**: Cursor with AI pair programming

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

## Step-by-Step Implementation

### Phase 1: Core Infrastructure

#### 1.1 Environment Setup
```bash
# Create virtual environment
python -m venv healthchat-env
source healthchat-env/bin/activate  # Linux/Mac
# healthchat-env\Scripts\activate  # Windows

# Install dependencies
pip install fastapi uvicorn sqlalchemy psycopg2-binary
pip install openai pinecone-client langchain streamlit
pip install python-jose passlib bcrypt python-multipart
pip install pydantic-settings python-dotenv pytest
```

#### 1.2 Database Models (app/models/user.py)
```python
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    age = Column(Integer)
    medical_conditions = Column(Text)  # JSON string
    medications = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(Text)
    response = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    context_used = Column(Text)  # RAG sources
```

#### 1.3 Authentication Service (app/services/auth.py)
```python
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, status

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.algorithm = "HS256"
    
    def verify_password(self, plain_password, hashed_password):
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password):
        return pwd_context.hash(password)
    
    def create_access_token(self, data: dict, expires_delta: timedelta = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
```

#### 1.4 FastAPI Main Application (app/main.py)
```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.database import get_db
from app.routers import auth, chat, health

app = FastAPI(title="HealthChat RAG API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(health.router, prefix="/health", tags=["health"])

@app.get("/")
async def root():
    return {"message": "HealthChat RAG API is running"}
```

### Phase 2: RAG System Implementation

#### 2.1 Vector Database Setup (app/services/vector_store.py)
```python
import pinecone
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List, Dict

class VectorStore:
    def __init__(self, api_key: str, environment: str, index_name: str):
        pinecone.init(api_key=api_key, environment=environment)
        self.index = pinecone.Index(index_name)
        self.embeddings = OpenAIEmbeddings()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
    
    def add_documents(self, documents: List[Dict]):
        """Add medical documents to vector store"""
        for doc in documents:
            chunks = self.text_splitter.split_text(doc['content'])
            for i, chunk in enumerate(chunks):
                vector = self.embeddings.embed_query(chunk)
                self.index.upsert([(
                    f"{doc['source']}_{i}",
                    vector,
                    {"text": chunk, "source": doc['source'], "title": doc['title']}
                )])
    
    def similarity_search(self, query: str, k: int = 5) -> List[Dict]:
        """Search for similar medical content"""
        query_vector = self.embeddings.embed_query(query)
        results = self.index.query(
            vector=query_vector,
            top_k=k,
            include_metadata=True
        )
        return [
            {
                "text": match.metadata["text"],
                "source": match.metadata["source"],
                "score": match.score
            }
            for match in results.matches
        ]
```

#### 2.2 Medical Knowledge Ingestion (app/services/knowledge_base.py)
```python
import json
from pathlib import Path
from typing import List, Dict

class MedicalKnowledgeBase:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
    
    def load_medical_sources(self):
        """Load trusted medical sources"""
        sources = [
            {
                "source": "CDC",
                "title": "Disease Information",
                "content": "CDC guidelines and disease information...",
                "url": "https://cdc.gov"
            },
            {
                "source": "Mayo Clinic",
                "title": "Symptom Checker",
                "content": "Mayo Clinic symptom information...",
                "url": "https://mayoclinic.org"
            },
            # Add more sources
        ]
        
        self.vector_store.add_documents(sources)
    
    def get_relevant_context(self, query: str, user_profile: Dict) -> str:
        """Get relevant medical context for user query"""
        # Enhance query with user medical conditions
        enhanced_query = f"{query} {user_profile.get('medical_conditions', '')}"
        
        results = self.vector_store.similarity_search(enhanced_query)
        
        context = "Relevant medical information:\n"
        for result in results:
            context += f"Source: {result['source']}\n"
            context += f"Content: {result['text']}\n\n"
        
        return context
```

### Phase 3: OpenAI Agent SDK Integration

#### 3.1 Health Functions (app/services/health_functions.py)
```python
from typing import Dict, List
import json

def check_symptoms(symptoms: List[str], severity: str) -> Dict:
    """Analyze user symptoms and provide guidance"""
    # Emergency conditions
    emergency_symptoms = ["chest pain", "difficulty breathing", "severe bleeding"]
    
    if any(symptom.lower() in " ".join(symptoms).lower() for symptom in emergency_symptoms):
        return {
            "urgency": "emergency",
            "message": "Please seek immediate medical attention or call emergency services.",
            "recommendations": ["Call 911 or go to emergency room"]
        }
    
    return {
        "urgency": "routine",
        "message": "Consider consulting with healthcare provider if symptoms persist.",
        "recommendations": ["Monitor symptoms", "Rest", "Stay hydrated"]
    }

def calculate_bmi(weight_kg: float, height_m: float) -> Dict:
    """Calculate BMI and provide health category"""
    bmi = weight_kg / (height_m ** 2)
    
    if bmi < 18.5:
        category = "Underweight"
    elif bmi < 25:
        category = "Normal weight"
    elif bmi < 30:
        category = "Overweight"
    else:
        category = "Obese"
    
    return {
        "bmi": round(bmi, 2),
        "category": category,
        "healthy_range": "18.5 - 24.9"
    }

def check_drug_interactions(medications: List[str]) -> Dict:
    """Check for potential drug interactions"""
    # Simplified interaction checker
    interactions = []
    
    # Add basic interaction rules
    if "warfarin" in medications and "aspirin" in medications:
        interactions.append("Warfarin and aspirin may increase bleeding risk")
    
    return {
        "interactions_found": len(interactions) > 0,
        "interactions": interactions,
        "recommendation": "Consult pharmacist or doctor about potential interactions"
    }
```

#### 3.2 OpenAI Agent Service (app/services/openai_agent.py)
```python
from openai import OpenAI
from typing import Dict, List
from app.services.health_functions import check_symptoms, calculate_bmi, check_drug_interactions

class HealthAgent:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4"
        
        self.functions = [
            {
                "name": "check_symptoms",
                "description": "Analyze user symptoms and provide guidance",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symptoms": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of symptoms"
                        },
                        "severity": {
                            "type": "string",
                            "description": "Severity level: mild, moderate, severe"
                        }
                    },
                    "required": ["symptoms", "severity"]
                }
            },
            {
                "name": "calculate_bmi",
                "description": "Calculate BMI and health category",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "weight_kg": {"type": "number"},
                        "height_m": {"type": "number"}
                    },
                    "required": ["weight_kg", "height_m"]
                }
            },
            {
                "name": "check_drug_interactions",
                "description": "Check for medication interactions",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "medications": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["medications"]
                }
            }
        ]
    
    def chat_with_context(self, message: str, context: str, user_profile: Dict) -> str:
        """Chat with medical context and user profile"""
        system_prompt = f"""
        You are a helpful health assistant. Use the provided medical context and user profile to give personalized, accurate health information.
        
        IMPORTANT DISCLAIMERS:
        - Always remind users that this is not a substitute for professional medical advice
        - Encourage users to consult healthcare providers for serious concerns
        - Never provide specific medical diagnoses
        
        User Profile: {json.dumps(user_profile)}
        Medical Context: {context}
        """
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            functions=self.functions,
            function_call="auto"
        )
        
        return response.choices[0].message.content
```

### Phase 4: UI Development & Integration

#### 4.1 Streamlit Frontend (frontend/streamlit_app.py)
```python
import streamlit as st
import requests
import json
from datetime import datetime

# App configuration
st.set_page_config(
    page_title="HealthChat RAG",
    page_icon="🏥",
    layout="wide"
)

# Session state initialization
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'token' not in st.session_state:
    st.session_state.token = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

def authenticate(email: str, password: str):
    """Authenticate user with backend"""
    response = requests.post(
        "http://localhost:8000/auth/login",
        json={"email": email, "password": password}
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        st.session_state.authenticated = True
        st.session_state.token = token
        return True
    return False

def send_message(message: str):
    """Send message to chat API"""
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    response = requests.post(
        "http://localhost:8000/chat/message",
        json={"message": message},
        headers=headers
    )
    
    if response.status_code == 200:
        return response.json()["response"]
    return "Error: Could not process message"

# Main UI
def main():
    st.title("🏥 HealthChat RAG")
    st.markdown("Your AI-powered health assistant with personalized medical insights")
    
    if not st.session_state.authenticated:
        # Login form
        with st.form("login_form"):
            st.subheader("Login")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            
            if st.form_submit_button("Login"):
                if authenticate(email, password):
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid credentials")
    else:
        # Chat interface
        st.subheader("Chat with Your Health Assistant")
        
        # Display chat history
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.write(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask about your health..."):
            # Add user message
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            
            # Get AI response
            with st.spinner("Thinking..."):
                response = send_message(prompt)
            
            # Add AI response
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            
            st.rerun()

if __name__ == "__main__":
    main()
```

## Development Guidelines

### AI-Assisted Development with Cursor
1. Use Cursor's AI features for code generation and completion
2. Leverage GitHub Copilot for function implementations
3. Use AI for code reviews and optimizations
4. Document AI assistance used in development process

### Safety & Compliance
1. Implement medical disclaimer on all responses
2. Add content filtering for inappropriate medical advice
3. Emergency detection and appropriate routing
4. HIPAA-compliant data handling practices

### Testing Strategy
1. Unit tests for all service functions
2. Integration tests for API endpoints
3. End-to-end tests for user flows
4. RAG quality evaluation metrics

### Deployment Considerations
1. Environment variables for API keys
2. PostgreSQL database setup
3. Pinecone vector database configuration
4. Docker containerization for deployment

## Success Metrics
- RAG retrieval accuracy > 85%
- Response time < 2 seconds
- User satisfaction rating > 4.0/5
- Zero inappropriate medical advice incidents

## Portfolio Documentation
1. Architecture diagrams
2. Demo video showcasing features
3. Performance benchmarks
4. Safety measures implemented
5. Code quality metrics
