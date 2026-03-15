import json
import os
import urllib.request
import urllib.parse
import sqlite3
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

# ---------------- HELPERS ----------------

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

def load_recipes():
    user = get_current_user()
    if not user:
        return []
    cur = get_db().cursor()
    cur.execute('SELECT * FROM recipes WHERE owner_id=? ORDER BY name', (user['id'],))
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
    return render_template('index.html', recipes=load_recipes(), current_user=get_current_user())

# ---------------- SEARCH ----------------

def fetch_from_mealdb(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except:
        return None

@app.route('/search', methods=['GET','POST'])
def search_online():
    results = []
    query = ""
    ingredients = ""

    if request.method == 'POST':
        query = request.form.get('search_query','').strip()
        ingredients = request.form.get('ingredients','').strip()

        if not query and not ingredients:
            flash("Enter a recipe name or ingredient.", "warning")
            return render_template("search.html", results=[], query=query, ingredients=ingredients)

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

        if data and data.get("meals"):
            results = data["meals"]
        else:
            results = []

        # Also include any local recipes (created/saved by the current user)
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

        # Save search history
        try:
            cur = get_db().cursor()
            cur.execute(
                "INSERT INTO search_history (user_id, query) VALUES (?, ?)",
                (user['id'] if user else None, f"{query} {ingredients}".strip())
            )
            get_db().commit()
        except:
            pass

    return render_template("search.html", results=results, query=query, ingredients=ingredients, current_user=get_current_user())

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
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        password = request.form.get('password','')

        if not username or not password:
            flash("Username and password required.", "danger")
            return redirect(url_for('signup'))

        try:
            cur = get_db().cursor()
            cur.execute("INSERT INTO users (username,password_hash) VALUES (?,?)",
                        (username, generate_password_hash(password)))
            get_db().commit()
            flash("Account created! Please log in.", "success")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Username already exists.", "danger")

    return render_template("signup.html", current_user=get_current_user())

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
    cur.execute("SELECT query,timestamp FROM search_history WHERE user_id=? ORDER BY timestamp DESC",
                (user['id'],))
    rows = cur.fetchall()
    return render_template("history.html", history=rows, current_user=user)


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