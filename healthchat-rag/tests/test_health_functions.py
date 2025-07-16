import pytest
from app.services.health_functions import check_symptoms, calculate_bmi, check_drug_interactions

def test_check_symptoms_emergency():
    result = check_symptoms(["chest pain"], "severe")
    assert result["urgency"] == "emergency"
    assert "emergency" in result["urgency"]
    assert "immediate medical attention" in result["message"].lower()

def test_check_symptoms_routine():
    result = check_symptoms(["headache"], "mild")
    assert result["urgency"] == "routine"
    assert "consulting" in result["message"].lower() or "monitor" in result["recommendations"][0].lower()

def test_calculate_bmi_normal():
    result = calculate_bmi(70, 1.75)
    assert result["category"] == "Normal weight"
    assert 18.5 <= result["bmi"] <= 24.9

def test_calculate_bmi_obese():
    result = calculate_bmi(120, 1.6)
    assert result["category"] == "Obese"
    assert result["bmi"] > 30

def test_check_drug_interactions_positive():
    result = check_drug_interactions(["warfarin", "aspirin"])
    assert result["interactions_found"] is True
    assert any("bleeding" in i for i in result["interactions"])

def test_check_drug_interactions_negative():
    result = check_drug_interactions(["acetaminophen"])
    assert result["interactions_found"] is False
    assert result["interactions"] == [] 