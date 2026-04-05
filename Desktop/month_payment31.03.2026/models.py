from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from database import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    business_name = db.Column(db.String(200), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='User')  # Admin/User
    phone_number = db.Column(db.String(20))
    telegram_id = db.Column(db.String(50))  # Store Telegram username or ID
    balance = db.Column(db.Numeric(10, 2), default=0)  # User balance in tokens/manat
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)  # Admin flag
    is_blocked = db.Column(db.Boolean, default=False)  # Account blocked status

    
    #Profile photo filename (stored in static/profile_photos/)
    profile_photo = db.Column(db.String(100), nullable=True)

    # Monthly subscription fields (5 manat for 30 days)
    subscription_start = db.Column(db.DateTime)
    subscription_end = db.Column(db.DateTime)
    subscription_active = db.Column(db.Boolean, default=False)
    
    # Trial period fields
    trial_start = db.Column(db.DateTime)
    trial_end = db.Column(db.DateTime)
    has_trial = db.Column(db.Boolean, default=False)
    
    # Relationships
    products = db.relationship('Product', backref='seller', lazy=True)
    reviews = db.relationship('Review', foreign_keys='Review.reviewer_id', backref='reviewer', lazy=True)
    favorites = db.relationship('Favorite', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def start_trial(self, days=30):
        """Start trial period for user"""
        self.trial_start = datetime.utcnow()
        self.trial_end = self.trial_start + timedelta(days=days)
        self.has_trial = True
    
    def is_trial_active(self):
        """Check if user's trial period is active"""
        if not self.has_trial or not self.trial_end:
            return False
        return datetime.utcnow() < self.trial_end
    
    def needs_payment_for_selling(self):
        """Check if user needs to pay to sell products"""
        return not self.is_trial_active()
    
    def needs_payment_for_contacts(self):
        """Check if user needs to pay to view seller contact info"""
        return not self.is_trial_active()
    
    def trial_days_remaining(self):
        """Return days remaining in trial, or 0 if no active trial"""
        if not self.is_trial_active():
            return 0
        remaining = self.trial_end - datetime.utcnow()
        return max(0, remaining.days)
    
    # Monthly subscription methods (5 manat for 30 days)
    def start_subscription(self, days=30):
        """Start monthly subscription for user"""
        self.subscription_start = datetime.utcnow()
        self.subscription_end = self.subscription_start + timedelta(days=days)
        self.subscription_active = True
    
    def is_subscription_active(self):
        """Check if user's monthly subscription is active"""
        if not self.subscription_active or not self.subscription_end:
            return False
        # Auto-close if expired
        if datetime.utcnow() >= self.subscription_end:
            self.subscription_active = False
            return False
        return True
    
    def subscription_days_remaining(self):
        """Return days remaining in subscription, or 0 if no active subscription"""
        if not self.is_subscription_active():
            return 0
        remaining = self.subscription_end - datetime.utcnow()
        return max(0, remaining.days)
    
    def can_access_platform(self):
        """Check if user can access platform (trial OR subscription active)"""
        return self.is_trial_active() or self.is_subscription_active() or self.is_admin
    
    def get_access_status(self):
        """Get user access status for admin panel"""
        if self.is_admin:
            return "Admin"
        if self.is_trial_active():
            return f"Trial ({self.trial_days_remaining()} days)"
        if self.is_subscription_active():
            return f"Active ({self.subscription_days_remaining()} days)"
        return "Expired"
    
    def __repr__(self):
        return f'<User {self.username}>'

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    products = db.relationship('Product', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<Category {self.name}>'

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='Available')  # Available/Sold/Reserved
    photo_filename = db.Column(db.String(255))
    views = db.Column(db.Integer, default=0)  # Number of times product has been viewed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    
    # Relationships
    reviews = db.relationship('Review', backref='product', lazy=True, cascade='all, delete-orphan')
    favorites = db.relationship('Favorite', backref='product', lazy=True, cascade='all, delete-orphan')
    
    # Add timestamp property for compatibility - remove as we now use created_at consistently
    
    def __repr__(self):
        return f'<Product {self.title}>'

class Review(db.Model):
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Unique constraint to prevent duplicate reviews
    __table_args__ = (db.UniqueConstraint('product_id', 'reviewer_id', name='unique_product_review'),)
    
    def __repr__(self):
        return f'<Review {self.rating} stars for Product {self.product_id}>'

class Favorite(db.Model):
    __tablename__ = 'favorites'
    
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    
    # Unique constraint to prevent duplicate favorites
    __table_args__ = (db.UniqueConstraint('user_id', 'product_id', name='unique_user_product_favorite'),)
    
    def __repr__(self):
        return f'<Favorite User {self.user_id} -> Product {self.product_id}>'

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)  # Amount in manat/tokens
    sender_phone = db.Column(db.String(20), nullable=False)  # Phone number that sent the SMS
    transaction_id = db.Column(db.String(100), unique=True, nullable=False)  # Unique transaction ID
    status = db.Column(db.String(20), default='pending')  # pending/completed/failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    
    # Foreign Key
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationship
    user = db.relationship('User', backref='payments')
    
    def __repr__(self):
        return f'<Payment {self.amount} manat from {self.sender_phone}>'
    
class Post(db.Model):
    __tablename__ = 'posts'   # лучше во множественном числе

    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(100))   # можно оставить для удобства
    content = db.Column(db.Text, nullable=False)
    photo_filename = db.Column(db.String(255))   # фото, прикреплённое к посту

    # связь с User
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref='posts', lazy=True)

    # связь с Reply
    replies = db.relationship('Reply', backref='post', lazy=True)


class Reply(db.Model):
    __tablename__ = 'replies'

    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(100), nullable=False)  # можно оставить для удобства
    content = db.Column(db.Text, nullable=False)
    photo_filename = db.Column(db.String(100), nullable=True)  # фото, прикреплённое к ответу

    # связь с Post
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)

    # связь с User
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref='replies', lazy=True)


