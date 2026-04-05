#!/usr/bin/env python3

from app import app
from database import db
import sqlite3
import os

def migrate_database():
    """Add is_admin and is_blocked columns to users table"""
    db_path = 'instance/ecomaterial_hub.db'
    
    if not os.path.exists(db_path):
        print("❌ Database file not found!")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print(f"📊 Current columns: {columns}")
        
        # Add is_admin column if it doesn't exist
        if 'is_admin' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0")
            print("✅ Added is_admin column")
        else:
            print("ℹ️  is_admin column already exists")
        
        # Add is_blocked column if it doesn't exist
        if 'is_blocked' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN is_blocked BOOLEAN DEFAULT 0")
            print("✅ Added is_blocked column")
        else:
            print("ℹ️  is_blocked column already exists")
        
        conn.commit()
        conn.close()
        
        print("✅ Database migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration error: {e}")

if __name__ == '__main__':
    print("🚀 Running database migration...")
    migrate_database()
