from database import db
from models import User, Product, Category, Review, Favorite
from werkzeug.security import generate_password_hash
from app import app

def init_database():
    """Initialize the database with sample data"""
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if data already exists
        if Category.query.first():
            print("Database already initialized")
            return
        
        # Create categories
        categories = [
            Category(name='Metals', description='Ferrous and non-ferrous metals'),
            Category(name='Wood', description='Timber and wood products'),
            Category(name='Plastics', description='Recycled and virgin plastics'),
            Category(name='Construction', description='Building materials'),
            Category(name='Electronics', description='Electronic components and devices'),
            Category(name='Glass', description='Glass materials and products'),
            Category(name='Paper', description='Paper and cardboard products'),
            Category(name='Textiles', description='Fabrics and textile materials'),
            Category(name='Rubber', description='Rubber products and materials'),
            Category(name='Chemicals', description='Industrial chemicals and solvents'),
            Category(name='Machinery', description='Industrial machinery and equipment'),
            Category(name='Tools', description='Hand and power tools'),
            Category(name='Energy', description='Energy equipment and renewable energy'),
            Category(name='Waste Management', description='Recycling and waste disposal equipment'),
            Category(name='Packaging', description='Packaging materials and containers'),
            Category(name='Automotive', description='Automotive parts and materials'),
            Category(name='Agriculture', description='Agricultural equipment and supplies'),
            Category(name='Medical', description='Medical equipment and supplies'),
            Category(name='Food Processing', description='Food processing equipment'),
            Category(name='Marine', description='Marine equipment and materials'),
            Category(name='Aerospace', description='Materials and components for aerospace industry'),
            Category(name='Biotechnology', description='Biologically derived materials and processes'),
            Category(name='Ceramics', description='Ceramic materials and products'),
            Category(name='Composites', description='Advanced composite materials'),
            Category(name='Nanomaterials', description='Materials at the nanoscale'),
            Category(name='Optics', description='Optical materials and components'),
            Category(name='Polymers', description='Synthetic and natural polymers'),
            Category(name='Semiconductors', description='Materials for semiconductor devices'),
            Category(name='Sporting Goods', description='Materials for sports equipment'),
            Category(name='Jewelry', description='Precious metals and gemstones'),
            Category(name='Cosmetics', description='Ingredients for cosmetic products'),
            Category(name='Cleaning Supplies', description='Chemicals and materials for cleaning'),
            Category(name='Adhesives', description='Bonding agents and sealants'),
            Category(name='Paints & Coatings', description='Protective and decorative coatings')
        ]
        
        for category in categories:
            db.session.add(category)
        
        # Create admin user
        admin = User(
            business_name='EcoMaterial Admin',
            username='admin',
            email='admin@ecomaterial.com',
            phone_number='+1234567890',
            role='Admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        
        # Create test users
        users = [
            User(
                business_name='Green Building Supplies',
                username='greensupply',
                email='green@supply.com',
                phone_number='+1234567891',
                role='User'
            ),
            User(
                business_name='Recycled Materials Co',
                username='recycler',
                email='recycle@materials.com',
                phone_number='+1234567892',
                role='User'
            ),
            User(
                business_name='Sustainable Solutions',
                username='sustain',
                email='sustain@solutions.com',
                phone_number='+1234567893',
                role='User'
            )
        ]
        
        for user in users:
            user.set_password('password123')
            db.session.add(user)
        
        db.session.commit()
        
        # Create sample products
        products = [
            Product(
                title='Recycled Steel Beams',
                description='High-quality recycled steel beams perfect for construction projects. Environmentally friendly and cost-effective.',
                price=450.00,
                quantity=25,
                seller_id=2,
                category_id=1
            ),
            Product(
                title='FSC-Certified Wood Planks',
                description='Sustainably sourced wood planks from managed forests. Ideal for eco-friendly building projects.',
                price=85.50,
                quantity=100,
                seller_id=2,
                category_id=2
            ),
            Product(
                title='Recycled Plastic Sheets',
                description='Environmentally friendly plastic sheets that decompose naturally. Great for packaging and construction.',
                price=32.75,
                quantity=200,
                seller_id=3,
                category_id=3
            ),
            Product(
                title='Durable Metal Frame',
                description='Durable metal frame for construction projects. Made from recycled materials.',
                price=125.00,
                quantity=50,
                seller_id=3,
                category_id=4
            ),
            Product(
                title='Solar Panel Components',
                description='High-efficiency solar panel components for renewable energy projects.',
                price=280.00,
                quantity=30,
                seller_id=4,
                category_id=5
            )
        ]
        
        for product in products:
            db.session.add(product)
        
        db.session.commit()
        
        # Create sample reviews
        reviews = [
            Review(
                rating=5,
                comment='Excellent quality! Exactly what I needed for my project.',
                product_id=1,
                reviewer_id=3
            ),
            Review(
                rating=4,
                comment='Good product, fair price. Would recommend.',
                product_id=2,
                reviewer_id=4
            ),
            Review(
                rating=5,
                comment='Perfect for our sustainable building initiative.',
                product_id=3,
                reviewer_id=2
            )
        ]
        
        for review in reviews:
            db.session.add(review)
        
        db.session.commit()
        
        print("Database initialized successfully!")
        print("Admin user: admin@ecomaterial.com / admin123")
        print("Test users: greensupply@supply.com / password123")
        print("             recycle@materials.com / password123")
        print("             sustain@solutions.com / password123")

if __name__ == '__main__':
    init_database()
