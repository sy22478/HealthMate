import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_symptoms_emergency():
    data = {"symptoms": ["chest pain"], "severity": "severe"}
    response = client.post("/health/symptoms", json=data)
    assert response.status_code == 200
    result = response.json()
    assert result["urgency"] == "emergency"
    assert "emergency" in result["urgency"]
    assert "immediate medical attention" in result["message"].lower()

def test_symptoms_routine():
    data = {"symptoms": ["headache"], "severity": "mild"}
    response = client.post("/health/symptoms", json=data)
    assert response.status_code == 200
    result = response.json()
    assert result["urgency"] == "routine"
    assert "consulting" in result["message"].lower() or "monitor" in result["recommendations"][0].lower()

def test_drug_interactions_positive():
    data = {"medications": ["warfarin", "aspirin"]}
    response = client.post("/health/drug-interactions", json=data)
    assert response.status_code == 200
    result = response.json()
    assert result["interactions_found"] is True
    assert any("bleeding" in i for i in result["interactions"])

def test_drug_interactions_negative():
    data = {"medications": ["acetaminophen"]}
    response = client.post("/health/drug-interactions", json=data)
    assert response.status_code == 200
    result = response.json()
    assert result["interactions_found"] is False
    assert result["interactions"] == [] 