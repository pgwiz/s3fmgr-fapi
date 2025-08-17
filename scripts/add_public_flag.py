
import sys
import os
from sqlalchemy import text

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine

def add_is_public_column():
    """
    Adds the is_public column to the files table if it doesn't exist.
    This is a non-destructive operation.
    """
    print("Starting database schema update...")
    
    # SQL command to add the column only if it does not exist
    # This is safe to run multiple times.
    alter_command = text("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'files' AND column_name = 'is_public'
        ) THEN
            ALTER TABLE files ADD COLUMN is_public BOOLEAN NOT NULL DEFAULT FALSE;
            RAISE NOTICE 'Column is_public added to files table.';
        ELSE
            RAISE NOTICE 'Column is_public already exists in files table.';
        END IF;
    END $$;
    """)

    try:
        with engine.connect() as connection:
            connection.execute(alter_command)
            connection.commit()
        print("Schema update check completed successfully.")
    except Exception as e:
        print(f"An error occurred during schema update: {e}")

if __name__ == "__main__":
    # To run this script, navigate to the project root and execute:
    # python scripts/add_public_flag.py
