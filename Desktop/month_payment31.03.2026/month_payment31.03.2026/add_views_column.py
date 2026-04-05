from database import db, app
from models import Product

def add_views_column():
    """Add views column to existing products"""
    with app.app_context():
        # Update all existing products to have views = 0 if they don't have it already
        products = Product.query.all()
        updated_count = 0
        
        for product in products:
            # Check if views attribute exists and is None
            if not hasattr(product, 'views') or product.views is None:
                product.views = 0
                updated_count += 1
        
        if updated_count > 0:
            db.session.commit()
            print(f"Updated {updated_count} products with views column")
        else:
            print("All products already have views column")
        
        print(f"Total products: {len(products)}")
        
        # Show some sample products with their view counts
        print("\nSample products:")
        for i, product in enumerate(products[:5]):
            print(f"{i+1}. {product.title}: {product.views} views")

if __name__ == '__main__':
    add_views_column()
