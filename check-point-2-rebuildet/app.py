import json
import os
import urllib.request
import urllib.parse
import sqlite3
import re
import random
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, g, session
from uuid import uuid4
from werkzeug.security import generate_password_hash, check_password_hash

COOKING_TIPS = [
    "⚡ Always prep ALL ingredients before turning on the heat (mise en place)!",
    "🧂 Season as you go — don’t wait until the end!",
    "🥩 Let meat rest 5‑10 min after cooking so juices stay inside.",
    "🔪 Keep your knives sharp — a dull knife is dangerous!",
    "🌶️ Toast whole spices for 30 sec before grinding for MAX flavor.",
    "🥚 Use room‑temperature eggs for better emulsification (e.g., hollandaise).",
    "🍳 Never crowd the pan — it steams food instead of searing it!"
]

app = Flask(__name__)
app.secret_key = "recipe_pro_ultra_secret_2026"
DATA_FILE = 'recipes.json'
DATABASE = 'recipes.db'
APP_BOOT_ID = str(uuid4())


# --- 1. DATABASE HELPERS (sqlite3) ---

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
            favorite INTEGER DEFAULT 0
        )
    ''')
    try:
        cur.execute('ALTER TABLE recipes ADD COLUMN owner_id INTEGER')
    except Exception:
        pass
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
    db.commit()


def migrate_json_to_db():
    if not os.path.exists(DATA_FILE):
        return
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT COUNT(*) FROM recipes')
    if cur.fetchone()[0] > 0:
        return
    try:
        with open(DATA_FILE, 'r') as f:
            recipes = json.load(f)
    except Exception:
        return

    for r in recipes:
        cur.execute(
            "INSERT OR REPLACE INTO recipes (id, name, category, rating, image_url, ingredients, instructions, favorite) VALUES (?,?,?,?,?,?,?,?)",
            (r.get('id', str(uuid4())), r.get('name'), r.get('category'), r.get('rating', 5), r.get('image_url'), r.get('ingredients'), r.get('instructions'), 1 if r.get('favorite') else 0)
        )
    db.commit()


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
        'owner_id': row['owner_id'] if 'owner_id' in row.keys() else None
    }


def load_recipes(favorite=None, ingredient=None, search_query=None):
    user = get_current_user()
    if not user:
        return []
    cur = get_db().cursor()
    
    query = '''SELECT * FROM recipes 
               WHERE owner_id = ?'''
    params = [user['id']]

    # ⭐ Filter by FAVORITE
    if favorite is not None:               # `True` = only favorites, `False` = only non‑favorites
        query += " AND favorite = ?"
        params.append(1 if favorite else 0)

    # 🥦 Filter by INGREDIENT
    if ingredient:
        query += " AND ingredients LIKE ?"
        params.append(f"%{ingredient}%")

    # 🔍 Offline SEARCH (name OR ingredients)
    if search_query:
        query += " AND (name LIKE ? OR ingredients LIKE ?)"
        search_term = f"%{search_query}%"
        params.extend([search_term, search_term])

    query += " ORDER BY name COLLATE NOCASE"
    
    cur.execute(query, params)
    rows = cur.fetchall()
    return [row_to_recipe(r) for r in rows]


def get_recipe_by_id(recipe_id):
    cur = get_db().cursor()
    cur.execute('SELECT * FROM recipes WHERE id = ?', (recipe_id,))
    row = cur.fetchone()
    return row_to_recipe(row) if row else None


def add_recipe_to_db(recipe):
    cur = get_db().cursor()
    cur.execute(
        "INSERT INTO recipes (id, name, category, rating, image_url, ingredients, instructions, favorite, owner_id) VALUES (?,?,?,?,?,?,?,?,?)",
        (recipe['id'], recipe['name'], recipe['category'], recipe['rating'], recipe['image_url'], recipe['ingredients'], recipe['instructions'], 1 if recipe.get('favorite') else 0, recipe.get('owner_id'))
    )
    get_db().commit()


def update_recipe_in_db(recipe):
    cur = get_db().cursor()
    cur.execute(
        "UPDATE recipes SET name=?, category=?, rating=?, image_url=?, ingredients=?, instructions=?, favorite=? WHERE id=?",
        (recipe['name'], recipe['category'], recipe['rating'], recipe['image_url'], recipe['ingredients'], recipe['instructions'], 1 if recipe.get('favorite') else 0, recipe['id'])
    )
    get_db().commit()


def delete_recipe_in_db(recipe_id):
    cur = get_db().cursor()
    cur.execute('DELETE FROM recipes WHERE id=?', (recipe_id,))
    get_db().commit()


def toggle_favorite_in_db(recipe_id, new_status):
    cur = get_db().cursor()
    cur.execute('UPDATE recipes SET favorite=? WHERE id=?', (1 if new_status else 0, recipe_id))
    get_db().commit()
# --- 2. HELPERS FOR EXTERNAL DATA ---

def fetch_from_mealdb(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def fetch_meal_from_api(meal_id):
    url = f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={meal_id}"
    data = fetch_from_mealdb(url)
    return data['meals'][0] if data and data.get('meals') else None


def parse_ingredients(meal):
    ingredients_list = []
    for i in range(1, 21):
        ing = meal.get(f'strIngredient{i}')
        meas = meal.get(f'strMeasure{i}')
        if ing and ing.strip():
            ingredients_list.append(f"{meas.strip() if meas else ''} {ing.strip()}".strip())
    return ingredients_list


def build_recipe_from_meal(meal):
    ingredients_list = parse_ingredients(meal)
    return {
        "id": str(uuid4()),
        "name": meal.get('strMeal'),
        "category": meal.get('strCategory', 'Web'),
        "rating": 5,
        "image_url": meal.get('strMealThumb'),
        "ingredients": "\n".join(ingredients_list),
        "instructions": meal.get('strInstructions', ''),
        "favorite": False
    }

@app.context_processor
def inject_cooking_tip():
    return {'cooking_tip': random.choice(COOKING_TIPS)}

@app.route('/clear-chef-flag', methods=['POST'])
def clear_chef_flag():
    # Remove the session flags → chef won't show again until next login
    session.pop('show_chef', None)
    session.pop('chef_tip', None)
    return jsonify(success=True)
# --- 3. MAIN ROUTES ---


@app.route('/')
def home():
    if session.get('boot_id') != APP_BOOT_ID:
        return redirect(url_for('welcome'))

    # Get filter values from URL/query string
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

    
    return render_template(
        'index.html', 
        recipes=recipes, 
        current_user=get_current_user(),
        fav_filter=favorite_filter,
        ing_filter=ingredient_filter,
        search_q=search_query,
    )


@app.route('/recipe/<string:recipe_id>')
def view_recipe(recipe_id):
    recipe = get_recipe_by_id(recipe_id)
    if recipe:
        return render_template('recipe_detail.html', recipe=recipe, current_user=get_current_user())
    flash("Recipe not found!", "warning")
    return redirect(url_for('home'))


@app.route('/toggle_favorite/<string:recipe_id>', methods=['POST'])
def toggle_favorite(recipe_id):
    try:
        user = get_current_user()
        if not user:
            return jsonify({"status": "error", "message": "Login required"}), 401
        recipe = get_recipe_by_id(recipe_id)
        if not recipe:
            return jsonify({"status": "error", "message": "Recipe not found"})
        if recipe.get('owner_id') != user['id']:
            return jsonify({"status": "error", "message": "Forbidden"}), 403

        data = request.get_json()
        new_status = data.get('favorite', False)
        toggle_favorite_in_db(recipe_id, new_status)
        return jsonify({"status": "success", "new_val": new_status})
    except Exception:
        return jsonify({"status": "error", "message": "Failed to update favorite. Try again."})


@app.route('/search', methods=['GET', 'POST'])
def search_online():
    results = []
    query = ""
    ingredients = ""

    if request.method == 'POST':
        query = request.form.get('search_query', '').strip()
        ingredients = request.form.get('ingredients', '').strip()

        if not query and not ingredients:
            flash("Please enter a recipe name or ingredient.", "warning")
            return render_template("search.html", results=[], query="")

        if ingredients:
            url = f"https://www.themealdb.com/api/json/v1/1/filter.php?i={urllib.parse.quote(ingredients)}"
        else:
            url = f"https://www.themealdb.com/api/json/v1/1/search.php?s={urllib.parse.quote(query)}"

        data = fetch_from_mealdb(url)

        if data and data.get("meals"):
            results = data["meals"]
        else:
            results = []
            flash("No recipes found.", "warning")

        # save search history
        try:
            user = get_current_user()
            cur = get_db().cursor()
            cur.execute(
                'INSERT INTO search_history (user_id, query) VALUES (?,?)',
                (user['id'] if user else None, query or ingredients)
            )
            get_db().commit()
        except Exception:
            pass

    return render_template(
        "search.html",
        results=results,
        query=query or ingredients,
        current_user=get_current_user()
    )

@app.route('/save_online/<string:meal_id>', methods=['POST'])
def save_online(meal_id):
    try:
        if not get_current_user():
            flash("Please log in or sign up to save recipes.", "warning")
            return redirect(url_for('login'))
        meal = fetch_meal_from_api(meal_id)
        if meal is None:
            raise ValueError("Meal not found in API.")
        new_recipe = build_recipe_from_meal(meal)
        new_recipe['owner_id'] = get_current_user()['id']
        add_recipe_to_db(new_recipe)
        flash(f"'{new_recipe['name']}' added to your collection!", "success")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception:
        flash("Failed to import recipe.", "danger")
    return redirect(url_for('home'))


@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        if not get_current_user():
            flash("Please log in or sign up to save recipes.", "warning")
            return redirect(url_for('login'))
        try:
            rating = int(request.form.get('rating', 5))
            if not 1 <= rating <= 5:
                raise ValueError

            new_entry = {
                "id": str(uuid4()),
                "name": request.form.get('name', 'Untitled').strip(),
                "category": request.form.get('category', 'Other').strip(),
                "rating": rating,
                "image_url": request.form.get('image_url', '').strip(),
                "ingredients": request.form.get('ingredients', '').strip(),
                "instructions": request.form.get('instructions', '').strip(),
                "favorite": False,
                "owner_id": get_current_user()['id']
            }
            add_recipe_to_db(new_entry)
            flash("Recipe created successfully!", "success")
            return redirect(url_for('home'))
        except ValueError:
            flash("Rating must be a number between 1 and 5.", "danger")
        except Exception:
            flash("Something went wrong while creating the recipe.", "danger")
    return render_template('add_recipe.html', current_user=get_current_user())


@app.route('/edit/<string:recipe_id>', methods=['GET', 'POST'])
def edit(recipe_id):
    if not get_current_user():
        flash("Please log in or sign up to edit recipes.", "warning")
        return redirect(url_for('login'))
    recipe = get_recipe_by_id(recipe_id)
    if not recipe:
        flash("Recipe not found!", "danger")
        return redirect(url_for('home'))
    if recipe.get('owner_id') != get_current_user()['id']:
        flash("You do not have permission to edit this recipe.", "danger")
        return redirect(url_for('home'))

    if request.method == 'POST':
        try:
            rating = int(request.form.get('rating', 5))
            if not 1 <= rating <= 5:
                raise ValueError

            recipe['name'] = request.form.get('name', '').strip()
            recipe['category'] = request.form.get('category', '').strip()
            recipe['rating'] = rating
            recipe['image_url'] = request.form.get('image_url', '').strip()
            recipe['ingredients'] = request.form.get('ingredients', '').strip()
            recipe['instructions'] = request.form.get('instructions', '').strip()

            update_recipe_in_db(recipe)
            flash("Recipe updated successfully!", "success")
            return redirect(url_for('home'))
        except ValueError:
            flash("Rating must be a number between 1 and 5.", "danger")
        except Exception:
            flash("Something went wrong while updating the recipe.", "danger")
    return render_template('edit_recipe.html', recipe=recipe, current_user=get_current_user())


@app.route('/delete/<string:recipe_id>', methods=['POST'])
def delete(recipe_id):
    try:
        if not get_current_user():
            return jsonify({"success": False, "message": "Login required"}), 401
        recipe = get_recipe_by_id(recipe_id)
        if not recipe or recipe.get('owner_id') != get_current_user()['id']:
            return jsonify({"success": False, "message": "Forbidden"}), 403
        cur = get_db().cursor()
        cur.execute('DELETE FROM recipes WHERE id=?', (recipe_id,))
        if cur.rowcount:
            get_db().commit()
            return jsonify({"success": True, "message": "Recipe deleted."})
        else:
            return jsonify({"success": False, "message": "Recipe not found."}), 404
    except Exception:
        return jsonify({"success": False, "message": "Error deleting recipe."}), 500


# --- 4. AUTH + HISTORY ROUTES ---


def get_current_user():
    uid = session.get('user_id')
    if not uid:
        return None
    cur = get_db().cursor()
    cur.execute('SELECT id, username FROM users WHERE id=?', (uid,))
    row = cur.fetchone()
    return {'id': row['id'], 'username': row['username']} if row else None


def generate_captcha():
    a = random.randint(1, 9)
    b = random.randint(1, 9)
    session['captcha_answer'] = str(a + b)
    return f"{a} + {b} = ?"


def password_requirements(password):
    reqs = {
        'length': len(password) >= 8,
        'uppercase': bool(re.search(r'[A-Z]', password)),
        'lowercase': bool(re.search(r'[a-z]', password)),
        'digit': bool(re.search(r'\d', password)),
        'symbol': bool(re.search(r'[^A-Za-z0-9]', password)),
    }
    return reqs


def password_is_strong(password):
    reqs = password_requirements(password)
    return all(reqs.values()), reqs


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        captcha_input = request.form.get('captcha', '').strip()
        if captcha_input != session.get('captcha_answer'):
            flash('Captcha incorrect.', 'danger')
            return redirect(url_for('signup'))
        if not username or not password:
            flash('Username and password are required.', 'danger')
            return redirect(url_for('signup'))
        ok, reqs = password_is_strong(password)
        if not ok:
            messages = []
            if not reqs['length']:
                messages.append('At least 8 characters.')
            if not reqs['uppercase']:
                messages.append('Include an uppercase letter.')
            if not reqs['lowercase']:
                messages.append('Include a lowercase letter.')
            if not reqs['digit']:
                messages.append('Include a digit.')
            if not reqs['symbol']:
                messages.append('Include a symbol.')
            flash('Weak password: ' + ' '.join(messages), 'danger')
            return redirect(url_for('signup'))
        try:
            cur = get_db().cursor()
            cur.execute('INSERT INTO users (username, password_hash) VALUES (?,?)', (username, generate_password_hash(password)))
            get_db().commit()
            flash('Account created. Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception:
            flash('Username already taken or error creating account.', 'danger')
    captcha_question = generate_captcha()
    return render_template('signup.html', current_user=get_current_user(), captcha_question=captcha_question)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        captcha_input = request.form.get('captcha', '').strip()
        if captcha_input != session.get('captcha_answer'):
            flash('Captcha incorrect.', 'danger')
            return redirect(url_for('login'))
        cur = get_db().cursor()
        cur.execute('SELECT id, password_hash FROM users WHERE username=?', (username,))
        row = cur.fetchone()
        if row and check_password_hash(row['password_hash'], password):
            session['user_id'] = row['id']
            session['username'] = username
            session['accepted_welcome'] = True
            session['boot_id'] = APP_BOOT_ID

            # 👇 NEW: Set flags TO SHOW CHEF ON NEXT PAGE LOAD
            session['show_chef'] = True          # <--- THIS IS KEY
            session['chef_tip']  = random.choice(COOKING_TIPS)  # store random tip

            flash('Logged in successfully.', 'success')
            return redirect(url_for('home'))
    captcha_question = generate_captcha()
    return render_template('login.html', current_user=get_current_user(), captcha_question=captcha_question)


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('guest', None)
    session.pop('accepted_welcome', None)
    session.pop('boot_id', None)
    flash('Signed out.', 'info')
    return redirect(url_for('welcome'))

@app.route('/welcome')
def welcome():
    return render_template('welcome.html', current_user=get_current_user())

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
        flash('Please log in or sign up to view your search history.', 'warning')
        return redirect(url_for('login'))
    cur = get_db().cursor()
    cur.execute('SELECT query, timestamp FROM search_history WHERE user_id=? ORDER BY timestamp DESC', (user['id'],))
    rows = cur.fetchall()
    return render_template('history.html', history=rows, current_user=user)

if __name__ == '__main__':
    # CREATE APPLICATION CONTEXT BEFORE INITIALIZING DB
    with app.app_context():
        init_db()           # ✅ now has app context
        migrate_json_to_db() # ✅ now has app context
    app.run(debug=True)
## lolo
