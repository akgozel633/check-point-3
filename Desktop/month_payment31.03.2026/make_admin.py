from app import app
from models import User
from database import db

with app.app_context():
    # Find existing administrator user
    admin = User.query.filter_by(username='administrator').first()
    
    if admin:
        print(f"✅ Found user: {admin.username} ({admin.email})")
        admin.is_admin = True
        admin.balance = 999999.99
        db.session.commit()
        print(f"✅ Updated {admin.username} to admin status")
        print(f"   Email: {admin.email}")
        print(f"   Admin: {admin.is_admin}")
        print(f"   Balance: {admin.balance}")
    else:
        print("❌ No 'administrator' user found")
        
        # Try to find admin@gmail.com user
        admin = User.query.filter_by(email='admin@gmail.com').first()
        if admin:
            print(f"✅ Found admin@gmail.com user: {admin.username}")
            admin.is_admin = True
            admin.balance = 999999.99
            db.session.commit()
            print(f"✅ Updated {admin.username} to admin status")
        else:
            print("❌ No admin user found to update")
