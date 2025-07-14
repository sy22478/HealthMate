import json
from pathlib import Path
from typing import List, Dict

class MedicalKnowledgeBase:
    def __init__(self, vector_store):
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