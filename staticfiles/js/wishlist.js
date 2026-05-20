document.addEventListener("DOMContentLoaded", function () {
  const wishlistToggle = document.getElementById("wishlistToggle");
  const wishlistSidebar = document.getElementById("wishlist-sidebar");
  const wishlistClose = document.getElementById("wishlist-close");
  const wishlistCount = document.getElementById("wishlist-count");

  if (!wishlistToggle || !wishlistSidebar || !wishlistClose || !wishlistCount) return;

  wishlistToggle.addEventListener("click", function (e) {
    e.preventDefault();
    wishlistSidebar.classList.toggle("show");
    loadWishlistItems();
  });

  wishlistClose.addEventListener("click", function () {
    wishlistSidebar.classList.remove("show");
  });

  function loadWishlistItems() {
    fetch("/wishlist/items/")
      .then((res) => res.json())
      .then((data) => {
        const container = document.getElementById("wishlist-items");
        container.innerHTML = "";

        if (!data.items || data.items.length === 0) {
          container.innerHTML = "<p class='p-3'>Your wishlist is empty.</p>";
          wishlistCount.style.display = "none";
          return;
        }

        wishlistCount.style.display = "inline-block";
        wishlistCount.textContent = data.items.length;

        data.items.forEach((item) => {
          const div = document.createElement("div");
          div.classList.add("wishlist-item");
          div.innerHTML = `
            <div class="d-flex align-items-start gap-3">
              <img src="${item.image_url}" alt="${item.name}" class="img-thumbnail" style="width: 60px; height: 60px; object-fit: cover;">
              <div class="flex-grow-1">
                <a href="/product/${item.slug}/" class="fw-semibold text-dark text-decoration-none">${item.name}</a>
                <p class="mb-1 text-muted small">Rs. ${item.price}</p>
              </div>
              <button class="wishlist-item-remove btn btn-sm btn-outline-danger" data-id="${item.id}">&times;</button>
            </div>
          `;
          container.appendChild(div);
        });

        document.querySelectorAll(".wishlist-item-remove").forEach((btn) => {
          btn.addEventListener("click", function () {
            const id = this.getAttribute("data-id");
            fetch(`/wishlist/remove/${id}/`).then(() => {
              loadWishlistItems();
              updateWishlistCount();
            });
          });
        });

        updateWishlistCount();
      });
  }

  function updateWishlistCount() {
    fetch("/wishlist/count/")
      .then((res) => res.json())
      .then((data) => {
        wishlistCount.textContent = data.count;
        wishlistCount.style.display = data.count > 0 ? "inline-block" : "none";
      });
  }

  updateWishlistCount();

  document.querySelectorAll(".add-to-wishlist").forEach((btn) => {
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      const productId = this.getAttribute("data-id");
      fetch(`/wishlist/add/${productId}/`)
        .then((res) => res.json())
        .then((data) => {
          if (data.status === "added") {
            wishlistSidebar.classList.add("show");
            loadWishlistItems();
            updateWishlistCount();
          }
        });
    });
  });
});
