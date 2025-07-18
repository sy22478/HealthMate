from dotenv import load_dotenv
import os
load_dotenv(dotenv_path="/Users/sonuyadav/HealthMate/healthchat-rag/.env")
# Debug print to check environment variables
print("openai_api_key:", os.environ.get("openai_api_key"))
print("pinecone_api_key:", os.environ.get("pinecone_api_key"))
print("pinecone_environment:", os.environ.get("pinecone_environment"))
print("pinecone_index_name:", os.environ.get("pinecone_index_name"))
print("postgres_uri:", os.environ.get("postgres_uri"))
print("secret_key:", os.environ.get("secret_key"))
from app.database import engine
from app.models.user import Base

# Create all tables
Base.metadata.create_all(bind=engine)
print("Tables created successfully.")
