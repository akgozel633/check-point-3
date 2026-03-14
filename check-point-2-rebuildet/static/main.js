/**
 * Handles the "Heart" toggle for favorites without refreshing the page.
 * @param {HTMLElement} element - The heart container div clicked.
 * @param {string} recipeId - The unique ID of the recipe from the database.
 */
async function toggleFavorite(element, recipeId) {
    const icon = element.querySelector('i');
    if (!icon) return;

    // Optimistic UI update: toggle heart appearance immediately
    const willBeFavorite = icon.classList.toggle('fa-solid');
    icon.classList.toggle('fa-regular');
    icon.classList.toggle('active');

    try {
        const response = await fetch(`/toggle_favorite/${recipeId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ favorite: willBeFavorite })
        });

        if (!response.ok) {
            throw new Error(`Server responded with ${response.status}`);
        }

        console.log(`Favorite toggled for ${recipeId} → ${willBeFavorite}`);
    } catch (error) {
        console.error('Failed to toggle favorite:', error);
        // Revert UI on failure
        icon.classList.toggle('fa-solid');
        icon.classList.toggle('fa-regular');
        icon.classList.toggle('active');
        showToast("Could not update favorite. Please try again.", "error");
    }
}

/**
 * Deletes a recipe via AJAX without page reload.
 * @param {string} recipeId - The recipe's unique ID
 * @param {HTMLElement} button - The delete button element
 */
async function deleteRecipe(recipeId, button) {
    if (!confirm("Are you sure you want to delete this recipe?")) {
        return;
    }

    // Show loading state
    const originalContent = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Deleting...';

    try {
        const response = await fetch(`/delete/${recipeId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const data = await response.json();

        if (data.success) {
            // Find the recipe card and animate removal
            const card = button.closest('.recipe-card');
            if (card) {
                card.classList.add('removing');
                setTimeout(() => card.remove(), 400); // match CSS transition duration
            }
            showToast(data.message || "Recipe deleted successfully", "success");
        } else {
            showToast(data.message || "Recipe not found", "error");
        }
    } catch (error) {
        console.error('Delete failed:', error);
        showToast("Network error — could not delete recipe", "error");
    } finally {
        // Reset button
        button.disabled = false;
        button.innerHTML = originalContent;
    }
}

/**
 * Shows a temporary toast notification.
 * @param {string} message - Text to display
 * @param {"success"|"error"} type - Style of the toast
 */
function showToast(message, type = "success") {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);

    // Auto-remove after 3 seconds
    setTimeout(() => {
        toast.classList.add('fade-out');
        setTimeout(() => toast.remove(), 500);
    }, 3000);
}

// --- AUTO-HIDE FLASH MESSAGES (kept from original) ---
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.alert').forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transform = 'translateX(-50%) translateY(-20px)';
            setTimeout(() => alert.remove(), 500);
        }, 3000);
    });

    const pwdInput = document.getElementById('signup-password');
    if (pwdInput) {
        const meterBar = document.getElementById('signup-meter-bar');
        const hintsRoot = document.getElementById('signup-hints');
        const toggle = document.getElementById('signup-show');
        const calcReqs = (pwd) => {
            return {
                length: pwd.length >= 8,
                uppercase: /[A-Z]/.test(pwd),
                lowercase: /[a-z]/.test(pwd),
                digit: /\d/.test(pwd),
                symbol: /[^A-Za-z0-9]/.test(pwd),
            };
        };
        const updateHints = (reqs) => {
            if (!hintsRoot) return;
            ['length','uppercase','lowercase','digit','symbol'].forEach(key => {
                const li = hintsRoot.querySelector(`li[data-req="${key}"]`);
                if (li) {
                    li.classList.toggle('ok', !!reqs[key]);
                }
            });
        };
        const updateMeter = (reqs) => {
            const score = Object.values(reqs).filter(Boolean).length; // 0..5
            const pct = (score / 5) * 100;
            meterBar.style.width = `${pct}%`;
            meterBar.style.background = score <= 2 ? '#dc3545' : (score === 3 ? '#ffc107' : '#28a745');
        };
        const refresh = () => {
            const reqs = calcReqs(pwdInput.value || '');
            updateHints(reqs);
            updateMeter(reqs);
        };
        pwdInput.addEventListener('input', refresh);
        if (toggle) {
            toggle.addEventListener('change', () => {
                pwdInput.type = toggle.checked ? 'text' : 'password';
            });
        }
        refresh();
    }
    const loginPwd = document.getElementById('login-password');
    const loginToggle = document.getElementById('login-show');
    if (loginPwd && loginToggle) {
        loginToggle.addEventListener('change', () => {
            loginPwd.type = loginToggle.checked ? 'text' : 'password';
        });
    }
});
