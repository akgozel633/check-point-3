// EcoMaterial Hub - Main JavaScript
class EcoMaterialHub {
    constructor() {
        this.searchTimeout = null;
        this.searchInput = null;
        this.productGrid = null;
        this.loadingSpinner = null;
        this.categoryFilter = null;
        this.init();

        
    }

    init() {
        this.setupElements();
        this.setupSearch();
        this.setupMobileNav();
        this.setupFlashMessages();
        this.setupFavoriteButtons();
        this.setupCardClicks();
        this.setupEcoButton();
        this.setupSideMenu();
    }

  setupCardClicks() {
    document.addEventListener('click', (e) => {
        const card = e.target.closest('.product-card');
        // Проверяем, что кликнули по карточке, но не по кнопке внутри
        if (card && !e.target.closest('.favorite-btn') && !e.target.closest('.btn')) {
            const productId = card.getAttribute('data-product-id');
            if (productId) {
                window.location.href = `/product/${productId}`;
            }
        }
    });
}

    setupEcoButton() {
        const ecoTips = [
            { tip: "💡 Turn off lights when leaving a room.", reason: "This reduces electricity use and lowers carbon emissions." },
            { tip: "💧 Use reusable water bottles.", reason: "It helps cut down on single-use plastic waste." },
            { tip: "♻️ Recycle paper, glass, and plastic.", reason: "Recycling conserves resources and reduces landfill pollution." },
            { tip: "🌱 Compost food scraps.", reason: "Composting reduces methane emissions from landfills and enriches soil." },
            { tip: "🚶 Walk, bike, or use public transport.", reason: "This lowers greenhouse gas emissions compared to driving." },
            { tip: "🌳 Plant trees.", reason: "Trees absorb CO₂ and improve air quality." },
            { tip: "👕 Avoid fast fashion.", reason: "Sustainable clothing reduces waste and pollution from textile production." },
            { tip: "🥦 Reduce meat consumption.", reason: "Livestock farming produces high greenhouse gas emissions." },
            { tip: "⚡ Use energy-efficient appliances.", reason: "They consume less electricity and save money long-term." },
            { tip: "🌧️ Collect rainwater for plants.", reason: "This conserves clean drinking water and supports sustainability." },
            { tip: "☀️ Switch to renewable energy sources.", reason: "Renewables reduce reliance on fossil fuels and cut emissions." },
            { tip: "🛍️ Bring your own shopping bag.", reason: "Reusable bags reduce plastic waste in oceans and landfills." },
            { tip: "🔌 Unplug electronics when not in use.", reason: "This prevents phantom energy consumption." },
            { tip: "🍎 Support local farmers.", reason: "Buying local reduces transport emissions and supports communities." },
            { tip: "🔧 Repair and reuse items.", reason: "Extending product life reduces waste and resource demand." },
            { tip: "🧼 Use natural cleaning products.", reason: "They reduce harmful chemicals entering waterways." },
            { tip: "🚿 Install low-flow showerheads.", reason: "This saves water and reduces energy for heating." },
            { tip: "🚱 Avoid bottled water.", reason: "Tap water with a filter is cheaper and reduces plastic waste." },
            { tip: "♻️ Buy second-hand items.", reason: "Reusing products lowers demand for new manufacturing." },
            { tip: "✈️ Limit air travel.", reason: "Flying produces high CO₂ emissions compared to other transport." },
            { tip: "🏠 Insulate your home.", reason: "Better insulation reduces heating and cooling energy use." },
            { tip: "🧾 Choose digital receipts.", reason: "This reduces paper waste." },
            { tip: "🔋 Use rechargeable batteries.", reason: "They reduce toxic waste compared to disposable ones." },
            { tip: "🍳 Cook at home more often.", reason: "It reduces packaging waste and energy from food delivery." },
            { tip: "🥢 Avoid single-use cutlery.", reason: "Reusable utensils reduce plastic pollution." },
            { tip: "🎁 Donate unused items.", reason: "This extends product life and helps others." },
            { tip: "📦 Buy in bulk.", reason: "It reduces packaging waste and saves money." },
            { tip: "🌿 Grow your own herbs.", reason: "This reduces transport emissions and packaging waste." },
            { tip: "🚗 Choose eco-friendly transport apps.", reason: "They promote ride-sharing and reduce emissions." },
            { tip: "📚 Educate others about sustainability.", reason: "Awareness leads to collective action for the planet." }
        ];

        const ecoButton = document.getElementById('eco-button');
        const ecoOverlay = document.getElementById('eco-overlay');
        const ecoMessage = document.getElementById('eco-message');

        if (ecoButton && ecoOverlay && ecoMessage) {
        ecoButton.addEventListener('click', () => {
            const randomTip = ecoTips[Math.floor(Math.random() * ecoTips.length)];
            ecoMessage.textContent = `${randomTip.tip}\n\nWhy: ${randomTip.reason}`;
            ecoOverlay.style.display = "flex";
        });

        // закрытие при клике вне модалки
        ecoOverlay.addEventListener('click', (event) => {
            if (event.target === ecoOverlay) {
                ecoOverlay.style.display = "none";
            }
        });
    }
}


setupSideMenu() {
  const sideMenu = document.getElementById('side-menu');
  const menuClose = document.getElementById('menu-close');

  // например, открытие меню по клику на кнопку "Eco News" в навбаре
  const ecoNavLink = document.querySelector('a[href="/eco-news"]');

  if (ecoNavLink && sideMenu) {
    ecoNavLink.addEventListener('click', (e) => {
      e.preventDefault(); // чтобы не сразу переходить по ссылке
      sideMenu.classList.add('active');
    });
  }

  if (menuClose && sideMenu) {
    menuClose.addEventListener('click', () => {
      sideMenu.classList.remove('active');
    });
  }
}


