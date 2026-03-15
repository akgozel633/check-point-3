# 📝 CHANGES.md — Full Change Log

This file describes all modifications made to implement the feature:  
**“Chef appears ONLY after login (right-side sidebar, full size, with cooking tip)”**

## Added filter and search functions
---

## ✅ 1. Python Changes (`app.py`)

### 1.1 Added cooking tips list

At the top of `app.py` (after imports):

```python
COOKING_TIPS = [
    "⚡ Always prep ALL ingredients before turning on the heat (mise en place)!",
    "🧂 Season as you go — don’t wait until the end!",
    "🥩 Let meat rest 5‑10 min after cooking so juices stay inside.",
    "🔪 Keep your knives sharp — a dull knife is dangerous!",
    "🌶️ Toast whole spices for 30 sec before grinding for MAX flavor.",
    "🥚 Use room‑temperature eggs for better emulsification (e.g., hollandaise).",
    "🍳 Never crowd the pan — it steams food instead of searing it!",
    "🍞 Brush baked goods with milk or egg wash for a golden crust.",
    "🥦 Blanch vegetables in salted boiling water for vibrant colour.",
    "🧈 Add butter OFF the heat to sauces — it won’t break!"
]
```

### 1.2 Modified `login()` route

Inside the `login()` route, after successful authentication:

```python
if row and check_password_hash(row['password_hash'], password):
    session['user_id']   = row['id']
    session['username']  = username
    session['accepted_welcome'] = True
    session['boot_id']   = APP_BOOT_ID

    # 👇 NEW: show chef on next page load
    session['show_chef'] = True
    session['chef_tip']  = random.choice(COOKING_TIPS)

    flash('Logged in successfully.', 'success')
    return redirect(url_for('home'))
```

### 1.3 Added `/clear-chef-flag` endpoint

Added this route **before** `if __name__ == '__main__':`:

```python
from flask import jsonify  # if not already imported

@app.route('/clear-chef-flag', methods=['POST'])
def clear_chef_flag():
    session.pop('show_chef', None)
    session.pop('chef_tip',  None)
    return jsonify(success=True)
```

---

## ✅ 2. HTML/Template Changes (`templates/base.html`)

### 2.1 Added chef sidebar (conditional)

Placed **just before `</body>`** in `base.html`:

```html
{% if session.show_chef %}
<div id="chef-sidebar" class="chef-sidebar">
    <div class="chef-inner">
        <img src="https://images.unsplash.com/photo-1504674900247-0877df9cc836?q=80&w=1000" 
             alt="Chef" class="chef-img">

        <div class="chef-quote">
            <h4>📝 Chef’s Pro Tip</h4>
            <p>{{ session.chef_tip }}</p>
        </div>

        <button id="close-chef" class="btn btn-sm btn-outline-dark">✕ Close</button>
    </div>
</div>

<style>
.chef-sidebar {
    position: fixed;
    top: 0;
    right: 0;
    height: 100vh;
    width: 420px;
    background: #fff;
    box-shadow: -12px 0 30px rgba(0,0,0,0.25);
    z-index: 9999;
    padding: 2rem;
    overflow-y: auto;
    transform: translateX(100%);
    transition: transform 0.5s ease-in-out;
}

.chef-sidebar.active {
    transform: translateX(0);
}

.chef-img {
    width: 180px;
    height: 180px;
    border-radius: 50%;
    object-fit: cover;
    margin: 0 auto 2rem;
    display: block;
    border: 4px solid #ffeeba;
}

.chef-quote {
    text-align: center;
    font-size: 1.2rem;
    line-height: 1.7;
    color: #222;
}

.chef-quote h4 {
    color: #d9480f;
    margin-bottom: 1rem;
}

#close-chef {
    position: absolute;
    top: 1rem;
    right: 1rem;
    padding: 0.3rem 0.8rem;
}
</style>

<script>
document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.getElementById('chef-sidebar');
    const closeBtn = document.getElementById('close-chef');

    sidebar.classList.add('active');

    closeBtn.addEventListener('click', () => {
        sidebar.classList.remove('active');

        fetch("{{ url_for('clear_chef_flag') }}", {
            method: 'POST',
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .catch(e => console.error("Error clearing chef flag", e));
    });
});
</script>
{% endif %}
```

---

## ✅ 3. Behavior Summary

| Step | Behavior |
| --- | --- |
| User logs in | `session['show_chef'] = True` and a random tip is stored |
| Next page loads | Sidebar slides in from right, full height |
| User closes sidebar | Session flags removed → chef never appears again until next login |

---

## ✅ 4. Restart Requirement

After making these changes, restart the Flask app:

```bash
python app.py
```

---

## 🎯 Result

✔ Chef appears **only once after login**  
✔ Full-height, right-side sidebar  
✔ Random cooking tip displayed  
✔ Closing the sidebar makes it disappear forever until next login