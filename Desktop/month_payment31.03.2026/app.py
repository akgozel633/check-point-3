from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm, CSRFProtect
from flask_migrate import Migrate
import requests
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timezone
import os
import uuid
import logging
from flask import jsonify
import requests
import random
from rapidfuzz import fuzz
from functools import wraps
from dotenv import load_dotenv
import time






from database import db
from models import User, Product, Category, Review, Favorite, Payment, Post, Reply
from forms import LoginForm, RegistrationForm, ProductForm, ReviewForm, SearchForm, ProfileForm, ForumForm, EditPostForm, EditReplyForm, ReplyForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired

load_dotenv()

app = Flask(__name__)

# Конфигурация
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///ecomaterial_hub.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Папка для загрузок
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])


# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'
# Initialize CSRF protection
csrf = CSRFProtect(app)

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# Subscription required decorator
def subscription_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        # Admins always have access
        if current_user.is_admin:
            return f(*args, **kwargs)
        # Check if user has active trial or subscription
        if not current_user.can_access_platform():
            flash('Your subscription has expired. Please pay 5 manat to continue using the platform for 30 days.', 'warning')
            return redirect(url_for('subscription_expired'))
        return f(*args, **kwargs)
    return decorated_function

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Routes
@app.route('/', methods=['GET', 'POST'])
def home():
    """Home page with search functionality"""
    form = SearchForm()
    
    # Load categories for search dropdown
    try:
        categories = Category.query.all()
        form.category.choices = [(0, 'All Categories')]
        if current_user.is_authenticated:
            form.category.choices.append((-1, '❤️ My Favorites'))
        form.category.choices += [(c.id, c.name) for c in categories]
    except Exception as e:
        logger.error(f"Error loading home page categories: {e}")
        categories = []
        form.category.choices = [(0, 'All Categories')]
    
    # Handle search on home page
    products = []
    search_performed = False
    
    if request.method == 'POST' and form.validate_on_submit():
        query = form.query.data.strip() if form.query.data else ''
        category_id = form.category.data
        search_performed = True
        
        logger.info(f"Home search query: '{query}', category_id: {category_id}")
        
        # Handle favorites category
        if category_id == -1:  # Favorites category
            if current_user.is_authenticated:
                favorite_product_ids = [f.product_id for f in Favorite.query.filter_by(user_id=current_user.id).all()]
                products = Product.query.filter(Product.id.in_(favorite_product_ids)).order_by(Product.created_at.desc()).all()
            else:
                products = []
        else:
            # Regular search
            product_query = Product.query.filter_by(status='Available')
            
            if category_id and category_id != 0:
                product_query = product_query.filter_by(category_id=category_id)
            
            if query:
                product_query = product_query.filter(
                    Product.title.contains(query) | 
                    Product.description.contains(query)
                )
            
            products = product_query.order_by(Product.created_at.desc()).all()
            logger.info(f"Home search found {len(products)} products")
    else:
        # Show featured products when no search is performed
        try:
            products = Product.query.filter_by(status='Available').order_by(Product.created_at.desc()).limit(6).all()
        except Exception as e:
            logger.error(f"Error loading featured products: {e}")
            products = []
    
    return render_template('home.html', products=products, categories=categories, form=form, search_performed=search_performed)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            # Check if user is blocked
            if user.is_blocked:
                flash('Your account has been blocked. Please contact support.', 'error')
                return render_template('login.html', form=form)
            
            login_user(user)
            # flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html', form=form)


@app.route('/subscription-expired')
@login_required
def subscription_expired():
    """Page shown when subscription expires"""
    # If user has access (trial or subscription), redirect home
    if current_user.can_access_platform():
        return redirect(url_for('home'))
    
    return render_template('subscription_expired.html',
                         subscription_days=current_user.subscription_days_remaining(),
                         trial_days=current_user.trial_days_remaining())

@app.route('/payment-instructions')
@login_required
def payment_instructions():
    """Show payment instructions for subscription"""
    return render_template('payment_instructions.html',
                         subscription_days=current_user.subscription_days_remaining(),
                         trial_days=current_user.trial_days_remaining())

# @app.route("/eco-data")
# def eco_data():
#     page = int(request.args.get("page", 0))
#     limit = 12

#     animals_with_photos = []
#     tries = 0

#     # Пробуем до 10 раз, пока не найдём фото
#     while not animals_with_photos and tries < 10:
#         offset = random.randint(0, 20000)
#         url = f"https://api.gbif.org/v1/occurrence/search?kingdom=Animalia&limit={limit}&offset={offset}"
#         response = requests.get(url)
#         results = response.json().get("results", [])

#         animals_with_photos = [
#             item for item in results
#             if item.get("class") != "Insecta"
#             and item.get("media")
#             and any(m.get("identifier") for m in item["media"])
#         ]
#         tries += 1

#     return render_template("eco_data.html", data=animals_with_photos, page=page)




