from app.database import engine
from app.models.user import Base

# Create all tables
Base.metadata.create_all(bind=engine)
print("Tables created successfully.")
