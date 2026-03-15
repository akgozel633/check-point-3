## I have put here some comment but in app.py clear code without """..."""

import json
import os
import urllib.request
import urllib.parse
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from uuid import uuid4

app = Flask(__name__)
app.secret_key = "recipe_pro_ultra_secret_2026"
DATA_FILE = 'recipes.json'

# --- 1. DATABASE HELPERS ---

def load_recipes():
    """Safely loads the JSON database."""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

def save_recipes(recipes):
    """Safely saves the list to the JSON database."""
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(recipes, f, indent=4)
    except IOError:
        flash("System Error: Could not save to database.", "danger")

def fetch_from_mealdb(url):
    """Makes a GET request to TheMealDB API and returns the JSON data (or None if it fails)."""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None

# --- 2. MAIN ROUTES ---

@app.route('/')
def home():
    """Displays all recipes on the dashboard."""
    return render_template('index.html', recipes=load_recipes())

@app.route('/recipe/<string:recipe_id>')
def view_recipe(recipe_id):
    """Shows full details for a single recipe."""
    recipes = load_recipes()
    recipe = next((r for r in recipes if r['id'] == recipe_id), None)
    if recipe:
        return render_template('recipe_detail.html', recipe=recipe)
    flash("Recipe not found!", "warning")
    return redirect(url_for('home'))

@app.route('/toggle_favorite/<string:recipe_id>', methods=['POST'])
def toggle_favorite(recipe_id):
    """AJAX: Updates favorite status without page reload."""
    recipes = load_recipes()
    data = request.get_json()
    new_status = data.get('favorite', False)
    
    for r in recipes:
        if r['id'] == recipe_id:
            r['favorite'] = new_status
            break
            
    save_recipes(recipes)
    return jsonify({"status": "success", "new_val": new_status})

# --- 3. ONLINE SEARCH & WEB IMPORT ---

@app.route('/search', methods=['GET', 'POST'])
def search_online():
    """Connects to TheMealDB API to find recipes."""
    results = []
    query = ""
    if request.method == 'POST':
        query = request.form.get('search_query', '').strip()
        if query:
            url = f"https://www.themealdb.com/api/json/v1/1/search.php?s={urllib.parse.quote(query)}"
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as resp:
                    data = json.loads(resp.read().decode())
                    results = data.get('meals') or []
            except Exception:
                flash("Connection error: Online search unavailable.", "danger")
                
    return render_template('search.html', results=results, query=query)



""" this code was first 
@app.route('/save_online/<string:meal_id>', methods=['POST'])
def save_online(meal_id):

    url = f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={meal_id}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp:
            meal = json.loads(resp.read().decode())['meals'][0]

            # Parse ingredients into a clean list
            ingredients_list = []
            for i in range(1, 21):
                ing = meal.get(f'strIngredient{i}')
                meas = meal.get(f'strMeasure{i}')
                if ing and ing.strip():
                    ingredients_list.append(f"{meas.strip() if meas else ''} {ing.strip()}".strip())
            
            recipes = load_recipes()
            new_recipe = {
                "id": str(uuid4()),
                "name": meal.get('strMeal'),
                "category": meal.get('strCategory', 'Web'),
                "rating": 5,
                "image_url": meal.get('strMealThumb'),
                "ingredients": "\n".join(ingredients_list),
                "instructions": meal.get('strInstructions', ''),
                "favorite": False
            }
            recipes.append(new_recipe)
            save_recipes(recipes)
            flash(f"'{new_recipe['name']}' added to your collection!", "success")
    except Exception:
        flash("Failed to import recipe.", "danger")
    
    return redirect(url_for('home'))
"""

#old one Fetches raw meal data from TheMealDB API.

"""
def fetch_meal_from_api(meal_id):
    url = f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={meal_id}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        return data['meals'][0]
"""

#new instd of fetch_meal_from_api

def fetch_meal_from_api(meal_id):
    """Fetches one meal by ID using the shared helper."""
    url = f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={meal_id}"
    data = fetch_from_mealdb(url)
    return data['meals'][0] if data and data.get('meals') else None


def get_recipe_by_id(recipe_id):
    """Retrieves a recipe by ID from the database."""
    recipes = load_recipes()
    return next((r for r in recipes if r['id'] == recipe_id), None)

def parse_ingredients(meal):
    """Extracts and cleans ingredients into a list."""
    ingredients_list = []
    for i in range(1, 21):
        ing = meal.get(f'strIngredient{i}')
        meas = meal.get(f'strMeasure{i}')
        if ing and ing.strip():
            ingredients_list.append(f"{meas.strip() if meas else ''} {ing.strip()}".strip())
    return ingredients_list


def build_recipe_from_meal(meal):
    """Builds a clean recipe dictionary from the API meal data."""
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

