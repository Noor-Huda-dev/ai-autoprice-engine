// dresses/static/js/cart-toggle.js
document.addEventListener("DOMContentLoaded", function() {
    const cartToggle = document.getElementById("cartToggle");
    const cartSidebar = document.getElementById("cartSidebar"); // This is the main sidebar element
    const closeCartSidebar = document.getElementById("closeCartSidebar");

    if (cartToggle && cartSidebar) {
        cartToggle.addEventListener("click", function(event) {
            event.preventDefault();
            loadCartSidebar(); // Call the function from cart.js to load content and open
        });
    }

    if (closeCartSidebar && cartSidebar) {
        closeCartSidebar.addEventListener("click", function() {
            cartSidebar.classList.remove("active");
        });
    }

    // Optional: Close cart sidebar when clicking outside it
    document.addEventListener('click', function(event) {
        // Check if the click target is outside the sidebar AND outside the toggle button
        if (!cartSidebar.contains(event.target) && !cartToggle.contains(event.target) && cartSidebar.classList.contains('active')) {
            cartSidebar.classList.remove('active');
        }
    });
});