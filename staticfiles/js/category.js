document.addEventListener("DOMContentLoaded", function () {
  const scrollContainer = document.getElementById('category-scroll');
  document.getElementById('scroll-left').onclick = () => scrollContainer.scrollBy({ left: -200, behavior: 'smooth' });
  document.getElementById('scroll-right').onclick = () => scrollContainer.scrollBy({ left: 200, behavior: 'smooth' });
});
