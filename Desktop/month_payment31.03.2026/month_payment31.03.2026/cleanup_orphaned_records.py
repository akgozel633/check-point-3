#!/usr/bin/env python3

from app import app
from models import User, Favorite, Review, Product, Payment
from database import db

def cleanup_orphaned_records():
    """Clean up orphaned records in the database"""
    with app.app_context():
        print("🧹 Cleaning Up Orphaned Records")
        print("=" * 50)
        
        try:
            # Find orphaned payments (where user_id doesn't exist)
            orphaned_payments = db.session.query(Payment).outerjoin(User, Payment.user_id == User.id).filter(User.id.is_(None)).all()
            print(f"📊 Found {len(orphaned_payments)} orphaned payments")
            
            # Delete orphaned payments
            for payment in orphaned_payments:
                db.session.delete(payment)
            
            # Find orphaned favorites (where user_id doesn't exist)
            orphaned_favorites = db.session.query(Favorite).outerjoin(User, Favorite.user_id == User.id).filter(User.id.is_(None)).all()
            print(f"📊 Found {len(orphaned_favorites)} orphaned favorites")
            
            # Delete orphaned favorites
            for fav in orphaned_favorites:
                db.session.delete(fav)
            
            # Find orphaned reviews (where reviewer_id doesn't exist)
            orphaned_reviews = db.session.query(Review).outerjoin(User, Review.reviewer_id == User.id).filter(User.id.is_(None)).all()
            print(f"📊 Found {len(orphaned_reviews)} orphaned reviews")
            
            # Delete orphaned reviews
            for review in orphaned_reviews:
                db.session.delete(review)
            
            # Find products with non-existent sellers
            orphaned_products = db.session.query(Product).outerjoin(User, Product.seller_id == User.id).filter(User.id.is_(None)).all()
            print(f"📊 Found {len(orphaned_products)} orphaned products")
            
            # Delete orphaned products
            for product in orphaned_products:
                db.session.delete(product)
            
            # Commit changes
            db.session.commit()
            print("✅ Cleanup completed successfully!")
            
            # Show remaining counts
            print(f"\n📈 Remaining Records:")
            print(f"   Users: {User.query.count()}")
            print(f"   Products: {Product.query.count()}")
            print(f"   Payments: {Payment.query.count()}")
            print(f"   Favorites: {Favorite.query.count()}")
            print(f"   Reviews: {Review.query.count()}")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Cleanup error: {e}")

if __name__ == '__main__':
    cleanup_orphaned_records()
