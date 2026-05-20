document.addEventListener("DOMContentLoaded", function () {
  // Horizontal Scroll
  const scrollContainer = document.getElementById("category-scroll");
  const scrollLeftBtn = document.getElementById("scroll-left");
  const scrollRightBtn = document.getElementById("scroll-right");

  if (scrollContainer && scrollLeftBtn && scrollRightBtn) {
    scrollLeftBtn.addEventListener("click", () => {
      scrollContainer.scrollLeft -= 300;
    });

    scrollRightBtn.addEventListener("click", () => {
      scrollContainer.scrollLeft += 300;
    });
  }

  // Sidebar Toggle
  const filterToggle = document.getElementById("filterToggle");
  const filterSection = document.getElementById("filterSection");
  const overlay = document.getElementById("overlay");

  if (filterToggle && filterSection && overlay) {
    filterToggle.addEventListener("click", function () {
      const currentLeft = window.getComputedStyle(filterSection).left;
      if (currentLeft === "0px") {
        filterSection.style.left = "-270px";
        overlay.style.display = "none";
      } else {
        filterSection.style.left = "0px";
        overlay.style.display = "block";
      }
    });

    overlay.addEventListener("click", function () {
      filterSection.style.left = "-270px";
      overlay.style.display = "none";
    });
  }
});
