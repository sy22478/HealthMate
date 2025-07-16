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
            {
                "source": "WHO",
                "title": "World Health Organization Health Topics",
                "content": "WHO health topics, global health standards, and emergency guidance...",
                "url": "https://www.who.int/health-topics"
            },
            {
                "source": "NIH",
                "title": "National Institutes of Health Resources",
                "content": "NIH research, clinical trials, and health information...",
                "url": "https://www.nih.gov/health-information"
            },
            {
                "source": "PubMed",
                "title": "PubMed Medical Literature",
                "content": "PubMed abstracts and peer-reviewed medical research...",
                "url": "https://pubmed.ncbi.nlm.nih.gov/"
            },
            {
                "source": "MedlinePlus",
                "title": "MedlinePlus Patient Information",
                "content": "MedlinePlus patient-friendly health information and drug data...",
                "url": "https://medlineplus.gov/"
            },
            {
                "source": "Cochrane Library",
                "title": "Cochrane Systematic Reviews",
                "content": "Cochrane Library systematic reviews and evidence-based health information...",
                "url": "https://www.cochranelibrary.com/"
            },
            {
                "source": "FDA",
                "title": "U.S. Food & Drug Administration",
                "content": "FDA drug safety, recalls, approvals, and regulatory information...",
                "url": "https://www.fda.gov/"
            },
            {
                "source": "Johns Hopkins Medicine",
                "title": "Johns Hopkins Patient Guides",
                "content": "Johns Hopkins Medicine patient education, guides, and research...",
                "url": "https://www.hopkinsmedicine.org/health/"
            },
            {
                "source": "Cleveland Clinic",
                "title": "Cleveland Clinic Health Library",
                "content": "Cleveland Clinic patient education and health information...",
                "url": "https://my.clevelandclinic.org/health"
            },
            {
                "source": "NLM",
                "title": "National Library of Medicine",
                "content": "NLM biomedical literature, research, and health information...",
                "url": "https://www.nlm.nih.gov/"
            },
            {
                "source": "AHA",
                "title": "American Heart Association",
                "content": "AHA heart disease, stroke, and cardiovascular health information...",
                "url": "https://www.heart.org/"
            },
            {
                "source": "ADA",
                "title": "American Diabetes Association",
                "content": "ADA diabetes care, research, and patient resources...",
                "url": "https://diabetes.org/"
            },
            {
                "source": "NCI",
                "title": "National Cancer Institute",
                "content": "NCI cancer research, treatment, and patient information...",
                "url": "https://www.cancer.gov/"
            },
            # Add more sources as needed
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