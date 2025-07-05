
import sys
import os


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine, Base

from app.models import user, folder, file, upload_session, permission # Make sure to import all models to register them with SQLAlchemy


def create_tables():
    print("Starting database migration...")
    try:
        print("Dropping all existing tables (for development purposes)...")
        Base.metadata.drop_all(bind=engine)
        print("Creating all tables...")
        Base.metadata.create_all(bind=engine)
        
        print("Tables created successfully!")
    except Exception as e:
        print(f"An error occurred during table creation: {e}")

if __name__ == "__main__":
    create_tables()
