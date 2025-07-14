from openai import OpenAI
from typing import Dict, List
from app.services.health_functions import check_symptoms, calculate_bmi, check_drug_interactions
import json

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
        """Chat with medical context and user profile, handle function calls."""
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
        msg = response.choices[0].message
        # Handle function call if present
        if hasattr(msg, "function_call") and msg.function_call:
            fn_name = msg.function_call.name
            try:
                args = json.loads(msg.function_call.arguments)
            except Exception:
                args = {}
            if fn_name == "check_symptoms":
                result = check_symptoms(**args)
            elif fn_name == "calculate_bmi":
                result = calculate_bmi(**args)
            elif fn_name == "check_drug_interactions":
                result = check_drug_interactions(**args)
            else:
                result = {"message": "Unknown function call."}
            # Return the function result as a string
            return result.get("message") or json.dumps(result)
        # Otherwise, return the model's message content
        return msg.content or "Sorry, I couldn't understand your question." 