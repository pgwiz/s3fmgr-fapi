import sys
import os

# This line allows the script to import modules from the parent 'app' directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.crud import crud_user
from app.schemas.user import UserCreate

# --- Configuration for the initial admin user ---
# In a real application, you would load this from a secure config
ADMIN_EMAIL = "admin@epgwiz.uk"
ADMIN_PASSWORD = "1up.2te4dword"

def seed_data():
    """
    Populates the database with initial data.
    """
    print("Starting database seeding...")
    
    # Get a database session
    db = SessionLocal()
    
    try:
        # Check if the admin user already exists
        admin_user = crud_user.get_user_by_email(db, email=ADMIN_EMAIL)
        
        if not admin_user:
            print(f"Admin user not found. Creating user: {ADMIN_EMAIL}")
            
            # Create the user schema object
            user_in = UserCreate(
                email=ADMIN_EMAIL,
                password=ADMIN_PASSWORD,
                role="admin" # Assign the 'admin' role
            )
            
            # Use the CRUD function to create the user
            crud_user.create_user(db=db, user=user_in)
            
            print("Admin user created successfully.")
        else:
            print("Admin user already exists. Skipping.")
            
    except Exception as e:
        print(f"An error occurred during seeding: {e}")
    finally:
        # Always close the session
        db.close()
        print("Seeding process finished.")

if __name__ == "__main__":
    # To run this script, navigate to the root directory of your project
    # (e.g., file-server-api/) in your terminal and execute:
    # python scripts/seed.py
    seed_data()
