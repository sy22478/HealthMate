from fastapi import FastAPI
import os

app = FastAPI(title="HealthMate Minimal", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "HealthMate Minimal API is running"}

@app.get("/health")
async def health_check():
    return {"status": "ok", "port": os.getenv("PORT", "8000")}

@app.get("/test")
async def test():
    return {"status": "ok", "message": "Test endpoint working"}

@app.get("/health/debug")
async def debug_health_check():
    return {
        "status": "ok",
        "port": os.getenv("PORT", "8000"),
        "environment": os.getenv("ENVIRONMENT", "unknown"),
        "message": "Minimal app working"
    } 