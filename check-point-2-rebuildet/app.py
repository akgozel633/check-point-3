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

def get_recipe_by_id(recipe_id):
    """Retrieves a recipe by ID from the database."""
    recipes = load_recipes()
    return next((r for r in recipes if r['id'] == recipe_id), None)

def fetch_meal_from_api(meal_id):
    """Fetches one meal by ID using the shared helper."""
    url = f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={meal_id}"
    data = fetch_from_mealdb(url)
    return data['meals'][0] if data and data.get('meals') else None

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

# --- 2. MAIN ROUTES ---

@app.route('/')
def home():
    """Displays all recipes on the dashboard."""
    return render_template('index.html', recipes=load_recipes())

@app.route('/recipe/<string:recipe_id>')
def view_recipe(recipe_id):
    """Shows full details for a single recipe."""
    recipe = get_recipe_by_id(recipe_id)
    if recipe:
        return render_template('recipe_detail.html', recipe=recipe)
    flash("Recipe not found!", "warning")
    return redirect(url_for('home'))

@app.route('/toggle_favorite/<string:recipe_id>', methods=['POST'])
def toggle_favorite(recipe_id):
    """AJAX: Updates favorite status without page reload."""
    try:
        recipe = get_recipe_by_id(recipe_id)
        if not recipe:
            return jsonify({"status": "error", "message": "Recipe not found"})

        data = request.get_json()
        new_status = data.get('favorite', False)
        
        recipe['favorite'] = new_status
        save_recipes(load_recipes())
        return jsonify({"status": "success", "new_val": new_status})
    except Exception:
        return jsonify({"status": "error", "message": "Failed to update favorite. Try again."})

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
            data = fetch_from_mealdb(url)
            results = data.get('meals') or [] if data else []
            if not data:
                flash("Connection error: Online search unavailable.", "danger")
                
    return render_template('search.html', results=results, query=query)

@app.route('/save_online/<string:meal_id>', methods=['POST'])
def save_online(meal_id):
    """Imports a recipe from the web into your local JSON."""
    try:
        meal = fetch_meal_from_api(meal_id)
        if meal is None:
            raise ValueError("Meal not found in API.")
        new_recipe = build_recipe_from_meal(meal)
        
        recipes = load_recipes()
        recipes.append(new_recipe)
        save_recipes(recipes)
        
        flash(f"'{new_recipe['name']}' added to your collection!", "success")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception:
        flash("Failed to import recipe.", "danger")
    
    return redirect(url_for('home'))

# --- 4. CREATE, EDIT, & DELETE ---

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

@app.route('/edit/<string:recipe_id>', methods=['GET', 'POST'])
def edit(recipe_id):
    """Update an existing recipe."""
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

            save_recipes(load_recipes())  # safe save
            flash("Recipe updated successfully!", "success")
            return redirect(url_for('home'))
        except ValueError:
            flash("Rating must be a number between 1 and 5.", "danger")
        except Exception:
            flash("Something went wrong while updating the recipe.", "danger")
    
    return render_template('edit_recipe.html', recipe=recipe)

@app.route('/delete/<string:recipe_id>', methods=['POST'])
def delete(recipe_id):
    """AJAX-delete a recipe without reload."""
    try:
        recipes = load_recipes()
        original_len = len(recipes)
        recipes = [r for r in recipes if r['id'] != recipe_id]
        
        if len(recipes) < original_len:
            save_recipes(recipes)
            return jsonify({"success": True, "message": "Recipe deleted."})
        else:
            return jsonify({"success": False, "message": "Recipe not found."}), 404
    except Exception:
        return jsonify({"success": False, "message": "Error deleting recipe."}), 500

# --- START THE APP ---
if __name__ == '__main__':
    app.run(debug=True)