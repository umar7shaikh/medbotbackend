import os
import django
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from django.conf import settings

# Set Django settings module correctly
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")  # Update to match your project

# Initialize Django
django.setup()

# Get database connection URL from Django settings
DATABASES = settings.DATABASES["default"]
DB_ENGINE = DATABASES["ENGINE"].split(".")[-1]  # Example: 'postgresql', 'mysql', etc.

DATABASE_URL = f"{DB_ENGINE}://{DATABASES['USER']}:{DATABASES['PASSWORD']}@{DATABASES['HOST']}/{DATABASES['NAME']}"

# Create SQLAlchemy engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
