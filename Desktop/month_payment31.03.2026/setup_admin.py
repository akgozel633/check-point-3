#!/usr/bin/env python3

from app import app
from models import User
from database import db
from werkzeug.security import generate_password_hash

def create_admin_user():
    """Create admin user if it doesn't exist"""
    with app.app_context():
        # Check if admin user already exists
        admin = User.query.filter_by(email='admin@ecomaterialhub.com').first()
        
        if admin:
            print("✅ Admin user already exists:")
            print(f"   Username: {admin.username}")
            print(f"   Email: {admin.email}")
            print(f"   Admin: {admin.is_admin}")
            return admin
        
        # Create new admin user
        admin = User(
            username='administrator',
            email='admin@ecomaterialhub.com',
            business_name='EcoMaterial Hub Administration',
            phone_number='',
            is_admin=True,
            balance=999999.99  # Unlimited balance for admin
        )
        admin.set_password('Admin123!@#')
        
        db.session.add(admin)
        db.session.commit()
        
        print("✅ Admin user created successfully:")
        print(f"   Username: administrator")
        print(f"   Email: admin@ecomaterialhub.com")
        print(f"   Password: Admin123!@#")
        print(f"   Admin: {admin.is_admin}")
        print(f"   Balance: {admin.balance}")
        
        return admin

def update_existing_admin():
    """Update existing user to be admin if they have admin role"""
    with app.app_context():
        # Find users with 'Admin' role and update is_admin flag
        admin_role_users = User.query.filter_by(role='Admin').all()
        
        for user in admin_role_users:
            if not user.is_admin:
                user.is_admin = True
                print(f"✅ Updated {user.username} to admin status")
        
        db.session.commit()
        
        if admin_role_users:
            print(f"✅ Updated {len(admin_role_users)} users to admin status")
        else:
            print("ℹ️  No users with 'Admin' role found")

if __name__ == '__main__':
    print("🚀 Setting up admin user...")
    create_admin_user()
    update_existing_admin()
    print("✅ Admin setup complete!")
