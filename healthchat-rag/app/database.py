from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .base import Base

engine = None
SessionLocal = None
try:
    from app.config import settings
    SQLALCHEMY_DATABASE_URL = settings.postgres_uri
    print("[database.py] Using DB URL:", SQLALCHEMY_DATABASE_URL)
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,   # Helps with serverless DBs like Neon
        pool_size=5,          # Small pool size for cloud DB
        max_overflow=2        # Allow a few extra connections
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    print("[database.py] Engine created successfully.")
except Exception as e:
    print("[database.py] Failed to create engine:", e)
    # Alembic or other tools can still import Base
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 