    setupElements() {
        this.searchInput = document.getElementById('search-input');
        this.featuredProductsGrid = document.getElementById('featured-products-grid');
        this.searchResultsGrid = document.getElementById('search-results-grid');
        this.searchResultsSection = document.getElementById('search-results-section');
        this.loadingSpinner = document.getElementById('search-loading');
        this.categoryFilter = document.getElementById('category-filter');
    }

    setupSearch() {
        if (!this.searchInput || !this.searchResultsGrid) return;

        // Debounced search input
        this.searchInput.addEventListener('input', (e) => {
            clearTimeout(this.searchTimeout);
            const query = e.target.value.trim();
            
            if (query.length === 0) {
                this.showOriginalProducts();
                return;
            }
            
            if (query.length < 2) return; // Don't search for very short queries
            
            this.showLoading();
            
            // Debounce search (wait 300ms after user stops typing)
            this.searchTimeout = setTimeout(() => {
                this.performSearch(query);
            }, 300);
        });

        // Category filter change
        if (this.categoryFilter) {
            this.categoryFilter.addEventListener('change', () => {
                const query = this.searchInput.value.trim();
                if (query.length >= 2) {
                    this.showLoading();
                    this.performSearch(query);
                }
            });
        }
    }

    async performSearch(query) {
        try {
            const categoryId = this.categoryFilter ? this.categoryFilter.value : '';
            let url = `/api/search?q=${encodeURIComponent(query)}`;
            if (categoryId) {
                url += `&category=${categoryId}`;
            }
            
            const response = await fetch(url);
            const products = await response.json();
            
            this.displaySearchResults(products);
        } catch (error) {
            console.error('Search error:', error);
            this.showError('Search failed. Please try again.');
        } finally {
            this.hideLoading();
        }
    }

    displaySearchResults(products) {
        if (!this.searchResultsGrid) return;

        // Show search results section
        if (this.searchResultsSection) {
            this.searchResultsSection.style.display = 'block';
        }

        if (products.length === 0) {
            this.searchResultsGrid.innerHTML = `
                <div class="col-12">
                    <div class="card text-center">
                        <div class="card-body py-5">
                            <i class="fas fa-search fa-3x text-muted mb-3"></i>
                            <h4>No products found</h4>
                            <p class="text-muted">Try adjusting your search terms</p>
                        </div>
                    </div>
                </div>
            `;
            return;
        }

        const productsHTML = products.map(product => this.createProductCard(product)).join('');
        this.searchResultsGrid.innerHTML = productsHTML;

        this.searchResultsGrid.querySelectorAll('.product-card').forEach(card => {
        card.classList.add('loaded');
    });
}
    

