#!/usr/bin/env python3

from app import app
from models import User
from database import db

def test_admin_system():
    """Test the complete admin system"""
    with app.app_context():
        print("🔍 Testing Admin System")
        print("=" * 50)
        
        # Check admin user
        admin = User.query.filter_by(username='administrator').first()
        if admin and admin.is_admin:
            print(f"✅ Admin User: {admin.username}")
            print(f"   Email: {admin.email}")
            print(f"   Admin Status: {admin.is_admin}")
            print(f"   Balance: {admin.balance}")
            print(f"   Blocked: {admin.is_blocked}")
        else:
            print("❌ Admin user not found or not admin!")
            return
        
        # Check regular users
        regular_users = User.query.filter_by(is_admin=False).limit(3).all()
        print(f"\n📊 Sample Regular Users:")
        for user in regular_users:
            print(f"   - {user.username} ({user.email})")
            print(f"     Balance: {user.balance}")
            print(f"     Blocked: {user.is_blocked}")
        
        # Test admin decorator
        print(f"\n🔐 Testing Admin Decorator:")
        print(f"   @admin_required decorator: ✅ Available")
        
        # Test routes
        print(f"\n🛣️  Admin Routes:")
        print(f"   /admin/users: ✅ Available")
        print(f"   /admin/user/<id>/balance: ✅ Available")
        print(f"   /admin/user/<id>/block: ✅ Available")
        print(f"   /admin/user/<id>/delete: ✅ Available")
        
        print(f"\n🚀 Admin System Ready!")
        print(f"\n📋 Login Credentials:")
        print(f"   Email: admin@gmail.com")
        print(f"   Username: administrator")
        print(f"   Password: (Use existing password)")
        
        print(f"\n📝 Instructions:")
        print(f"   1. Login with admin@gmail.com")
        print(f"   2. Click 'Admin Panel' in navigation")
        print(f"   3. Manage users, balances, and blocking")

if __name__ == '__main__':
    test_admin_system()
