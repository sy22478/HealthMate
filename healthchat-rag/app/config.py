from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    pinecone_api_key: str
    pinecone_environment: str
    pinecone_index_name: str
    postgres_uri: str
    secret_key: str
    encryption_key: str

    class Config:
        env_file = ".env"

settings = Settings() 