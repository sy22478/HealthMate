"""
Enhanced Chat Service
Provides advanced chat functionality with health data integration
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from app.models.user import User, Conversation
from app.models.health_data import HealthData, SymptomLog, MedicationLog
from app.services.openai_agent import HealthAgent
from app.services.health_analytics import HealthAnalyticsService
from app.utils.encryption_utils import encryption_manager
import json

logger = logging.getLogger(__name__)

class EnhancedChatService:
    """Enhanced chat service with health data integration"""
    
    def __init__(self, db: Session, openai_api_key: str):
        self.db = db
        self.health_agent = HealthAgent(openai_api_key)
        self.analytics_service = HealthAnalyticsService(db)
    
    def get_user_health_context(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive user health context for chat"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get recent health data
            health_data = self.db.query(HealthData).filter(
                and_(
                    HealthData.user_id == user_id,
                    HealthData.timestamp >= start_date
                )
            ).order_by(desc(HealthData.timestamp)).limit(50).all()
            
            # Get recent symptoms
            symptoms = self.db.query(SymptomLog).filter(
                and_(
                    SymptomLog.user_id == user_id,
                    SymptomLog.timestamp >= start_date
                )
            ).order_by(desc(SymptomLog.timestamp)).limit(20).all()
            
            # Get recent medications
            medications = self.db.query(MedicationLog).filter(
                and_(
                    MedicationLog.user_id == user_id,
                    MedicationLog.taken_at >= start_date
                )
            ).order_by(desc(MedicationLog.taken_at)).limit(20).all()
            
            # Decrypt sensitive fields
            for data in health_data:
                data.decrypt_sensitive_fields()
            for symptom in symptoms:
                symptom.decrypt_sensitive_fields()
            for med in medications:
                med.decrypt_sensitive_fields()
            
            # Compile health context
            health_context = {
                "recent_health_data": [
                    {
                        "type": data.data_type,
                        "value": data.value,
                        "unit": data.unit,
                        "timestamp": data.timestamp.isoformat(),
                        "source": data.source
                    }
                    for data in health_data
                ],
                "recent_symptoms": [
                    {
                        "symptom": symptom.symptom,
                        "severity": symptom.severity,
                        "description": symptom.description,
                        "timestamp": symptom.timestamp.isoformat(),
                        "pain_level": symptom.pain_level
                    }
                    for symptom in symptoms
                ],
                "recent_medications": [
                    {
                        "medication": med.medication_name,
                        "dosage": med.dosage,
                        "frequency": med.frequency,
                        "taken_at": med.taken_at.isoformat(),
                        "effectiveness": med.effectiveness
                    }
                    for med in medications
                ],
                "data_summary": {
                    "health_data_points": len(health_data),
                    "symptoms_logged": len(symptoms),
                    "medications_taken": len(medications),
                    "data_types": list(set(data.data_type for data in health_data))
                }
            }
            
            return health_context
            
        except Exception as e:
            logger.error(f"Error getting user health context: {e}")
            return {}
    
    def get_conversation_history(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation history for context"""
        try:
            conversations = self.db.query(Conversation).filter(
                Conversation.user_id == user_id
            ).order_by(desc(Conversation.timestamp)).limit(limit).all()
            
            history = []
            for conv in conversations:
                history.append({
                    "user_message": conv.message,
                    "assistant_response": conv.response,
                    "timestamp": conv.timestamp.isoformat(),
                    "context_used": conv.context_used
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []
    
    def create_enhanced_system_prompt(self, user: User, health_context: Dict[str, Any], conversation_history: List[Dict[str, Any]]) -> str:
        """Create an enhanced system prompt with user context"""
        
        # Get user profile
        user.decrypt_sensitive_fields()
        user_profile = {
            "age": user.age,
            "medical_conditions": user.medical_conditions,
            "medications": user.medications,
            "blood_type": user.blood_type,
            "allergies": user.allergies
        }
        
        # Create health summary
        health_summary = ""
        if health_context.get("recent_health_data"):
            health_summary += f"Recent health data: {len(health_context['recent_health_data'])} data points\n"
        
        if health_context.get("recent_symptoms"):
            health_summary += f"Recent symptoms: {len(health_context['recent_symptoms'])} symptoms logged\n"
        
        if health_context.get("recent_medications"):
            health_summary += f"Recent medications: {len(health_context['recent_medications'])} medications taken\n"
        
        # Create conversation context
        conversation_context = ""
        if conversation_history:
            recent_conversations = conversation_history[:3]  # Last 3 conversations
            conversation_context = "Recent conversation context:\n"
            for conv in recent_conversations:
                conversation_context += f"User: {conv['user_message'][:100]}...\n"
                conversation_context += f"Assistant: {conv['assistant_response'][:100]}...\n\n"
        
        system_prompt = f"""
You are HealthMate, an AI-powered health assistant designed to provide personalized health information and guidance.

USER PROFILE:
- Age: {user_profile.get('age', 'Not specified')}
- Medical Conditions: {user_profile.get('medical_conditions', 'None specified')}
- Current Medications: {user_profile.get('medications', 'None specified')}
- Blood Type: {user_profile.get('blood_type', 'Not specified')}
- Allergies: {user_profile.get('allergies', 'None specified')}

HEALTH CONTEXT:
{health_summary}

{conversation_context}

IMPORTANT GUIDELINES:
1. **Personalization**: Use the user's health profile and recent data to provide personalized responses
2. **Medical Disclaimer**: Always remind users that this is not a substitute for professional medical advice
3. **Emergency Awareness**: Recognize potential emergency situations and advise immediate medical attention
4. **Data Integration**: Reference recent health data when relevant to provide context-aware responses
5. **Privacy**: Never share specific personal health information in responses
6. **Accuracy**: Base responses on reliable medical information and the user's specific context
7. **Encouragement**: Encourage healthy behaviors and regular medical checkups
8. **Limitations**: Acknowledge when a question requires professional medical evaluation

RESPONSE FORMAT:
- Provide clear, concise, and helpful information
- Include relevant health context when appropriate
- Always end with a medical disclaimer
- Suggest follow-up actions when relevant

Remember: Your role is to support and educate, not to diagnose or treat medical conditions.
"""
        
        return system_prompt
    
    def chat_with_health_context(self, user: User, message: str, medical_knowledge_context: str = "") -> Dict[str, Any]:
        """Enhanced chat with comprehensive health context"""
        try:
            # Get user health context
            health_context = self.get_user_health_context(user.id)
            
            # Get conversation history
            conversation_history = self.get_conversation_history(user.id)
            
            # Create enhanced system prompt
            system_prompt = self.create_enhanced_system_prompt(user, health_context, conversation_history)
            
            # Combine medical knowledge with health context
            full_context = f"{medical_knowledge_context}\n\nUser Health Context: {json.dumps(health_context, indent=2)}"
            
            # Get AI response
            response = self.health_agent.chat_with_context(message, full_context, {"user_profile": "enhanced"})
            
            # Handle function calls
            if isinstance(response, dict):
                return {
                    "response": response.get("message", ""),
                    "function_call": True,
                    "function_data": response,
                    "health_context_used": True,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Add health insights if relevant
            enhanced_response = self._add_health_insights(response, health_context, user.id)
            
            return {
                "response": enhanced_response,
                "function_call": False,
                "health_context_used": True,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in enhanced chat: {e}")
            return {
                "response": "I apologize, but I'm having trouble processing your request right now. Please try again or consult a healthcare provider for immediate concerns.",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _add_health_insights(self, response: str, health_context: Dict[str, Any], user_id: int) -> str:
        """Add relevant health insights to the response"""
        try:
            insights = []
            
            # Check for recent severe symptoms
            if health_context.get("recent_symptoms"):
                severe_symptoms = [s for s in health_context["recent_symptoms"] if s.get("severity") == "severe"]
                if severe_symptoms:
                    insights.append("⚠️ I notice you've logged some severe symptoms recently. Please consider consulting a healthcare provider.")
            
            # Check medication adherence
            if health_context.get("recent_medications"):
                unique_meds = len(set(med["medication"] for med in health_context["recent_medications"]))
                if unique_meds > 0:
                    insights.append(f"💊 I see you're tracking {unique_meds} medication(s). Remember to take them as prescribed.")
            
            # Check for data gaps
            if health_context.get("data_summary", {}).get("health_data_points", 0) < 5:
                insights.append("📊 Consider logging more health data to get better personalized insights.")
            
            # Add insights to response if any
            if insights:
                response += "\n\n**Personal Health Insights:**\n" + "\n".join(insights)
            
            return response
            
        except Exception as e:
            logger.error(f"Error adding health insights: {e}")
            return response
    
    def get_chat_suggestions(self, user_id: int) -> List[str]:
        """Get personalized chat suggestions based on user's health data"""
        try:
            suggestions = []
            
            # Get user's recent health data
            health_context = self.get_user_health_context(user_id, days=7)
            
            # Suggest based on data types
            data_types = health_context.get("data_summary", {}).get("data_types", [])
            
            if "blood_pressure" in data_types:
                suggestions.append("How can I improve my blood pressure management?")
            
            if "heart_rate" in data_types:
                suggestions.append("What's a normal heart rate range for my age?")
            
            if "weight" in data_types:
                suggestions.append("How can I maintain a healthy weight?")
            
            # Suggest based on symptoms
            if health_context.get("recent_symptoms"):
                suggestions.append("How can I better manage my symptoms?")
            
            # Suggest based on medications
            if health_context.get("recent_medications"):
                suggestions.append("Are there any lifestyle changes that could help with my medications?")
            
            # General health suggestions
            suggestions.extend([
                "What are some healthy lifestyle tips for my age?",
                "How can I improve my sleep quality?",
                "What exercises are safe for my health condition?",
                "How can I reduce stress and improve mental health?"
            ])
            
            return suggestions[:5]  # Return top 5 suggestions
            
        except Exception as e:
            logger.error(f"Error getting chat suggestions: {e}")
            return [
                "How can I improve my overall health?",
                "What are some healthy lifestyle tips?",
                "How can I better manage stress?"
            ]
    
    def save_conversation(self, user_id: int, message: str, response: str, context_used: str = "") -> int:
        """Save conversation to database and return conversation ID"""
        try:
            conversation = Conversation(
                user_id=user_id,
                message=message,
                response=response,
                context_used=context_used,
                timestamp=datetime.utcnow()
            )
            
            self.db.add(conversation)
            self.db.commit()
            self.db.refresh(conversation)
            
            return conversation.id
            
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
            self.db.rollback()
            return 0 