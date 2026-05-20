function toggleForm() {
  const login = document.getElementById("loginForm");
  const signup = document.getElementById("signupForm");
  login.classList.toggle("hidden");
  signup.classList.toggle("hidden");
}
function openSidebar() {
  document.getElementById("accountSidebar").classList.add("open");
}
function closeSidebar() {
  document.getElementById("accountSidebar").classList.remove("open");
}
function togglePassword(id, iconId) {
  const input = document.getElementById(id);
  const icon = document.getElementById(iconId);
  if (input.type === "password") {
    input.type = "text";
    icon.classList.remove('fa-eye');
    icon.classList.add('fa-eye-slash');
  } else {
    input.type = "password";
    icon.classList.remove('fa-eye-slash');
    icon.classList.add('fa-eye');
  }
}

document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('sidebarSignupForm');
    form.addEventListener('submit', function (e) {
        e.preventDefault();

        const formData = new FormData(form);
        fetch("{% url 'account_signup' %}", {
            method: 'POST',
            headers: {
                'X-CSRFToken': formData.get('csrfmiddlewaretoken'),
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Optional: reload or close sidebar
                window.location.reload();
            } else {
                // Show validation errors
                alert(data.errors); // Or display in a div
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    });
});