from app import app
from models import User

with app.app_context():
    users = User.query.all()
    print("📊 Existing users:")
    for user in users:
        print(f"  - {user.username} ({user.email}) - Admin: {user.is_admin}")
    
    # Find existing admin
    admin = User.query.filter_by(email='admin@ecomaterialhub.com').first()
    if admin:
        print(f"\n✅ Admin user found: {admin.username}")
        admin.is_admin = True
        from database import db
        db.session.commit()
        print(f"✅ Updated {admin.username} to admin status")
    else:
        print("\n❌ No admin@ecomaterialhub.com user found")
