from database import db, app
from models import Category

def test_categories():
    """Test if categories are loaded correctly"""
    with app.app_context():
        categories = Category.query.all()
        print(f"Total categories in database: {len(categories)}")
        print("\nCategories list:")
        for i, category in enumerate(categories, 1):
            print(f"{i}. {category.name} - {category.description}")

if __name__ == '__main__':
    test_categories()