@app.route("/forum", methods=["GET", "POST"])
@login_required
def forum():
    post_form = ForumForm()
    reply_form = ReplyForm()

    # обработка создания поста
    if post_form.validate_on_submit():
        filename = None
        if post_form.photo.data:
            filename = secure_filename(post_form.photo.data.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            post_form.photo.data.save(filepath)

        new_post = Post(
            user_id=current_user.id,          # сохраняем ID пользователя
            author=current_user.username,     # можно оставить для удобства
            content=post_form.content.data,
            photo_filename=filename
        )
        db.session.add(new_post)
        db.session.commit()
        flash("Post created successfully!", "success")
        return redirect(url_for("forum"))

    # подтягиваем посты вместе с пользователями
    posts = Post.query.order_by(Post.id.desc()).all()

    return render_template(
        "forum.html",
        posts=posts,
        post_form=post_form,
        reply_form=reply_form
    )


@app.route("/reply/<int:post_id>", methods=["POST"])
@login_required
def reply(post_id):
    form = ReplyForm()
    if form.validate_on_submit():
        filename = None
        if form.photo.data:
            filename = secure_filename(form.photo.data.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            form.photo.data.save(filepath)

        new_reply = Reply(
            author=current_user.username,
            content=form.content.data,
            photo_filename=filename,
            post_id=post_id,
            user_id=current_user.id   # обязательно сохраняем ID пользователя
        )
        db.session.add(new_reply)
        db.session.commit()
        flash("Reply added successfully!", "success")
    return redirect(url_for("forum"))




@app.route("/edit_reply/<int:reply_id>", methods=["GET", "POST"])
@login_required
def edit_reply(reply_id):
    reply = Reply.query.get_or_404(reply_id)
    if reply.author != current_user.username:
        flash("You can only edit your own replies.", "error")
        return redirect(url_for("forum"))

    form = EditReplyForm(obj=reply)
    if form.validate_on_submit():
        reply.content = form.content.data

        if form.photo.data:  # заменить фото
            filename = secure_filename(form.photo.data.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            form.photo.data.save(filepath)
            reply.photo_filename = filename
        elif form.remove_photo.data:  # удалить фото
            reply.photo_filename = None

        db.session.commit()
        flash("Reply updated successfully!", "success")
        return redirect(url_for("forum"))

    return render_template("edit_reply.html", form=form, reply=reply)


    form = EditReplyForm(obj=reply)
    if form.validate_on_submit():
        reply.content = form.content.data
        db.session.commit()
        flash("Reply updated successfully!", "success")
        return redirect(url_for("forum"))

    return render_template("edit_reply.html", form=form, reply=reply)

@app.route("/delete_reply/<int:reply_id>", methods=["POST"])
@login_required
def delete_reply(reply_id):
    reply = Reply.query.get_or_404(reply_id)
    if reply.author == current_user.username:  # только автор может удалить
        db.session.delete(reply)
        db.session.commit()
        flash("Reply deleted successfully!", "success")
    else:
        flash("You can only delete your own replies.", "error")
    return redirect(url_for("forum"))

@app.route("/delete_post/<int:post_id>", methods=["POST"])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    # Проверяем, что автор поста совпадает с текущим пользователем
    if post.author == current_user.username:
        # Сначала удаляем все ответы к посту
        for reply in post.replies:
            db.session.delete(reply)
        db.session.delete(post)
        db.session.commit()
        flash("Post deleted successfully!", "success")
    else:
        flash("You can only delete your own posts.", "error")
    return redirect(url_for("forum"))

@app.route("/edit_post/<int:post_id>", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user.username:
        flash("You can only edit your own posts.", "error")
        return redirect(url_for("forum"))

    form = EditPostForm(obj=post)
    if form.validate_on_submit():
        post.content = form.content.data

        # Если пользователь загрузил новое фото
        if form.photo.data:
            filename = secure_filename(form.photo.data.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            form.photo.data.save(filepath)
            post.photo_filename = filename

        # Если пользователь отметил "Удалить фото"
        elif form.remove_photo.data:
            post.photo_filename = None

        db.session.commit()
        flash("Post updated successfully!", "success")
        return redirect(url_for("forum"))

    return render_template("edit_post.html", form=form, post=post)

@app.route("/update_profile_photo", methods=["POST"])
@login_required
def update_profile_photo():
    if 'photo' in request.files:
        file = request.files['photo']
        if file.filename != '':
            # генерируем уникальное имя файла
            filename = f"{current_user.id}_{int(time.time())}_{secure_filename(file.filename)}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # обновляем поле в базе
            current_user.profile_photo = filename
            db.session.commit()
            flash("Profile photo updated!", "success")
    return redirect(url_for("profile"))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page"""
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if email already exists
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already exists', 'error')
            return render_template('register.html', form=form)
        
        # Check if username already exists
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists', 'error')
            return render_template('register.html', form=form)
        
        # Create new user
        user = User(
            business_name=form.business_name.data,
            username=form.username.data,
            email=form.email.data,
            phone_number=form.phone_number.data
        )
        user.set_password(form.password.data)
        
        # Start trial period for new user
        user.start_trial(30)  # 30 days trial
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! You have a 30-day free trial period. During this time you can sell products and view seller contact information without any payment. Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    # flash('You have been logged out successfully', 'info')
    return redirect(url_for('home'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page"""
    form = ProfileForm()
    
    if form.validate_on_submit():
        # Update user information
        current_user.business_name = form.business_name.data
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.phone_number = form.phone_number.data
        current_user.telegram_id = form.telegram_id.data

        # Удаление фото (если нажата корзина)
        if 'remove_photo' in request.form:
            if current_user.profile_photo:
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], current_user.profile_photo)
                if os.path.exists(filepath):
                    os.remove(filepath)
                current_user.profile_photo = None
                db.session.commit()
                flash('Profile photo removed successfully!', 'success')
                return redirect(url_for('profile'))

        # Загрузка нового фото (если выбрано)
        if form.profile_photo.data:
            # удалить старый файл, если есть
            if current_user.profile_photo:
                old_path = os.path.join(app.config['UPLOAD_FOLDER'], current_user.profile_photo)
                if os.path.exists(old_path):
                    os.remove(old_path)

            filename = secure_filename(form.profile_photo.data.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            form.profile_photo.data.save(filepath)
            current_user.profile_photo = filename
        
        # Handle password change
        if form.new_password.data:
            if form.current_password.data and current_user.check_password(form.current_password.data):
                current_user.set_password(form.new_password.data)
                flash('Password updated successfully!', 'success')
            else:
                flash('Current password is incorrect', 'error')
                return render_template('profile.html', form=form,
                                       subscription_days=current_user.subscription_days_remaining(),
                                       trial_days=current_user.trial_days_remaining(),
                                       subscription_end=current_user.subscription_end)
        
        # Check for duplicates
        if User.query.filter(User.id != current_user.id, User.email == form.email.data).first():
            flash('Email already exists', 'error')
            return render_template('profile.html', form=form,
                                   subscription_days=current_user.subscription_days_remaining(),
                                   trial_days=current_user.trial_days_remaining(),
                                   subscription_end=current_user.subscription_end)
        
        if User.query.filter(User.id != current_user.id, User.username == form.username.data).first():
            flash('Username already exists', 'error')
            return render_template('profile.html', form=form,
                                   subscription_days=current_user.subscription_days_remaining(),
                                   trial_days=current_user.trial_days_remaining(),
                                   subscription_end=current_user.subscription_end)
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    
    elif request.method == 'GET':
        # Pre-fill form with current user data
        form.business_name.data = current_user.business_name
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.phone_number.data = current_user.phone_number
        form.telegram_id.data = current_user.telegram_id
    
    return render_template('profile.html', form=form,
                         subscription_days=current_user.subscription_days_remaining(),
                         trial_days=current_user.trial_days_remaining(),
                         subscription_end=current_user.subscription_end)



@app.route('/sell', methods=['GET', 'POST'])
@subscription_required
def sell():
    """Sell product page"""
    
    form = ProductForm()
    
    # Populate category choices
    try:
        categories = Category.query.all()
        form.category_id.choices = [(c.id, c.name) for c in categories]
        logger.info(f"Loaded {len(categories)} categories for product form")
    except Exception as e:
        logger.error(f"Error loading categories: {e}")
        form.category_id.choices = []
    
    if request.method == 'POST':
        # Check if this is an AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if form.validate_on_submit():
            try:
                # Handle file upload
                photo_filename = None
                if 'photo' in request.files:
                    file = request.files['photo']
                    if file and file.filename:
                        filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
                        photo_filename = secure_filename(filename)
                        file.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))
                
                # Create new product
                product = Product(
                    title=form.title.data,
                    description=form.description.data,
                    price=form.price.data,
                    quantity=form.quantity.data,
                    category_id=form.category_id.data,
                    status=form.status.data,
                    seller_id=current_user.id,
                    photo_filename=photo_filename
                )
                
                db.session.add(product)
                db.session.commit()
                
                logger.info(f"Product '{product.title}' listed successfully by user {current_user.id}")
                
                if is_ajax:
                    return jsonify({
                        'success': True,
                        'message': 'Product listed successfully!'
                    })
                else:
                    flash('Product listed successfully!', 'success')
                    return redirect(url_for('dashboard'))
                    
            except Exception as e:
                logger.error(f"Error creating product: {e}")
                db.session.rollback()
                
                if is_ajax:
                    return jsonify({
                        'success': False,
                        'message': 'An error occurred while creating the product. Please try again.',
                        'errors': {'general': ['An error occurred while creating the product. Please try again.']}
                    })
                else:
                    flash('An error occurred while creating the product. Please try again.', 'error')
        
        # Form validation errors
        if is_ajax:
            errors = {}
            for field, field_errors in form.errors.items():
                errors[field] = field_errors
            
            return jsonify({
                'success': False,
                'message': 'Please fix the errors in the form.',
                'errors': errors
            })
    
    # GET request - render the template
    return render_template('sell.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    try:
        user_products = Product.query.filter_by(seller_id=current_user.id).order_by(Product.created_at.desc()).all()
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        user_products = []
    
    # Create a form for CSRF token
    from forms import SearchForm
    form = SearchForm()
    return render_template('dashboard.html', products=user_products, form=form,
                         subscription_days=current_user.subscription_days_remaining(),
                         trial_days=current_user.trial_days_remaining())

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """Product detail page"""
    print(f"DEBUG: Accessing product {product_id}")
    
    product = Product.query.get_or_404(product_id)
    print(f"DEBUG: Product found, current views: {product.views}")
    
    # Increment view count with proper session management
    try:
        # Ensure views is not None
        if product.views is None:
            product.views = 0
            print(f"DEBUG: Product {product_id} had None views, setting to 0")
        
        old_views = product.views
        product.views += 1
        print(f"DEBUG: Incrementing views from {old_views} to {product.views}")
        
        # Explicitly add to session and commit
        db.session.add(product)
        db.session.commit()
        print(f"DEBUG: Database commit completed")
        
        # Verify the update
        db.session.refresh(product)
        print(f"DEBUG: Verified views after commit: {product.views}")
        
    except Exception as e:
        print(f"ERROR: Failed to update views: {e}")
        db.session.rollback()
        print("DEBUG: Session rolled back")
    
    # Check if current user has favorited this product
    is_favorited = False
    has_reviewed = False
    seller_subscription = None
    
    if current_user.is_authenticated:
        is_favorited = Favorite.query.filter_by(user_id=current_user.id, product_id=product_id).first() is not None
        has_reviewed = Review.query.filter_by(product_id=product_id, reviewer_id=current_user.id).first() is not None
        
        # If admin, get seller subscription info
        if current_user.is_admin:
            seller = product.seller
            seller_subscription = {
                'is_active': seller.is_subscription_active(),
                'days_remaining': seller.subscription_days_remaining(),
                'trial_days': seller.trial_days_remaining(),
                'subscription_end': seller.subscription_end,
                'trial_end': seller.trial_end
            }
    
    # Create a form for CSRF token
    from forms import ReviewForm
    form = ReviewForm()
    return render_template('product_detail.html', product=product, is_favorited=is_favorited, has_reviewed=has_reviewed, form=form, seller_subscription=seller_subscription)

@app.route('/product/<int:product_id>/review', methods=['POST'])
@login_required
def add_review(product_id):
    """Add a review to a product"""
    product = Product.query.get_or_404(product_id)
    
    # Check if user already reviewed this product
    existing_review = Review.query.filter_by(product_id=product_id, reviewer_id=current_user.id).first()
    if existing_review:
        flash('You have already reviewed this product', 'error')
        return redirect(url_for('product_detail', product_id=product_id))
    
    form = ReviewForm()
    if form.validate_on_submit():
        review = Review(
            rating=form.rating.data,
            comment=form.comment.data,
            product_id=product_id,
            reviewer_id=current_user.id
        )
        
        db.session.add(review)
        db.session.commit()
        
        flash('Review added successfully!', 'success')
    else:
        flash('Invalid review data', 'error')
    
    return redirect(url_for('product_detail', product_id=product_id))

@app.route('/toggle-favorite/<int:product_id>', methods=['POST'])
@login_required
def toggle_favorite(product_id):
    """Toggle favorite status"""
    try:
        product = Product.query.get_or_404(product_id)
        
        existing_favorite = Favorite.query.filter_by(user_id=current_user.id, product_id=product_id).first()
        
        if existing_favorite:
            # Remove from favorites
            db.session.delete(existing_favorite)
            is_saved = False
        else:
            # Add to favorites
            favorite = Favorite(user_id=current_user.id, product_id=product_id)
            db.session.add(favorite)
            is_saved = True
        
        db.session.commit()
        
        return jsonify({'status': 'success', 'is_saved': is_saved})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/favorites')
@login_required
def favorites():
    """User favorites page"""
    try:
        favorites = Favorite.query.filter_by(user_id=current_user.id).order_by(Favorite.created_at.desc()).all()
    except Exception as e:
        logger.error(f"Error loading favorites: {e}")
        favorites = []
    
    # Create a form for CSRF token
    from forms import SearchForm
    form = SearchForm()
    return render_template('favorites.html', favorites=favorites, form=form)

@app.route('/search', methods=['GET', 'POST'])
def search():
    """Search products with fuzzy matching (works with typos)"""
    form = SearchForm()
    
    try:
        categories = Category.query.all()
        form.category.choices = [(0, 'All Categories')]
        if current_user.is_authenticated:
            form.category.choices.append((-1, '❤️ My Favorites'))
        form.category.choices += [(c.id, c.name) for c in categories]
    except Exception as e:
        logger.error(f"Error loading search categories: {e}")
        categories = []
        form.category.choices = [(0, 'All Categories')]
    
    products = []
    if request.method == 'POST' and form.validate_on_submit():
        query = form.query.data.strip() if form.query.data else ''
        category_id = form.category.data
        
        logger.info(f"Search query: '{query}', category_id: {category_id}")
        
        # --- Favorites (точное совпадение, fuzzy тут не нужен) ---
        if category_id == -1:
            if current_user.is_authenticated:
                favorite_product_ids = [f.product_id for f in Favorite.query.filter_by(user_id=current_user.id).all()]
                products = Product.query.filter(Product.id.in_(favorite_product_ids)).order_by(Product.created_at.desc()).all()
            else:
                products = []
        else:
            # Базовый фильтр по статусу и категории
            base_query = Product.query.filter_by(status='Available')
            if category_id and category_id != 0:
                base_query = base_query.filter_by(category_id=category_id)
            
            if query:
                # === Шаг 1: Ищем точные подстроки (быстро) ===
                exact_matches = base_query.filter(
                    Product.title.ilike(f'%{query}%') | 
                    Product.description.ilike(f'%{query}%')
                ).all()
                
                # === Шаг 2: Если мало результатов (<3) — добавляем "похожие" (fuzzy) ===
                if len(exact_matches) < 3:
                    # Берём пул кандидатов (последние 200 товаров — для скорости)
                    candidate_pool = base_query.order_by(Product.created_at.desc()).limit(200).all()
                    
                    scored_results = []
                    query_lower = query.lower()
                    
                    for product in candidate_pool:
                        # Считаем схожесть по заголовку и описанию
                        title_score = fuzz.partial_ratio(query_lower, product.title.lower())
                        desc_score  = fuzz.partial_ratio(query_lower, product.description.lower())
                        token_score = fuzz.token_sort_ratio(query_lower, product.title.lower())
                        
                        best_score = max(title_score, desc_score, token_score)
                        
                        # Порог 60: "достаточно похоже" (можно изменить на 50–70)
                        if best_score > 60:
                            scored_results.append((product, best_score))
                    
                    # Сортируем по релевантности (сначала самые похожие)
                    scored_results.sort(key=lambda x: x[1], reverse=True)
                    
                    # Объединяем: exact + fuzzy (без дубликатов)
                    exact_ids = {p.id for p in exact_matches}
                    fuzzy_matches = [p for p, _ in scored_results if p.id not in exact_ids]
                    
                    products = exact_matches + fuzzy_matches
                    logger.info(f"Fuzzy search added {len(fuzzy_matches)} similar products for query '{query}'")
                else:
                    products = exact_matches
                    # Если точных много — сортируем по дате (как раньше)
                    products = sorted(products, key=lambda p: p.created_at, reverse=True)
            else:
                # Просто категория, без текста
                products = base_query.order_by(Product.created_at.desc()).all()
    
    elif request.method == 'GET':
        # Показать все доступные товары при первом заходе
        products = Product.query.filter_by(status='Available').order_by(Product.created_at.desc()).all()
    
    return render_template('search.html', form=form, products=products, categories=categories)

@app.route('/api/search')
def api_search():
    """API endpoint for AJAX search with fuzzy support"""
    query = request.args.get('q', '').strip()
    category_id = request.args.get('category', type=int)
    
    if not query:
        return jsonify([])
    
    try:
        product_query = Product.query.filter_by(status='Available')
        
        if category_id and category_id > 0:
            product_query = product_query.filter_by(category_id=category_id)
        
        # 1️⃣ Точные совпадения (быстро)
        products = product_query.filter(
            Product.title.ilike(f'%{query}%') | 
            Product.description.ilike(f'%{query}%')
        ).limit(10).all()
        
        # 2️⃣ Если мало — добавляем похожие (fuzzy)
        if len(products) < 3:
            candidates = product_query.limit(100).all()  # ограничиваем для скорости
            query_lower = query.lower()
            scored = []
            
            for p in candidates:
                score = max(
                    fuzz.partial_ratio(query_lower, p.title.lower()),
                    fuzz.partial_ratio(query_lower, p.description.lower())
                )
                if score > 60:  # порог "похожести"
                    scored.append((p, score))
            
            scored.sort(key=lambda x: x[1], reverse=True)
            
            # Добавляем не-дубликаты
            existing_ids = {p.id for p in products}
            for p, _ in scored:
                if p.id not in existing_ids:
                    products.append(p)
                    if len(products) >= 20:  # общий лимит ответа
                        break
        
        # Формируем JSON
        result = []
        for product in products:
            is_favorited = False
            if current_user.is_authenticated:
                is_favorited = Favorite.query.filter_by(user_id=current_user.id, product_id=product.id).first() is not None
            
            result.append({
                'id': product.id,
                'title': product.title,
                'description': product.description,
                'price': float(product.price),
                'category': product.category.name if product.category else 'Unknown',
                'is_favorited': is_favorited,
                'photo_filename': product.photo_filename
            })
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin')
@login_required
def admin():
    """Admin dashboard"""
    if current_user.role != 'Admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('home'))
    
    try:
        products = Product.query.order_by(Product.created_at.desc()).all()
    except Exception as e:
        logger.error(f"Error loading admin dashboard: {e}")
        products = []
    
    return render_template('admin.html', products=products)

@app.route('/product/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    """Edit a product"""
    product = Product.query.get_or_404(product_id)
    
    # Check if current user is the seller
    if product.seller_id != current_user.id:
        flash('You can only edit your own products', 'error')
        return redirect(url_for('dashboard'))
    
    form = ProductForm()
    
    # Populate category choices
    try:
        categories = Category.query.all()
        form.category_id.choices = [(c.id, c.name) for c in categories]
        logger.info(f"Loaded {len(categories)} categories for edit form")
    except Exception as e:
        logger.error(f"Error loading categories: {e}")
        form.category_id.choices = []
    
    if form.validate_on_submit():
        # Handle file upload
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename:
                # Generate unique filename
                filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
                photo_filename = secure_filename(filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))
                product.photo_filename = photo_filename
        
        # Update product fields
        product.title = form.title.data
        product.description = form.description.data
        product.price = form.price.data
        product.quantity = form.quantity.data
        product.category_id = form.category_id.data
        product.status = form.status.data
        
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    elif request.method == 'GET':
        # Pre-fill form with current product data
        form.title.data = product.title
        form.description.data = product.description
        form.price.data = float(product.price)
        form.quantity.data = product.quantity
        form.category_id.data = product.category_id
        form.status.data = product.status
    
    return render_template('edit_product.html', form=form, product=product)

@app.route('/product/<int:product_id>/delete', methods=['POST'])
@login_required
def delete_product(product_id):
    """Delete a product (owner only)"""
    product = Product.query.get_or_404(product_id)
    
    # Check if current user is the seller or admin
    if product.seller_id != current_user.id and current_user.role != 'Admin':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        flash('Access denied. You can only delete your own products.', 'error')
        return redirect(url_for('dashboard'))
    
    product_title = product.title
    
    try:
        # Delete the product (this will also delete related reviews and favorites due to cascade)
        db.session.delete(product)
        db.session.commit()
        logger.info(f'Product {product_id} deleted by user {current_user.id}')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'message': f'Product "{product_title}" has been deleted successfully'
            })
        
        flash(f'Product "{product_title}" has been deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting product {product_id}: {e}")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'An error occurred while deleting the product'}), 500
        
        flash('An error occurred while deleting the product. Please try again.', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/admin/delete_product/<int:product_id>')
@login_required
def admin_delete_product(product_id):
    """Delete a product (admin only)"""
    if current_user.role != 'Admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('home'))
    
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash(f'Product "{product.title}" has been deleted', 'success')
    return redirect(url_for('admin'))

@app.route('/view-seller/<int:product_id>')
@login_required
def view_seller_number(product_id):
    """View seller contact information"""
    product = Product.query.get_or_404(product_id)
    
    # Admins can always view without restrictions
    if current_user.is_admin:
        return render_template('seller_contact.html', product=product, seller=product.seller)
    
    # Check if user has active subscription or trial
    if not current_user.can_access_platform():
        flash('Your subscription has expired. Please pay 5 manat to continue using the platform for 30 days.', 'warning')
        return redirect(url_for('subscription_expired'))
    
    return render_template('seller_contact.html', product=product, seller=product.seller)

@app.route('/test-payment')
def test_payment_page():
    """Simple test page for payment processing"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Payment Test</title>
        <style>
            body { font-family: Arial; padding: 20px; }
            .container { max-width: 600px; margin: 0 auto; }
            .form-group { margin: 10px 0; }
            input, button { padding: 10px; margin: 5px; }
            .result { margin: 20px 0; padding: 10px; background: #f0f0f0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🧪 Payment Testing Interface</h2>
            <p>Test your payment system without Telegram bot</p>
            
            <form id="paymentForm">
                <div class="form-group">
                    <label>Username:</label>
                    <input type="text" id="username" value="your_username" required>
                </div>
                <div class="form-group">
                    <label>Amount:</label>
                    <input type="number" id="amount" value="5" min="1" required>
                </div>
                <button type="submit">Test Payment</button>
            </form>
            
            <div id="result" class="result" style="display:none;"></div>
        </div>
        
        <script>
        document.getElementById('paymentForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const data = {
                telegram_id: '123456789',
                username: document.getElementById('username').value,
                amount: parseFloat(document.getElementById('amount').value),
                message: 'PAY ' + document.getElementById('amount').value
            };
            
            try {
                const response = await fetch('/api/payment/telegram', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                const resultDiv = document.getElementById('result');
                
                if (response.ok) {
                    resultDiv.innerHTML = `
                        <h3>✅ Payment Successful!</h3>
                        <p><strong>Amount:</strong> ${result.amount} tokens</p>
                        <p><strong>New Balance:</strong> ${result.new_balance} tokens</p>
                        <p><strong>Transaction ID:</strong> ${result.payment_id}</p>
                        <p><strong>User ID:</strong> ${result.user_id}</p>
                    `;
                    resultDiv.style.background = '#d4edda';
                } else {
                    resultDiv.innerHTML = `
                        <h3>❌ Payment Failed</h3>
                        <p><strong>Error:</strong> ${result.error}</p>
                    `;
                    resultDiv.style.background = '#f8d7da';
                }
                
                resultDiv.style.display = 'block';
            } catch (error) {
                document.getElementById('result').innerHTML = `
                    <h3>❌ Connection Error</h3>
                    <p>${error.message}</p>
                `;
                document.getElementById('result').style.display = 'block';
            }
        });
        </script>
    </body>
    </html>
    '''

@app.route('/api/payment/test', methods=['POST'])
def test_payment_api():
    """Simple test API endpoint"""
    return jsonify({
        'message': 'Test API is working',
        'status': 'success'
    })

@app.route('/api/payment/telegram', methods=['POST'])
@csrf.exempt  # Disable CSRF for API endpoint
def telegram_payment():
    """API endpoint to receive Telegram payment notifications"""
    try:
        data = request.get_json()
        
        telegram_id = data.get('telegram_id')
        username = data.get('username')
        amount = data.get('amount')
        message_text = data.get('message', '')
        
        if not telegram_id or not amount or amount <= 0:
            return jsonify({'error': 'Invalid telegram_id or amount'}), 400
        
        # Find user by telegram_id, username, email, or phone number
        user = None
        
        # Try to find by telegram_id first
        if telegram_id:
            user = User.query.filter_by(telegram_id=str(telegram_id)).first()
        
        # If not found, try username
        if not user and username:
            user = User.query.filter_by(username=username).first()
        
        # If still not found, try email (for login with email users)
        if not user and username:
            # Try to find by email if username looks like email
            if '@' in username:
                user = User.query.filter_by(email=username).first()
        
        # If still not found, try phone number
        if not user:
            user = User.query.filter_by(phone_number=str(telegram_id)).first()
        
        if not user:
            return jsonify({'error': 'User not found. Please link your Telegram account in profile.'}), 404
        
        # Generate unique transaction ID
        transaction_id = f"TG_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{str(telegram_id)[-4:]}"
        
        # Check if transaction already exists
        existing_payment = Payment.query.filter_by(transaction_id=transaction_id).first()
        if existing_payment:
            return jsonify({'error': 'Transaction already processed'}), 400
        
        # Create payment record
        payment = Payment(
            amount=amount,
            sender_phone=f"TG_{telegram_id}",  # Store Telegram ID as phone
            transaction_id=transaction_id,
            user_id=user.id,
            status='completed',
            processed_at=datetime.now(timezone.utc)
        )
        
        # For 5 manat payment - activate 30-day subscription
        if amount >= 5:
            user.start_subscription(days=30)
            subscription_msg = f"30-day subscription activated! Expires: {user.subscription_end.strftime('%Y-%m-%d')}"
        else:
            subscription_msg = f"Payment received: {amount} manat. Minimum 5 manat required for subscription."
        
        # Save to database
        db.session.add(payment)
        db.session.commit()
        
        logger.info(f"Telegram payment processed: {amount} manat from @{username} (TG:{telegram_id})")
        
        return jsonify({
            'success': True,
            'message': subscription_msg,
            'user_id': user.id,
            'subscription_active': user.subscription_active,
            'subscription_end': user.subscription_end.isoformat() if user.subscription_end else None,
            'days_remaining': user.subscription_days_remaining(),
            'payment_id': payment.id
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error processing Telegram payment: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/payment/sms', methods=['POST'])
def sms_payment():
    """API endpoint to receive SMS payment notifications (Clickatell compatible)"""
    try:
        # Get SMS data from request (Clickatell format)
        data = request.get_json() if request.is_json else request.form
        
        # Clickatell webhook format
        if request.is_json:
            sender_phone = data.get('from_number') or data.get('sender_phone')
            message_text = data.get('text') or data.get('message', '')
        else:
            # Form data format
            sender_phone = data.get('from_number') or data.get('sender_phone')
            message_text = data.get('text') or data.get('message', '')
        
        # Extract amount from message (e.g., "PAY 5" -> 5)
        amount = 0
        import re
        match = re.search(r'PAY\s+(\d+(?:\.\d+)?)', message_text.upper())
        if match:
            amount = float(match.group(1))
        
        if not sender_phone or amount <= 0:
            return jsonify({'error': 'Invalid phone number or amount'}), 400
        
        # Clean phone number (remove +, spaces, etc.)
        sender_phone = re.sub(r'[^\d]', '', sender_phone)
        if len(sender_phone) == 9 and not sender_phone.startswith('994'):
            sender_phone = '994' + sender_phone
        
        # Find user by phone number
        user = User.query.filter_by(phone_number=sender_phone).first()
        if not user:
            return jsonify({'error': 'User not found for this phone number'}), 404
        
        # Generate unique transaction ID
        transaction_id = f"CL_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{sender_phone[-4:]}"
        
        # Check if transaction already exists
        existing_payment = Payment.query.filter_by(transaction_id=transaction_id).first()
        if existing_payment:
            return jsonify({'error': 'Transaction already processed'}), 400
        
        # Create payment record
        payment = Payment(
            amount=amount,
            sender_phone=sender_phone,
            transaction_id=transaction_id,
            user_id=user.id,
            status='completed',
            processed_at=datetime.now(timezone.utc)
        )
        
        # For 5 manat payment - activate 30-day subscription
        if amount >= 5:
            user.start_subscription(days=30)
            subscription_msg = f"30-day subscription activated! Expires: {user.subscription_end.strftime('%Y-%m-%d')}"
        else:
            subscription_msg = f"Payment received: {amount} manat. Minimum 5 manat required for subscription."
        
        # Save to database
        db.session.add(payment)
        db.session.commit()
        
        logger.info(f"Clickatell payment processed: {amount} manat from {sender_phone} for user {user.id}")
        
        return jsonify({
            'success': True,
            'message': subscription_msg,
            'user_id': user.id,
            'subscription_active': user.subscription_active,
            'subscription_end': user.subscription_end.isoformat() if user.subscription_end else None,
            'days_remaining': user.subscription_days_remaining(),
            'payment_id': payment.id
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error processing SMS payment: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Admin Routes
@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    """Admin dashboard - display all users"""
    users = User.query.all()
    return render_template('admin_users.html', users=users)

@app.route('/admin/user/<int:id>/balance', methods=['POST'])
@login_required
@admin_required
def update_user_balance(id):
    """Update user balance"""
    user = User.query.get_or_404(id)
    new_balance = request.form.get('balance', type=float)
    
    if new_balance is None or new_balance < 0:
        flash('Invalid balance amount', 'error')
        return redirect(url_for('admin_users'))
    
    user.balance = new_balance
    db.session.commit()
    flash(f'Updated balance for {user.username} to {new_balance}', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/user/<int:id>/extend', methods=['POST'])
@login_required
@admin_required
def extend_subscription(id):
    """Extend user subscription by admin"""
    user = User.query.get_or_404(id)
    days = request.form.get('days', type=int, default=30)
    
    if days <= 0:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Invalid number of days'}), 400
        flash('Invalid number of days', 'error')
        return redirect(url_for('admin_users'))
    
    # If subscription is expired, start new one; otherwise extend current
    if not user.subscription_active or not user.subscription_end or user.subscription_end < datetime.now(timezone.utc).replace(tzinfo=None):
        user.start_subscription(days=days)
        action = "activated"
    else:
        # Extend existing subscription
        user.subscription_end = user.subscription_end + timedelta(days=days)
        user.subscription_active = True
        action = "extended"
    
    db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'message': f'Subscription {action} for {user.username}!',
            'days_remaining': user.subscription_days_remaining(),
            'subscription_end': user.subscription_end.isoformat() if user.subscription_end else None
        })
    
    flash(f'Subscription {action} for {user.username}! Now expires: {user.subscription_end.strftime("%Y-%m-%d")}', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/user/<int:id>/block', methods=['POST'])
@login_required
@admin_required
def toggle_user_block(id):
    """Toggle user blocked status"""
    user = User.query.get_or_404(id)
    
    # Don't allow blocking admin users
    if user.is_admin:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Cannot block admin users'}), 403
        flash('Cannot block admin users', 'error')
        return redirect(url_for('admin_users'))
    
    user.is_blocked = not user.is_blocked
    status = 'unblocked' if not user.is_blocked else 'blocked'
    db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'message': f'User {user.username} has been {status}',
            'is_blocked': user.is_blocked
        })
    
    flash(f'User {user.username} has been {status}', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/user/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(id):
    """Delete user with confirmation"""
    user = User.query.get_or_404(id)
    
    # Don't allow deleting admin users
    if user.is_admin:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Cannot delete admin users'}), 403
        flash('Cannot delete admin users', 'error')
        return redirect(url_for('admin_users'))
    
    # Confirmation check
    if request.form.get('confirm') != user.username:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Confirmation does not match username'}), 400
        flash('Confirmation does not match username. Deletion cancelled.', 'error')
        return redirect(url_for('admin_users'))
    
    username = user.username
    
    try:
        # Delete user's related records first
        # Delete payments made by this user
        Payment.query.filter_by(user_id=id).delete()
        
        # Delete favorites where user is the owner
        Favorite.query.filter_by(user_id=id).delete()
        
        # Delete reviews made by this user
        Review.query.filter_by(reviewer_id=id).delete()
        
        # Delete favorites of this user's products (other users' favorites)
        user_product_ids = [p.id for p in user.products]
        if user_product_ids:
            Favorite.query.filter(Favorite.product_id.in_(user_product_ids)).delete()
        
        # Delete user's products
        Product.query.filter_by(seller_id=id).delete()
        
        # Delete the user
        db.session.delete(user)
        db.session.commit()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'message': f'User {username} has been deleted successfully'
            })
        
        flash(f'User {username} has been deleted successfully', 'success')
        
    except Exception as e:
        db.session.rollback()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': str(e)}), 500
        flash(f'Error deleting user: {str(e)}', 'error')
        logger.error(f"Error deleting user {id}: {e}")
    
    return redirect(url_for('admin_users'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
