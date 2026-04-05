"""
Migration script to add subscription fields to User model
Run this script to add the new subscription columns to your database

Usage:
    python migrate_subscription.py
"""

import os
import sys

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from sqlalchemy import text

def migrate_subscription_fields():
    """Add subscription fields to users table"""
    with app.app_context():
        print("Starting migration...")
        
        # Check if columns already exist
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('users')]
        
        new_columns = []
        
        if 'subscription_start' not in columns:
            new_columns.append("ALTER TABLE users ADD COLUMN subscription_start DATETIME")
        if 'subscription_end' not in columns:
            new_columns.append("ALTER TABLE users ADD COLUMN subscription_end DATETIME")
        if 'subscription_active' not in columns:
            new_columns.append("ALTER TABLE users ADD COLUMN subscription_active BOOLEAN DEFAULT 0")
        
        if not new_columns:
            print("All subscription columns already exist. No migration needed.")
            return
        
        # Execute migrations
        for sql in new_columns:
            try:
                print(f"Executing: {sql}")
                db.session.execute(text(sql))
            except Exception as e:
                print(f"Warning: {e}")
                continue
        
        db.session.commit()
        print("Migration completed successfully!")
        print("\nNew columns added:")
        print("  - subscription_start: DateTime")
        print("  - subscription_end: DateTime")
        print("  - subscription_active: Boolean (default: False)")

if __name__ == '__main__':
    migrate_subscription_fields()
