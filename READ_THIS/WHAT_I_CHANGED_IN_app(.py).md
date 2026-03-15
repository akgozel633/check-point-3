##                      Plan A 🙌👍😊👌🫥🫥🫥🫥🫥🫥🥱😶‍🌫️
## Refactored save_online function(❁´◡`❁)

**What I changed:**
Broke 40+ line function into 4 small helpers:
  fetch_meal_from_api()
  parse_ingredients()
  build_recipe_from_meal()
  and added a save_online to collect in json

**Why:** Each function now does ONE thing only. Route went from ~40 lines to ~13 lines

**Hardest part:** Moving the ingredients parsing into its own helper

**Result:** Code is much cleaner and easier to read.

Old code :
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

## I replased to this  :
def fetch_meal_from_api(meal_id):
    """Fetches raw meal data from TheMealDB API."""
    url = f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={meal_id}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        return data['meals'][0]


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

## ------------------------------------------------------------------------------------------------
## Added comprehensive error handling

**What I added:**
   try/except in create(), edit(), toggle_favorite()
   Safe int() conversion for rating with friendly message
   Better flash messages for all errors
   JSON safety in AJAX route

**Result:** App never crashes for the user — always shows helpful messages