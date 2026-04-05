from database import db, app
from models import Product

def test_view_counting():
    """Test view counting functionality"""
    with app.app_context():
        products = Product.query.all()
        print("Current view counts:")
        for product in products:
            print(f"{product.title}: {product.views} views")
        
        # Simulate viewing a product
        if products:
            product = products[0]
            print(f"\nSimulating view of: {product.title}")
            print(f"Before: {product.views} views")
            
            # Increment views (same as in product_detail route)
            product.views += 1
            db.session.commit()
            
            print(f"After: {product.views} views")

if __name__ == '__main__':
    test_view_counting()
