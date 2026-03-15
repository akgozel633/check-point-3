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

    // --- Password Strength Validation for Signup ---
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirmPassword');
    const passwordToggle = document.getElementById('passwordToggle');
    const strengthFill = document.getElementById('strengthFill');
    const strengthText = document.getElementById('strengthText');
    const passwordRequirements = document.getElementById('passwordRequirements');
    const passwordMatch = document.getElementById('passwordMatch');
    const matchText = document.getElementById('matchText');
    const submitBtn = document.getElementById('submitBtn');
    const signupForm = document.getElementById('signupForm');

    if (passwordInput && signupForm) {
        // Password visibility toggle
        if (passwordToggle) {
            passwordToggle.addEventListener('click', () => {
                const type = passwordInput.type === 'password' ? 'text' : 'password';
                passwordInput.type = type;
                
                // Update icon
                const icon = passwordToggle.querySelector('i');
                if (type === 'text') {
                    icon.classList.remove('fa-eye');
                    icon.classList.add('fa-eye-slash');
                    passwordToggle.setAttribute('title', 'Hide password');
                } else {
                    icon.classList.remove('fa-eye-slash');
                    icon.classList.add('fa-eye');
                    passwordToggle.setAttribute('title', 'Show password');
                }
            });
        }
        // Password strength checker function (mirrors backend logic)
        function checkPasswordStrength(password) {
            const requirements = {
                length: password.length >= 8,
                uppercase: /[A-Z]/.test(password),
                lowercase: /[a-z]/.test(password),
                number: /\d/.test(password),
                special: /[!@#$%^&*(),.?":{}|<>]/.test(password)
            };
            
            const score = Object.values(requirements).filter(Boolean).length;
            const isStrong = score >= 4;
            
            return { requirements, score, isStrong };
        }

        // Update password strength UI
        function updatePasswordStrength(password) {
            const { requirements, score, isStrong } = checkPasswordStrength(password);
            
            // Update strength bar
            strengthFill.className = 'password-strength-fill';
            strengthText.className = 'password-strength-text';
            
            if (score === 0) {
                strengthText.textContent = 'Enter a password';
            } else if (score === 1) {
                strengthFill.classList.add('weak');
                strengthText.classList.add('weak');
                strengthText.textContent = 'Weak password';
            } else if (score === 2) {
                strengthFill.classList.add('fair');
                strengthText.classList.add('fair');
                strengthText.textContent = 'Fair password';
            } else if (score === 3) {
                strengthFill.classList.add('good');
                strengthText.classList.add('good');
                strengthText.textContent = 'Good password';
            } else if (score === 4) {
                strengthFill.classList.add('strong');
                strengthText.classList.add('strong');
                strengthText.textContent = 'Strong password';
            } else {
                strengthFill.classList.add('very-strong');
                strengthText.classList.add('very-strong');
                strengthText.textContent = 'Very strong password';
            }
            
            // Update requirements list
            Object.keys(requirements).forEach(req => {
                const reqElement = passwordRequirements.querySelector(`[data-requirement="${req}"]`);
                if (reqElement) {
                    if (requirements[req]) {
                        reqElement.classList.add('met');
                    } else {
                        reqElement.classList.remove('met');
                    }
                }
            });
            
            // Update password input validation style
            if (password.length > 0) {
                passwordInput.classList.toggle('valid', isStrong);
                passwordInput.classList.toggle('invalid', !isStrong);
            } else {
                passwordInput.classList.remove('valid', 'invalid');
            }
            
            return isStrong;
        }

        // Update password match UI
        function updatePasswordMatch() {
            const password = passwordInput.value;
            const confirmPassword = confirmPasswordInput.value;
            
            if (confirmPassword.length === 0) {
                passwordMatch.classList.remove('match');
                confirmPasswordInput.classList.remove('valid', 'invalid');
                return false;
            }
            
            const isMatch = password === confirmPassword;
            passwordMatch.classList.toggle('match', isMatch);
            matchText.textContent = isMatch ? 'Passwords match' : 'Passwords do not match';
            
            confirmPasswordInput.classList.toggle('valid', isMatch);
            confirmPasswordInput.classList.toggle('invalid', !isMatch);
            
            return isMatch;
        }

        // Form validation
        function validateForm() {
            const password = passwordInput.value;
            const confirmPassword = confirmPasswordInput.value;
            const username = signupForm.querySelector('input[name="username"]').value;
            const captcha = signupForm.querySelector('input[name="captcha"]').value;
            
            const { isStrong: isPasswordStrong } = checkPasswordStrength(password);
            const isPasswordMatch = password === confirmPassword && confirmPassword.length > 0;
            
            // Update password match UI
            if (confirmPassword.length > 0) {
                passwordMatch.classList.toggle('match', isPasswordMatch);
                matchText.textContent = isPasswordMatch ? 'Passwords match' : 'Passwords do not match';
                confirmPasswordInput.classList.toggle('valid', isPasswordMatch);
                confirmPasswordInput.classList.toggle('invalid', !isPasswordMatch);
            }
            
            // Enable/disable submit button
            const isValid = username.length > 0 && 
                           password.length > 0 && 
                           confirmPassword.length > 0 && 
                           isPasswordStrong && 
                           isPasswordMatch && 
                           captcha.length > 0;
            
            submitBtn.disabled = !isValid;
            submitBtn.style.opacity = isValid ? '1' : '0.6';
            
            return isValid;
        }

        // Event listeners
        passwordInput.addEventListener('input', () => {
            updatePasswordStrength(passwordInput.value);
            if (confirmPasswordInput.value) {
                const isMatch = passwordInput.value === confirmPasswordInput.value;
                passwordMatch.classList.toggle('match', isMatch);
                matchText.textContent = isMatch ? 'Passwords match' : 'Passwords do not match';
                confirmPasswordInput.classList.toggle('valid', isMatch);
                confirmPasswordInput.classList.toggle('invalid', !isMatch);
            }
            validateForm();
        });

        confirmPasswordInput.addEventListener('input', () => {
            const isMatch = passwordInput.value === confirmPasswordInput.value && confirmPasswordInput.value.length > 0;
            passwordMatch.classList.toggle('match', isMatch);
            matchText.textContent = isMatch ? 'Passwords match' : 'Passwords do not match';
            confirmPasswordInput.classList.toggle('valid', isMatch);
            confirmPasswordInput.classList.toggle('invalid', !isMatch);
            validateForm();
        });

        // Add input listeners for all form fields
        signupForm.querySelectorAll('input').forEach(input => {
            input.addEventListener('input', validateForm);
        });

        // Prevent form submission if validation fails
        signupForm.addEventListener('submit', (e) => {
            if (!validateForm()) {
                e.preventDefault();
                // Show error message
                const errorDiv = document.createElement('div');
                errorDiv.className = 'alert alert-danger';
                errorDiv.textContent = 'Please fix all validation errors before submitting.';
                errorDiv.style.position = 'relative';
                errorDiv.style.top = '0';
                errorDiv.style.transform = 'none';
                signupForm.insertBefore(errorDiv, signupForm.firstChild);
                
                setTimeout(() => errorDiv.remove(), 5000);
            }
        });

        // Initial validation
        validateForm();
    }

    const loginPwd = document.getElementById('login-password');
    const loginToggle = document.getElementById('login-show');
    if (loginPwd && loginToggle) {
        loginToggle.addEventListener('change', () => {
            loginPwd.type = loginToggle.checked ? 'text' : 'password';
        });
    }

    // --- AI Helper Animation & Close ---
    const helper = document.getElementById('ai-helper');
    const closeBtn = document.querySelector('.ai-close');
    const message = helper ? helper.querySelector('.ai-message p') : null;

    // функция печати текста
    function typeText(element, text, speed = 50) {
        element.textContent = "";
        let i = 0;
        const interval = setInterval(() => {
            element.textContent += text[i];
            i++;
            if (i >= text.length) {
                clearInterval(interval);
            }
        }, speed);
    }

    // показываем только на welcome.html и если не закрыт в текущей сессии
    if (helper && window.location.pathname.includes("welcome") && !sessionStorage.getItem('helperClosed')) {
        setTimeout(() => {
            helper.classList.add('show');
            if (message) {
                typeText(message, "Welcome to RecipeLog Pro! 🍳 Here you can save, search, and manage your favorite recipes with ease.", 40);
            }
        }, 1500); // появится через 1.5 секунды
    }

    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            helper.classList.remove('show');
            sessionStorage.setItem('helperClosed', 'true'); // запоминаем только на время текущей сессии
        });
    }
});
