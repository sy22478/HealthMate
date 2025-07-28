import logging
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from app.services.health_functions import check_symptoms, calculate_bmi, check_drug_interactions

logger = logging.getLogger(__name__)

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
    logger.info(f"BMI calculation requested", extra={"weight_kg": data.weight_kg, "height_m": data.height_m})
    return calculate_bmi(data.weight_kg, data.height_m)

@router.post("/symptoms")
def symptom_check(data: SymptomCheckRequest):
    logger.info(f"Symptom check requested", extra={"symptoms": data.symptoms, "severity": data.severity})
    return check_symptoms(data.symptoms, data.severity)

@router.post("/drug-interactions")
def drug_interactions(data: DrugInteractionRequest):
    logger.info(f"Drug interaction check requested", extra={"medications": data.medications})
    return check_drug_interactions(data.medications) 