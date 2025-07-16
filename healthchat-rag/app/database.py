from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .base import Base

try:
    from app.config import settings
    SQLALCHEMY_DATABASE_URL = settings.postgres_uri
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,   # Helps with serverless DBs like Neon
        pool_size=5,          # Small pool size for cloud DB
        max_overflow=2        # Allow a few extra connections
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except ImportError:
    # Alembic or other tools can still import Base
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 