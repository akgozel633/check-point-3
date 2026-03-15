import json
import urllib.request
import urllib.parse
import sqlite3
import re
import random
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, g, session
from uuid import uuid4
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "recipe_pro_ultra_secret_2026"

DATABASE = 'recipes.db'
APP_BOOT_ID = str(uuid4())

# ---------------- DATABASE ----------------

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    cur = db.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            id TEXT PRIMARY KEY,
            name TEXT,
            category TEXT,
            rating INTEGER,
            image_url TEXT,
            ingredients TEXT,
            instructions TEXT,
            favorite INTEGER DEFAULT 0,
            owner_id INTEGER
        )
    ''')

    # Add owner_id column if it doesn't exist (for existing databases)
    cur.execute('PRAGMA table_info(recipes)')
    columns = [row[1] for row in cur.fetchall()]
    if 'owner_id' not in columns:
        cur.execute('ALTER TABLE recipes ADD COLUMN owner_id INTEGER')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            query TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # ---- MIGRATION: add columns for structured history ----
    cur.execute('PRAGMA table_info(search_history)')
    cols = [row[1] for row in cur.fetchall()]

    if 'search_query' not in cols:
        cur.execute('ALTER TABLE search_history ADD COLUMN search_query TEXT')
    if 'ingredients' not in cols:
        cur.execute('ALTER TABLE search_history ADD COLUMN ingredients TEXT')

    db.commit()

# ---------------- HELPERS ----------------

def check_password_strength(password):
    """
    Check password strength and return (is_valid, score, errors).
    Score: 0-5 (0=weak, 5=strong)
    """
    errors = []
    score = 0
    
    if len(password) >= 8:
        score += 1
    else:
        errors.append("At least 8 characters")
    
    if re.search(r'[A-Z]', password):
        score += 1
    else:
        errors.append("At least one uppercase letter")
    
    if re.search(r'[a-z]', password):
        score += 1
    else:
        errors.append("At least one lowercase letter")
    
    if re.search(r'\d', password):
        score += 1
    else:
        errors.append("At least one number")
    
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        score += 1
    else:
        errors.append("At least one special character (!@#$%^&*...)")
    
    # Require minimum score of 4 for strong password
    is_valid = score >= 4
    return is_valid, score, errors

def generate_captcha():
    """Generate a simple math captcha with addition only."""
    a = random.randint(1, 20)
    b = random.randint(1, 20)
    
    answer = a + b
    question = f"{a} + {b} = ?"
    
    # Store answer in session
    session['captcha_answer'] = answer
    return question

def row_to_recipe(row):
    return {
        'id': row['id'],
        'name': row['name'],
        'category': row['category'],
        'rating': row['rating'],
        'image_url': row['image_url'],
        'ingredients': row['ingredients'],
        'instructions': row['instructions'],
        'favorite': bool(row['favorite']),
        'owner_id': row['owner_id']
    }

def get_current_user():
    uid = session.get('user_id')
    if not uid:
        return None
    cur = get_db().cursor()
    cur.execute('SELECT id, username FROM users WHERE id=?', (uid,))
    row = cur.fetchone()
    return {'id': row['id'], 'username': row['username']} if row else None

def load_recipes(favorite=None, ingredient=None, search_query=None):
    """
    Загружает рецепты для текущего пользователя с возможностью фильтрации.
    """
    user = get_current_user()
    if not user:
        return []

    cur = get_db().cursor()

    # Базовый SQL-запрос
    sql = "SELECT * FROM recipes WHERE owner_id=?"
    params = [user['id']]

    # Добавляем фильтры в запрос, если они есть
    if favorite is not None:
        sql += " AND favorite=?"
        params.append(1 if favorite else 0)

    if ingredient:
        sql += " AND ingredients LIKE ?"
        params.append(f"%{ingredient}%")

    if search_query:
        # Ищем по названию ИЛИ по ингредиентам
        sql += " AND (name LIKE ? OR ingredients LIKE ?)"
        like_query = f"%{search_query}%"
        params.extend([like_query, like_query])

    # Добавляем сортировку
    sql += " ORDER BY name"

    # Выполняем запрос
    cur.execute(sql, params)
    rows = cur.fetchall()

    return [row_to_recipe(r) for r in rows]

def add_recipe_to_db(recipe):
    cur = get_db().cursor()
    cur.execute(
        "INSERT INTO recipes (id,name,category,rating,image_url,ingredients,instructions,favorite,owner_id) VALUES (?,?,?,?,?,?,?,?,?)",
        (
            recipe['id'],
            recipe['name'],
            recipe['category'],
            recipe['rating'],
            recipe['image_url'],
            recipe['ingredients'],
            recipe['instructions'],
            1 if recipe.get('favorite') else 0,
            recipe['owner_id']
        )
    )
    get_db().commit()

# ---------------- HOME ----------------

@app.route('/')
def home():
    if session.get('boot_id') != APP_BOOT_ID:
        return redirect(url_for('welcome'))
    

    favorite_filter   = request.args.get('favorite')   # "yes" or "no"
    ingredient_filter = request.args.get('ingredient') 
    search_query      = request.args.get('q')           # offline search term

    # Convert favorite_filter to Boolean (None = no filter)
    favorite = None
    if favorite_filter == 'yes':
        favorite = True
    elif favorite_filter == 'no':
        favorite = False

    recipes = load_recipes(
        favorite=favorite,
        ingredient=ingredient_filter,
        search_query=search_query
    )


    return render_template('index.html',         
        recipes=recipes, 
        current_user=get_current_user(),
        fav_filter=favorite_filter,
        ing_filter=ingredient_filter,
        search_q=search_query)

# ---------------- SEARCH ----------------

def fetch_from_mealdb(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except:
        return None

@app.route('/search', methods=['GET', 'POST'])
def search_online():
    results = []
    query = ""
    ingredients = ""

    # 1) Берём данные либо из POST (форма), либо из GET (Search Again)
    if request.method == 'POST':
        query = (request.form.get('search_query') or "").strip()
        ingredients = (request.form.get('ingredients') or "").strip()
    else:
        query = (request.args.get('search_query') or "").strip()
        ingredients = (request.args.get('ingredients') or "").strip()

    # Нормализуем пустые строки -> ""
    query = query.strip()
    ingredients = ingredients.strip()

    # 2) Если есть что искать — выполняем поиск (и на GET тоже)
    if query or ingredients:
        data = None

        # Search by recipe name
        if query:
            url = f"https://www.themealdb.com/api/json/v1/1/search.php?s={urllib.parse.quote(query)}"
            data = fetch_from_mealdb(url)

        # Search by ingredients
        if ingredients:
            url = f"https://www.themealdb.com/api/json/v1/1/filter.php?i={urllib.parse.quote(ingredients)}"
            ing_data = fetch_from_mealdb(url)

            if ing_data and ing_data.get("meals"):
                if data and data.get("meals"):
                    existing_ids = {meal['idMeal'] for meal in data['meals']}
                    for meal in ing_data['meals']:
                        if meal['idMeal'] not in existing_ids:
                            data['meals'].append(meal)
                else:
                    data = ing_data

        results = data.get("meals") if data and data.get("meals") else []

        # Add local results
        user = get_current_user()
        if user:
            cur = get_db().cursor()
            sql = "SELECT * FROM recipes WHERE owner_id=?"
            params = [user['id']]

            if query:
                sql += " AND (name LIKE ? OR ingredients LIKE ?)"
                like_q = f"%{query}%"
                params.extend([like_q, like_q])

            if ingredients:
                sql += " AND ingredients LIKE ?"
                params.append(f"%{ingredients}%")

            cur.execute(sql, params)
            local_rows = cur.fetchall()

            local_results = []
            for row in local_rows:
                local_results.append({
                    "idMeal": row["id"],
                    "strMeal": row["name"],
                    "strCategory": row["category"],
                    "strMealThumb": row["image_url"] or "",
                    "strIngredients": row["ingredients"],
                    "strInstructions": row["instructions"],
                    "is_local": True
                })

            if local_results:
                existing_ids = {meal.get('idMeal') for meal in results}
                for meal in local_results:
                    if meal['idMeal'] not in existing_ids:
                        results.append(meal)

        if not results:
            flash("No recipes found.", "warning")

        # 3) Сохраняем историю ТОЛЬКО на POST (чтобы Search Again не плодил дубли)
        if request.method == 'POST':
            user = get_current_user()
            if user:
                combined = " | ".join([x for x in [query, ingredients] if x])  # legacy display if нужно
                try:
                    cur = get_db().cursor()
                    cur.execute(
                        "INSERT INTO search_history (user_id, query, search_query, ingredients) VALUES (?, ?, ?, ?)",
                        (user['id'], combined, query or None, ingredients or None)
                    )
                    get_db().commit()
                except:
                    pass

    return render_template(
        "search.html",
        results=results,
        query=query,
        ingredients=ingredients,
        current_user=get_current_user()
    )
# ---------------- CREATE RECIPE ----------------

@app.route('/create', methods=['GET','POST'])
def create():
    if not get_current_user():
        flash("Login required.", "warning")
        return redirect(url_for('login'))

    if request.method == 'POST':
        recipe = {
            "id": str(uuid4()),
            "name": request.form.get('name'),
            "category": request.form.get('category'),
            "rating": int(request.form.get('rating',5)),
            "image_url": request.form.get('image_url'),
            "ingredients": request.form.get('ingredients'),
            "instructions": request.form.get('instructions'),
            "favorite": False,
            "owner_id": get_current_user()['id']
        }
        add_recipe_to_db(recipe)
        flash("Recipe created!", "success")
        return redirect(url_for('home'))

    return render_template("add_recipe.html", current_user=get_current_user())

# ---------------- AUTH ----------------

@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'GET':
        # Generate new captcha only for page loads
        captcha_question = generate_captcha()
        return render_template("signup.html", captcha_question=captcha_question, current_user=get_current_user())
    
    # POST request - process form
    username = request.form.get('username','').strip()
    password = request.form.get('password','')
    confirm_password = request.form.get('confirm_password','')
    captcha_input = request.form.get('captcha','')

    if not username or not password:
        flash("Username and password required.", "danger")
        # Generate new captcha for the retry
        captcha_question = generate_captcha()
        return render_template("signup.html", captcha_question=captcha_question, username=username, current_user=get_current_user())

    # Check password strength
    is_valid, score, errors = check_password_strength(password)
    
    if not is_valid:
        for error in errors:
            flash(error, "warning")
        # Generate new captcha for the retry
        captcha_question = generate_captcha()
        return render_template("signup.html", captcha_question=captcha_question, username=username, current_user=get_current_user())
    
    if password != confirm_password:
        flash("Passwords do not match!", "danger")
        # Generate new captcha for the retry
        captcha_question = generate_captcha()
        return render_template("signup.html", captcha_question=captcha_question, username=username, current_user=get_current_user())
    
    # Check captcha
    stored_answer = session.get('captcha_answer')
    try:
        if int(captcha_input) != stored_answer:
            flash("Incorrect captcha answer. Please try again.", "danger")
            # Generate new captcha for the retry
            captcha_question = generate_captcha()
            return render_template("signup.html", captcha_question=captcha_question, username=username, current_user=get_current_user())
    except (ValueError, TypeError):
        flash("Please enter a valid captcha answer.", "danger")
        # Generate new captcha for the retry
        captcha_question = generate_captcha()
        return render_template("signup.html", captcha_question=captcha_question, username=username, current_user=get_current_user())

    try:
        cur = get_db().cursor()
        cur.execute("INSERT INTO users (username,password_hash) VALUES (?,?)",
                    (username, generate_password_hash(password)))
        get_db().commit()
        flash("Account created! Please log in.", "success")
        return redirect(url_for('login'))
    except sqlite3.IntegrityError:
        flash("Username already exists.", "danger")
        # Generate new captcha for the retry
        captcha_question = generate_captcha()
        return render_template("signup.html", captcha_question=captcha_question, username=username, current_user=get_current_user())

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        password = request.form.get('password','')
        cur = get_db().cursor()
        cur.execute("SELECT id,password_hash FROM users WHERE username=?", (username,))
        row = cur.fetchone()

        if row and check_password_hash(row['password_hash'], password):
            session['user_id'] = row['id']
            session['username'] = username
            session['accepted_welcome'] = True
            session['boot_id'] = APP_BOOT_ID
            flash("Logged in!", "success")
            return redirect(url_for('home'))

        flash("Invalid username or password.", "danger")

    return render_template("login.html", current_user=get_current_user())

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for('welcome'))

# ---------------- OTHER PAGES ----------------

@app.route('/welcome')
def welcome():
    return render_template("welcome.html", current_user=get_current_user())

@app.route('/guest')
def guest_mode():
    session['guest'] = True
    session['accepted_welcome'] = True
    session['boot_id'] = APP_BOOT_ID
    return redirect(url_for('home'))

@app.route('/history')
def history():
    user = get_current_user()
    if not user:
        flash("Login required.", "warning")
        return redirect(url_for('login'))

    cur = get_db().cursor()
    cur.execute("""
        SELECT id, query, search_query, ingredients, timestamp
        FROM search_history
        WHERE user_id=?
        ORDER BY timestamp DESC
    """, (user['id'],))
    rows = cur.fetchall()

    items = []
    for r in rows:
        ts = r["timestamp"]
        # SQLite обычно отдаёт 'YYYY-MM-DD HH:MM:SS' строкой
        try:
            dt = datetime.fromisoformat(ts) if ts else None
        except:
            dt = None

        sq = r["search_query"]
        ing = r["ingredients"]

        # fallback для старых записей (если новые поля пустые)
        if (not sq and not ing) and r["query"]:
            sq = r["query"]

        params = {}
        if sq:
            params["search_query"] = sq
        if ing:
            params["ingredients"] = ing

        search_again_url = url_for("search_online", **params) if params else url_for("search_online")

        items.append({
            "id": r["id"],
            "search_query": sq or "",
            "ingredients": ing or "",
            "date": dt.strftime("%d %b %Y") if dt else (ts.split(" ")[0] if ts else ""),
            "time": dt.strftime("%H:%M") if dt else (ts.split(" ")[1][:5] if ts and " " in ts else ""),
            "search_again_url": search_again_url
        })

    return render_template("history.html", history=items, current_user=user)

@app.route('/clear_history', methods=['POST'])
def clear_history():
    user = get_current_user()
    if not user:
        flash("Login required.", "warning")
        return redirect(url_for('login'))

    cur = get_db().cursor()
    cur.execute("DELETE FROM search_history WHERE user_id=?", (user['id'],))
    get_db().commit()

    flash("Your search history has been cleared.", "success")
    return redirect(url_for('history'))

@app.route('/delete_history/<int:history_id>', methods=['POST'])
def delete_history(history_id):
    user = get_current_user()
    if not user:
        flash("Login required.", "warning")
        return redirect(url_for('login'))

    cur = get_db().cursor()
    cur.execute("DELETE FROM search_history WHERE id=? AND user_id=?", (history_id, user["id"]))
    get_db().commit()

    if cur.rowcount == 0:
        flash("No history", "warning")

    flash("Your search history has been cleared.", "success")
    return redirect(url_for('history'))

@app.route('/recipe/<recipe_id>')
def view_recipe(recipe_id):
    cur = get_db().cursor()
    cur.execute("SELECT * FROM recipes WHERE id=?", (recipe_id,))
    row = cur.fetchone()

    if not row:
        flash("Recipe not found.", "warning")
        return redirect(url_for('home'))

    recipe = row_to_recipe(row)
    return render_template("recipe_detail.html", recipe=recipe, current_user=get_current_user())

@app.route('/edit/<recipe_id>', methods=['GET','POST'])
def edit(recipe_id):
    user = get_current_user()
    if not user:
        flash("Login required.", "warning")
        return redirect(url_for('login'))

    cur = get_db().cursor()
    cur.execute("SELECT * FROM recipes WHERE id=? AND owner_id=?", (recipe_id, user['id']))
    row = cur.fetchone()
    if not row:
        flash("Recipe not found or not yours.", "danger")
        return redirect(url_for('home'))

    recipe = row_to_recipe(row)

    if request.method == 'POST':
        cur.execute(
            "UPDATE recipes SET name=?, category=?, rating=?, image_url=?, ingredients=?, instructions=? WHERE id=?",
            (
                request.form.get('name'),
                request.form.get('category'),
                int(request.form.get('rating',5)),
                request.form.get('image_url'),
                request.form.get('ingredients'),
                request.form.get('instructions'),
                recipe_id
            )
        )
        get_db().commit()
        flash("Recipe updated!", "success")
        return redirect(url_for('view_recipe', recipe_id=recipe_id))

    return render_template("edit_recipe.html", recipe=recipe, current_user=user)

@app.route('/delete/<recipe_id>', methods=['POST'])
def delete_recipe(recipe_id):
    user = get_current_user()
    if not user:
        return {"success": False, "message": "Login required"}, 401

    cur = get_db().cursor()
    cur.execute("DELETE FROM recipes WHERE id=? AND owner_id=?", (recipe_id, user['id']))
    get_db().commit()

    return {"success": True, "message": "Recipe deleted successfully"}


@app.route('/toggle_favorite/<recipe_id>', methods=['POST'])
def toggle_favorite(recipe_id):
    user = get_current_user()
    if not user:
        return {"success": False, "error": "Login required"}, 401

    cur = get_db().cursor()
    cur.execute("SELECT favorite FROM recipes WHERE id=? AND owner_id=?", (recipe_id, user['id']))
    row = cur.fetchone()
    if not row:
        return {"success": False, "error": "Recipe not found"}, 404

    new_value = 0 if row['favorite'] else 1
    cur.execute("UPDATE recipes SET favorite=? WHERE id=?", (new_value, recipe_id))
    get_db().commit()

    return {"success": True, "favorite": bool(new_value)}





@app.route('/save_online/<meal_id>', methods=['POST'])
def save_online(meal_id):
    user = get_current_user()
    if not user:
        flash("Login required.", "warning")
        return redirect(url_for('login'))

    # get recipe from API
    url = f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={meal_id}"
    data = fetch_from_mealdb(url)

    if not data or not data.get("meals"):
        flash("Recipe not found.", "danger")
        return redirect(url_for('search_online'))

    meal = data["meals"][0]

    recipe = {
        "id": str(uuid4()),
        "name": meal["strMeal"],
        "category": meal.get("strCategory"),
        "rating": 5,
        "image_url": meal["strMealThumb"],
        "ingredients": "",
        "instructions": meal.get("strInstructions"),
        "favorite": False,
        "owner_id": user["id"]
    }

    add_recipe_to_db(recipe)

    flash("Recipe saved to your collection!", "success")
    return redirect(url_for('home'))


# ---------------- RUN APP ----------------

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)

#lol