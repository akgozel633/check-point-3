from database import db, app
from models import Category

def add_new_categories():
    """Add new categories to existing database"""
    with app.app_context():
        # Get existing category names
        existing_categories = {cat.name for cat in Category.query.all()}
        
        # New categories to add
        new_categories = [
            ('Glass', 'Glass materials and products'),
            ('Paper', 'Paper and cardboard products'),
            ('Textiles', 'Fabrics and textile materials'),
            ('Rubber', 'Rubber products and materials'),
            ('Chemicals', 'Industrial chemicals and solvents'),
            ('Machinery', 'Industrial machinery and equipment'),
            ('Tools', 'Hand and power tools'),
            ('Energy', 'Energy equipment and renewable energy'),
            ('Waste Management', 'Recycling and waste disposal equipment'),
            ('Packaging', 'Packaging materials and containers'),
            ('Automotive', 'Automotive parts and materials'),
            ('Agriculture', 'Agricultural equipment and supplies'),
            ('Medical', 'Medical equipment and supplies'),
            ('Food Processing', 'Food processing equipment'),
            ('Marine', 'Marine equipment and materials'),
            ('Aerospace', 'Materials and components for aerospace industry'),
            ('Biotechnology', 'Biologically derived materials and processes'),
            ('Ceramics', 'Ceramic materials and products'),
            ('Composites', 'Advanced composite materials'),
            ('Nanomaterials', 'Materials at the nanoscale'),
            ('Optics', 'Optical materials and components'),
            ('Polymers', 'Synthetic and natural polymers'),
            ('Semiconductors', 'Materials for semiconductor devices'),
            ('Sporting Goods', 'Materials for sports equipment'),
            ('Jewelry', 'Precious metals and gemstones'),
            ('Cosmetics', 'Ingredients for cosmetic products'),
            ('Cleaning Supplies', 'Chemicals and materials for cleaning'),
            ('Adhesives', 'Bonding agents and sealants'),
            ('Paints & Coatings', 'Protective and decorative coatings')
        ]
        
        added_count = 0
        for name, description in new_categories:
            if name not in existing_categories:
                category = Category(name=name, description=description)
                db.session.add(category)
                added_count += 1
                print(f"Added category: {name}")
            else:
                print(f"Category already exists: {name}")
        
        if added_count > 0:
            db.session.commit()
            print(f"\nSuccessfully added {added_count} new categories!")
        else:
            print("\nNo new categories to add.")
        
        # Show total categories
        total_categories = Category.query.count()
        print(f"Total categories in database: {total_categories}")

if __name__ == '__main__':
    add_new_categories()
