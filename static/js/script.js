// Example: Simple form validation
document.addEventListener("DOMContentLoaded", function() {
    const form = document.getElementById('register-form'); // Assuming your form has id="register-form"
    
    form.addEventListener('submit', function(event) {
        let isValid = true;
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        
        // Validate username (non-empty)
        if (username === '') {
            alert('Username is required');
            isValid = false;
        }

        // Validate password (non-empty and min length 6)
        if (password === '' || password.length < 6) {
            alert('Password must be at least 6 characters');
            isValid = false;
        }

        // If invalid, prevent form submission
        if (!isValid) {
            event.preventDefault();
        }
    });
    
    // Example: Hide alert after 3 seconds
    const alert = document.getElementById('alert');
    if (alert) {
        setTimeout(function() {
            alert.style.display = 'none';
        }, 3000); // Hides after 3 seconds
    }
});
