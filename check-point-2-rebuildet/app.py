import json
import os
import urllib.request
import urllib.parse
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, g, session
from uuid import uuid4
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "recipe_pro_ultra_secret_2026"
DATA_FILE = 'recipes.json'
DATABASE = 'recipes.db'


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
        'favorite': bool(row['favorite'])
    }


def load_recipes():
    cur = get_db().cursor()
    cur.execute('SELECT * FROM recipes ORDER BY name COLLATE NOCASE')
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
        "INSERT INTO recipes (id, name, category, rating, image_url, ingredients, instructions, favorite) VALUES (?,?,?,?,?,?,?,?)",
        (recipe['id'], recipe['name'], recipe['category'], recipe['rating'], recipe['image_url'], recipe['ingredients'], recipe['instructions'], 1 if recipe.get('favorite') else 0)
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


# --- 3. MAIN ROUTES ---


@app.route('/')
def home():
    """Displays all recipes on the dashboard."""
    return render_template('index.html', recipes=load_recipes(), current_user=get_current_user())


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
        recipe = get_recipe_by_id(recipe_id)
        if not recipe:
            return jsonify({"status": "error", "message": "Recipe not found"})

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
    if request.method == 'POST':
        query = request.form.get('search_query', '').strip()
        if query:
            url = f"https://www.themealdb.com/api/json/v1/1/search.php?s={urllib.parse.quote(query)}"
            data = fetch_from_mealdb(url)
            results = data.get('meals') or [] if data else []
            if not data:
                flash("Connection error: Online search unavailable.", "danger")
            # record history
            try:
                user = get_current_user()
                cur = get_db().cursor()
                cur.execute('INSERT INTO search_history (user_id, query) VALUES (?,?)', (user['id'] if user else None, query))
                get_db().commit()
            except Exception:
                pass
    return render_template('search.html', results=results, query=query, current_user=get_current_user())


@app.route('/save_online/<string:meal_id>', methods=['POST'])
def save_online(meal_id):
    try:
        meal = fetch_meal_from_api(meal_id)
        if meal is None:
            raise ValueError("Meal not found in API.")
        new_recipe = build_recipe_from_meal(meal)
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
                "favorite": False
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
    recipe = get_recipe_by_id(recipe_id)
    if not recipe:
        flash("Recipe not found!", "danger")
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


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if not username or not password:
            flash('Username and password are required.', 'danger')
            return redirect(url_for('signup'))
        try:
            cur = get_db().cursor()
            cur.execute('INSERT INTO users (username, password_hash) VALUES (?,?)', (username, generate_password_hash(password)))
            get_db().commit()
            flash('Account created. Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception:
            flash('Username already taken or error creating account.', 'danger')
    return render_template('signup.html', current_user=get_current_user())


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        cur = get_db().cursor()
        cur.execute('SELECT id, password_hash FROM users WHERE username=?', (username,))
        row = cur.fetchone()
        if row and check_password_hash(row['password_hash'], password):
            session['user_id'] = row['id']
            session['username'] = username
            flash('Logged in successfully.', 'success')
            return redirect(url_for('home'))
        flash('Invalid credentials.', 'danger')
    return render_template('login.html', current_user=get_current_user())


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Signed out.', 'info')
    return redirect(url_for('home'))


@app.route('/history')
def history():
    user = get_current_user()
    if not user:
        flash('Please log in to view your search history.', 'warning')
        return redirect(url_for('login'))
    cur = get_db().cursor()
    cur.execute('SELECT query, timestamp FROM search_history WHERE user_id=? ORDER BY timestamp DESC', (user['id'],))
    rows = cur.fetchall()
    return render_template('history.html', history=rows, current_user=user)


if __name__ == '__main__':
    with app.app_context():
        init_db()
        migrate_json_to_db()
    app.run(debug=True)
## lolo