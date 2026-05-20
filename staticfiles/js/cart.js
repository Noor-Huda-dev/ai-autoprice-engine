// dresses/static/js/cart.js

// Function to load and update the cart sidebar content
function loadCartSidebar() {
    fetch('/cart/sidebar/') // This URL will return the updated HTML and cart count
        .then(response => {
            if (!response.ok) {
                // If the response is not OK (e.g., 404, 500), throw an error
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json(); // Parse the JSON response
        })
        .then(data => {
            const cartDynamicContent = document.getElementById('cartDynamicContent');
            if (cartDynamicContent && data.cart_html) {
                cartDynamicContent.innerHTML = data.cart_html; // Update the inner content of the cart sidebar
            }

            const cartCountElement = document.getElementById("cart-count");
            if (cartCountElement && data.cart_count !== undefined) {
                cartCountElement.innerText = data.cart_count; // Update the cart count in the navbar
            }

            // After loading content, ensure the sidebar is active (visible)
            document.getElementById('cartSidebar').classList.add('active');
        })
        .catch(error => {
            console.error('Failed to load cart sidebar:', error);
            // Optionally, show a user-friendly message in the sidebar if an error occurs
            const cartDynamicContent = document.getElementById('cartDynamicContent');
            if (cartDynamicContent) {
                cartDynamicContent.innerHTML = '<p>Error loading cart. Please try again.</p>';
            }
        });
}

document.addEventListener("DOMContentLoaded", function () {
    // IMPORTANT: The cartToggle event listener is now handled in cart-toggle.js
    // We are only adding event delegation for dynamically loaded content here.

    // Handle clicks for dynamically added elements within the cart sidebar
    // This listener is on the document.body because cart content is dynamic
    document.body.addEventListener('click', function(event) {
        // --- Handle Decrease Quantity Button ---
        if (event.target.classList.contains('decrease-btn') || event.target.closest('.decrease-btn')) {
            event.preventDefault(); // Prevent default link behavior
            const btn = event.target.closest('.decrease-btn');
            const url = btn.href; // Get the URL from the link's href attribute

            fetch(url, { method: 'GET' }) // Assuming your decrease_quantity view handles GET requests
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        loadCartSidebar(); // Reload sidebar to reflect changes
                    } else if (data.error) {
                        alert(data.error); // Show error if any
                    }
                })
                .catch(error => console.error('Error decreasing quantity:', error));
        }

        // --- Handle Increase Quantity Button (Form Submission) ---
        if (event.target.classList.contains('increase-btn') || event.target.closest('.increase-btn')) {
            event.preventDefault(); // Prevent default button submit behavior
            const btn = event.target.closest('.increase-btn');
            const form = btn.closest('.increase-quantity-form'); // Get the parent form
            if (form) {
                const formData = new FormData(form);
                const url = form.action; // Get the URL from the form's action attribute

                fetch(url, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest', // Important for Django AJAX
                        'X-CSRFToken': formData.get('csrfmiddlewaretoken') // Get CSRF token from form data
                    },
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        loadCartSidebar(); // Reload sidebar to reflect changes
                    } else if (data.error) {
                        alert(data.error); // Show error if any
                    }
                })
                .catch(error => console.error('Error increasing quantity:', error));
            }
        }

        // --- Handle Remove from Cart Button ---
        if (event.target.classList.contains('remove-btn') || event.target.closest('.remove-btn')) {
            event.preventDefault(); // Prevent default link behavior
            const btn = event.target.closest('.remove-btn');
            const url = btn.href; // Get the URL from the link's href attribute

            fetch(url, { method: 'GET' }) // Assuming your remove_from_cart view handles GET requests
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        loadCartSidebar(); // Reload sidebar to reflect changes
                    } else if (data.error) {
                        alert(data.error); // Show error if any
                    }
                })
                .catch(error => console.error('Error removing item:', error));
        }
    });
});