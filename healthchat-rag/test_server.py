#!/usr/bin/env python3
"""
Simple test server to verify FastAPI setup
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="HealthMate Test API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "HealthMate Test API is running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "message": "All systems operational"}

@app.get("/test-mcp")
async def test_mcp():
    try:
        # Test importing MCP modules
        from app.mcp.types import ChunkMetadata, DiagnosisResult, DiagnosisUrgency
        from app.mcp.medical_data import EMERGENCY_KEYWORDS
        from app.mcp.rag_server import AdvancedRAGServer
        from app.mcp.diagnosis_server import DifferentialDiagnosisServer
        
        return {
            "status": "success",
            "message": "MCP modules imported successfully",
            "emergency_keywords_count": len(EMERGENCY_KEYWORDS)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"MCP import failed: {str(e)}"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 