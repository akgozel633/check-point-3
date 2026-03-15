import sqlite3

def update_database():
    conn = sqlite3.connect('recipes.db')
    cursor = conn.cursor()
    
    # Check if owner_id column exists
    cursor.execute('PRAGMA table_info(recipes)')
    columns = [row[1] for row in cursor.fetchall()]
    print('Current columns:', columns)
    
    if 'owner_id' not in columns:
        print('Adding owner_id column...')
        cursor.execute('ALTER TABLE recipes ADD COLUMN owner_id INTEGER')
        conn.commit()
        print('owner_id column added successfully!')
    else:
        print('owner_id column already exists')
    
    conn.close()

if __name__ == '__main__':
    update_database()
