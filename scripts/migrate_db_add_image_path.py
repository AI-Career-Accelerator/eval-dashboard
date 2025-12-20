"""
Database migration script to add image_path column to evaluations table.
Run this if you have an existing database before the multi-modal update.
"""
import os
import sys
from sqlalchemy import create_engine, inspect, text

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db import DATABASE_URL, engine

def check_column_exists(table_name, column_name):
    """Check if a column exists in a table."""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def migrate_database():
    """Add image_path column to evaluations table if it doesn't exist."""
    print("[MIGRATION] Checking database schema...")

    try:
        # Check if image_path column exists
        if check_column_exists('evaluations', 'image_path'):
            print("[OK] image_path column already exists. No migration needed.")
            return

        print("[MIGRATION] Adding image_path column to evaluations table...")

        # Add the column
        with engine.connect() as conn:
            # SQLite syntax for adding a column
            if 'sqlite' in DATABASE_URL:
                conn.execute(text('ALTER TABLE evaluations ADD COLUMN image_path VARCHAR(500)'))
            # PostgreSQL syntax
            elif 'postgresql' in DATABASE_URL:
                conn.execute(text('ALTER TABLE evaluations ADD COLUMN image_path VARCHAR(500)'))
            else:
                print("[ERROR] Unsupported database type")
                return

            conn.commit()

        print("[OK] Migration completed successfully!")
        print("[INFO] The evaluations table now has an image_path column.")

    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        print("[INFO] If you see 'duplicate column name' error, the column already exists.")
        return

if __name__ == "__main__":
    print("\n" + "="*60)
    print("DATABASE MIGRATION: Add image_path column")
    print("="*60 + "\n")

    print(f"Database URL: {DATABASE_URL}\n")

    migrate_database()

    print("\n" + "="*60)
    print("Migration process complete")
    print("="*60 + "\n")
