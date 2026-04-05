#!/usr/bin/env python3
"""
Database migration script to add payment system fields
"""

from database import db, app
from models import User, Payment
from sqlalchemy import text

def migrate_database():
    """Add new fields for payment system"""
    with app.app_context():
        try:
            # Add balance column to users table
            try:
                db.session.execute(text('ALTER TABLE users ADD COLUMN balance NUMERIC(10, 2) DEFAULT 0'))
                db.session.commit()
                print("✓ Added balance column to users table")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print("✓ Balance column already exists in users table")
                else:
                    print(f"✗ Error adding balance column: {e}")
                    db.session.rollback()
            
            # Add telegram_id column to users table
            try:
                db.session.execute(text('ALTER TABLE users ADD COLUMN telegram_id VARCHAR(50)'))
                db.session.commit()
                print("✓ Added telegram_id column to users table")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print("✓ Telegram ID column already exists in users table")
                else:
                    print(f"✗ Error adding telegram_id column: {e}")
                    db.session.rollback()
            
            # Create payments table
            Payment.__table__.create(db.engine, checkfirst=True)
            print("✓ Payments table created/verified")
            
            # Update existing users with 0 balance if they don't have one
            try:
                users_without_balance = db.session.execute(text('SELECT id FROM users WHERE balance IS NULL')).fetchall()
                if users_without_balance:
                    db.session.execute(text('UPDATE users SET balance = 0 WHERE balance IS NULL'))
                    db.session.commit()
                    print(f"✓ Updated {len(users_without_balance)} users with default balance")
            except Exception as e:
                print(f"Note: Could not update user balances: {e}")
            
            print("\n✅ Database migration completed successfully!")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            db.session.rollback()

if __name__ == '__main__':
    migrate_database()