@app.route('/save_online/<string:meal_id>', methods=['POST'])
def save_online(meal_id):
    """Imports a recipe from the web into your local JSON."""
    try:
        meal = fetch_meal_from_api(meal_id)
        new_recipe = build_recipe_from_meal(meal)
        
        recipes = load_recipes()
        recipes.append(new_recipe)
        save_recipes(recipes)
        
        flash(f"'{new_recipe['name']}' added to your collection!", "success")
    
    except Exception:
        flash("Failed to import recipe.", "danger")
    
    return redirect(url_for('home'))

# --- 4. CREATE, EDIT, & DELETE ---
"""we can add here try exept but it becomes too much
@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        recipes = load_recipes()
        # Create a new dictionary from the form
        new_entry = {
            "id": str(uuid4()),
            "name": request.form.get('name', 'Untitled'),
            "category": request.form.get('category', 'Other'),
            "rating": int(request.form.get('rating', 5)),
            "image_url": request.form.get('image_url', ''),
            "ingredients": request.form.get('ingredients', ''),
            "instructions": request.form.get('instructions', ''),
            "favorite": False
        }
        recipes.append(new_entry)
        save_recipes(recipes)
        flash("Recipe created!", "success")
        return redirect(url_for('home'))
    return render_template('add_recipe.html')
"""
@app.route('/create', methods=['GET', 'POST'])
def create():
    """Manual recipe entry."""
    if request.method == 'POST':
        try:
            recipes = load_recipes()
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
            recipes.append(new_entry)
            save_recipes(recipes)
            flash("Recipe created successfully!", "success")
            return redirect(url_for('home'))
        except ValueError:
            flash("Rating must be a number between 1 and 5.", "danger")
        except Exception:
            flash("Something went wrong while creating the recipe.", "danger")
    return render_template('add_recipe.html')

"""we can add here try exept but it ALSO becomes too much
@app.route('/edit/<string:recipe_id>', methods=['GET', 'POST'])
def edit(recipe_id):
    recipes = load_recipes()
    recipe = next((r for r in recipes if r['id'] == recipe_id), None)

    if not recipe:
        flash("Recipe not found!", "danger")
        return redirect(url_for('home'))

    if request.method == 'POST':
        recipe['name'] = request.form.get('name')
        recipe['category'] = request.form.get('category')
        recipe['rating'] = int(request.form.get('rating', 5))
        recipe['image_url'] = request.form.get('image_url')
        recipe['ingredients'] = request.form.get('ingredients')
        recipe['instructions'] = request.form.get('instructions')
        save_recipes(recipes)
        flash("Recipe updated!", "success")
        return redirect(url_for('home'))
    
    return render_template('edit_recipe.html', recipe=recipe)
"""
@app.route('/edit/<string:recipe_id>', methods=['GET', 'POST'])
def edit(recipe_id):
    """Update an existing recipe."""
    recipe = get_recipe_by_id(recipe_id)   # ← using the helper we created earlier

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

            save_recipes(load_recipes())  # safe save
            flash("Recipe updated successfully!", "success")
            return redirect(url_for('home'))
        except ValueError:
            flash("Rating must be a number between 1 and 5.", "danger")
        except Exception:
            flash("Something went wrong while updating the recipe.", "danger")
    
    return render_template('edit_recipe.html', recipe=recipe)

@app.route('/delete/<string:recipe_id>')
def delete(recipe_id):
    """Removes a recipe from the list."""
    recipes = load_recipes()
    original_len = len(recipes)
    recipes = [r for r in recipes if r['id'] != recipe_id]
    
    if len(recipes) < original_len:
        save_recipes(recipes)
        flash("Recipe deleted.", "info")
    return redirect(url_for('home'))

# --- START THE APP ---
if __name__ == '__main__':
    app.run(debug=True)

# --------------------------------------------------------------------------------------------------------
# ------------------------------------Database Design Questions-------------------------------------------
# --------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------

## Database Design Questions

* Why did you choose these data types? (TEXT vs INTEGER)
  TEXT for strings like id , name, category, image_url, ingredients, instructions — they can be long. INTEGER for rating (small number) and favorite . This keeps it simple, efficient, and matches JSON types without data loss.

* Do you have any list fields? How will you store them in SQL?
  Yes, "ingredients" is a list (newline-separated in JSON). Stored as TEXT with \n separators to keep it simple/no changes needed. Later, could split to separate table for better search (e.g., query by ingredient).

* Would you benefit from multiple tables? ---

* What queries would you run most often? (e.g., "show all incomplete tasks")
  - SELECT * FROM recipes ORDER BY name;  (Show all on home)
  - SELECT * FROM recipes WHERE id = 'uuid';  (View/edit single)
  - UPDATE recipes SET favorite = 1 WHERE id = 'uuid';  (Toggle favorite)
  - DELETE FROM recipes WHERE id = 'uuid';  (Delete)
  - SELECT * FROM recipes WHERE favorite = 1;  (Show favorites)
  - INSERT INTO recipes (...) VALUES (...);  (Add new)