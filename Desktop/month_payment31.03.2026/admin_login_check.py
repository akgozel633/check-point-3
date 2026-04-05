#!/usr/bin/env python3

from app import app
from models import User
from database import db
from flask_login import login_user

def check_admin_login():
    """Check admin login credentials"""
    with app.app_context():
        print("🔐 Admin Login Check")
        print("=" * 40)
        
        # Find admin user
        admin = User.query.filter_by(is_admin=True).first()
        if not admin:
            print("❌ No admin user found!")
            return
        
        print(f"👑 Admin User Found:")
        print(f"   Username: {admin.username}")
        print(f"   Email: {admin.email}")
        print(f"   Is Admin: {admin.is_admin}")
        print(f"   Is Blocked: {admin.is_blocked}")
        
        # Test password check
        print(f"\n🔑 Login Credentials:")
        print(f"   Email: {admin.email}")
        print(f"   Password: 1q2w3e4rQ!")
        
        # Verify password works
        if admin.check_password("1q2w3e4rQ!"):
            print("✅ Admin password verification works!")
        else:
            print("❌ Admin password verification failed!")
        
        print(f"\n🌐 Access Instructions:")
        print(f"1. Go to: http://localhost:5000/login")
        print(f"2. Email: {admin.email}")
        print(f"3. Password: 1q2w3e4rQ!")
        print(f"4. Click 'Admin Panel' in navigation")
        print(f"5. Or go directly to: http://localhost:5000/admin/users")
        
        print(f"\n🎯 Admin Features Available:")
        print(f"✅ View all users")
        print(f"✅ Update user balances")
        print(f"✅ Block/unblock users")
        print(f"✅ Delete non-admin users")
        print(f"✅ See user statistics")

if __name__ == '__main__':
    check_admin_login()
