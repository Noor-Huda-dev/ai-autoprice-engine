document.addEventListener('DOMContentLoaded', function() {
  const carousel = document.getElementById('carousel');
  const scrollAmount = 300;

  document.getElementById('scroll-left').addEventListener('click', function() {
    carousel.scrollBy({ left: -scrollAmount, behavior: 'smooth' });
  });

  document.getElementById('scroll-right').addEventListener('click', function() {
    carousel.scrollBy({ left: scrollAmount, behavior: 'smooth' });
  });
});
