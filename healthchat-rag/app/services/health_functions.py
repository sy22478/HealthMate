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