from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from app.services.health_functions import check_symptoms, calculate_bmi, check_drug_interactions

router = APIRouter()

class BMICalcRequest(BaseModel):
    weight_kg: float
    height_m: float

class SymptomCheckRequest(BaseModel):
    symptoms: List[str]
    severity: str

class DrugInteractionRequest(BaseModel):
    medications: List[str]

@router.post("/bmi")
def bmi_calc(data: BMICalcRequest):
    return calculate_bmi(data.weight_kg, data.height_m)

@router.post("/symptoms")
def symptom_check(data: SymptomCheckRequest):
    return check_symptoms(data.symptoms, data.severity)

@router.post("/drug-interactions")
def drug_interactions(data: DrugInteractionRequest):
    return check_drug_interactions(data.medications) 