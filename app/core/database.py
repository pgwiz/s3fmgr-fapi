from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from app.core.config import settings

# Create the SQLAlchemy engine
# The pool_pre_ping argument will check for "stale" connections and reconnect if necessary.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True
)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class for our models to inherit from
Base = declarative_base()

# Dependency to get a DB session
# This will be used in API endpoints to get a database session.
# It ensures that the session is always closed after the request is finished.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()