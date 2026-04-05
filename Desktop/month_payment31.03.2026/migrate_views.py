from database import db, app

def add_views_column():
    """Add views column to products table"""
    with app.app_context():
        # Add the views column to the products table
        try:
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE products ADD COLUMN views INTEGER DEFAULT 0"))
                conn.commit()
            print("Successfully added views column to products table")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("Views column already exists")
            else:
                print(f"Error adding views column: {e}")
        
        # Verify the column was added
        try:
            with db.engine.connect() as conn:
                result = conn.execute(db.text("PRAGMA table_info(products)"))
                columns = [row[1] for row in result]
            
            if 'views' in columns:
                print("✅ Views column exists in products table")
            else:
                print("❌ Views column not found in products table")
        except Exception as e:
            print(f"Error checking table structure: {e}")

if __name__ == '__main__':
    add_views_column()