    createProductCard(product) {
        const isFavorited = product.is_favorited;
        const favoriteIcon = isFavorited ? 'fas fa-heart text-danger' : 'far fa-heart text-muted';
        const favoriteText = isFavorited ? 'Saved' : 'Save';
        
        return `
            <div class="col-lg-4 col-md-6 mb-4">
                <div class="card h-100 product-card" data-product-id="${product.id}">
                    ${product.photo_filename ? 
                        `<img src="/static/uploads/${product.photo_filename}" alt="${product.title}" class="card-img-top" style="height: 200px; object-fit: cover;">` :
                        `<div class="card-img-top d-flex align-items-center justify-content-center bg-light" style="height: 200px;">
                            <i class="fas fa-box fa-3x text-success"></i>
                        </div>`
                    }
                    <div class="card-body d-flex flex-column">
                        <h5 class="card-title">${this.escapeHtml(product.title)}</h5>
                        <p class="card-text text-muted">${this.escapeHtml(product.description)}</p>
                        <div class="mt-auto">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <span class="h5 text-success mb-0">${product.price.toFixed(2)} TMT</span>
                                <span class="badge bg-secondary">${this.escapeHtml(product.category)}</span>
                            </div>
                            <div class="d-flex gap-2">
                                <button class="btn btn-sm btn-outline-danger favorite-btn" data-product-id="${product.id}">
                                    <i class="${favoriteIcon}"></i> ${favoriteText}
                                </button>
                                <a href="/product/${product.id}" class="btn btn-sm btn-success">
                                    <i class="fas fa-eye"></i> View Details
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    showOriginalProducts() {
        // Hide search results section
        if (this.searchResultsSection) {
            this.searchResultsSection.style.display = 'none';
        }
        // Clear search results grid
        if (this.searchResultsGrid) {
            this.searchResultsGrid.innerHTML = '';
        }
    }

    showLoading() {
        if (this.loadingSpinner) {
            this.loadingSpinner.style.display = 'block';
        }
    }

    hideLoading() {
        if (this.loadingSpinner) {
            this.loadingSpinner.style.display = 'none';
        }
    }

    showError(message) {
        this.showFlashMessage(message, 'danger');
    }

    setupMobileNav() {
        const currentPath = window.location.pathname;
        const navItems = document.querySelectorAll('.mobile-nav .nav-item');
        
        navItems.forEach(item => {
            if (item.getAttribute('href') === currentPath) {
                item.classList.add('active');
            }
        });
    }

    setupFlashMessages() {
        // Auto-dismiss flash messages after 5 seconds (only flash messages, not all alerts)
        const flashMessages = document.querySelectorAll('.flash-message');
        flashMessages.forEach(message => {
            setTimeout(() => {
                if (message.parentNode) {
                    message.style.transition = 'opacity 0.3s ease';
                    message.style.opacity = '0';
                    setTimeout(() => message.remove(), 300);
                }
            }, 5000);
        });
    }

    setupFavoriteButtons() {
        // Use event delegation for dynamic favorite buttons
        document.addEventListener('click', (e) => {
            if (e.target.closest('.favorite-btn')) {
                e.preventDefault();
                const btn = e.target.closest('.favorite-btn');
                const productId = btn.getAttribute('data-product-id');
                console.log('Favorite button clicked:', productId);
                
                if (!productId) {
                    console.error('No data-product-id found on favorite button');
                    return;
                }
                
                // Check if user is authenticated (look for login/logout links)
                const loginLink = document.querySelector('a[href*="login"]');
                const logoutLink = document.querySelector('a[href*="logout"]');
                
                if (loginLink && !logoutLink) {
                    // User is not logged in, redirect to login
                    window.location.href = '/login';
                    return;
                }
                
                console.log('Product ID:', productId);
                this.toggleFavorite(btn, productId);
            }
        });
    }

    async toggleFavorite(button, productId) {
        console.log('Toggling favorite for product:', productId);
        
        try {
            // Get CSRF token
            const csrfToken = document.querySelector('meta[name=csrf-token]')?.getAttribute('content') ||
                              document.querySelector('input[name=csrf_token]')?.value;
            
            console.log('CSRF token found:', !!csrfToken);
            
            const headers = {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json'
            };
            
            if (csrfToken) {
                headers['X-CSRFToken'] = csrfToken;
            }
            
            console.log('Sending request to:', `/toggle-favorite/${productId}`);
            
            const response = await fetch(`/toggle-favorite/${productId}`, {
                method: 'POST',
                headers: headers,
                credentials: 'same-origin'
            });
            
            console.log('Response status:', response.status);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('Response data:', data);
            
            if (data.status === 'success') {
                // Toggle the heart state without page reload
                if (data.is_saved) {
                    // Add to favorites - show filled red heart
                    button.innerHTML = '<i class="fas fa-heart"></i>';
                } else {
                    // Remove from favorites - show empty gray heart
                    button.innerHTML = '<i class="far fa-heart"></i>';
                    
                    // Special handling for favorites page - remove card
                    if (window.location.pathname.includes('/favorites')) {
                        const productCard = button.closest('.product-card');
                        if (productCard) {
                            productCard.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                            productCard.style.opacity = '0';
                            productCard.style.transform = 'scale(0.9)';
                            
                            setTimeout(() => {
                                productCard.remove();
                                
                                // Check if there are no more favorites
                                const remainingCards = document.querySelectorAll('.product-card');
                                if (remainingCards.length === 0) {
                                    // Reload page to show "no favorites" message
                                    window.location.reload();
                                }
                            }, 300);
                        }
                    }
                }
            } else {
                console.error('Failed to toggle favorite:', data);
                this.showFlashMessage('Failed to toggle favorite', 'danger');
            }
        } catch (error) {
            console.error('Error toggling favorite:', error);
            // Don't show error notifications to prevent stacking
        }
    }

    showFlashMessage(message, type) {
        // Create flash message element
        const flashDiv = document.createElement('div');
        flashDiv.className = `alert alert-${type} alert-dismissible fade show`;
        flashDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Add to page
        const container = document.querySelector('.container');
        if (container) {
            container.insertBefore(flashDiv, container.firstChild);
            
            // Auto-dismiss after 3 seconds
            setTimeout(() => {
                if (flashDiv.parentNode) {
                    flashDiv.remove();
                }
            }, 3000);
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize the app
document.addEventListener('DOMContentLoaded', () => {
    window.ecoHub = new EcoMaterialHub();
});

// Export for potential use in other scripts
window.EcoMaterialHub = EcoMaterialHub;
