document.addEventListener('DOMContentLoaded', function() {
    // Password strength indicator
    const passwordInput = document.querySelector('input[name="password"]');
    const strengthBar = document.querySelector('.strength-bar');
    const strengthValue = document.querySelector('.strength-value');

    passwordInput.addEventListener('input', function() {
        const password = this.value;
        const strength = calculatePasswordStrength(password);

        strengthBar.style.width = strength.percentage + '%';
        strengthBar.style.background = strength.color;
        strengthValue.textContent = strength.text;
        strengthValue.style.color = strength.color;
    });

    // Toggle password visibility
    const togglePasswordBtns = document.querySelectorAll('.toggle-password');
    togglePasswordBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const input = this.previousElementSibling;
            const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
            input.setAttribute('type', type);
            this.classList.toggle('fa-eye');
            this.classList.toggle('fa-eye-slash');
        });
    });

    // Form validation
    const form = document.querySelector('.signup-form');
    form.addEventListener('submit', function(e) {
        const password = document.querySelector('input[name="password"]').value;
        const confirmPassword = document.querySelector('input[name="confirm_password"]').value;
        const termsChecked = document.querySelector('input[name="terms"]').checked;

        if (password !== confirmPassword) {
            e.preventDefault();
            alert('Passwords do not match!');
            return false;
        }

        if (!termsChecked) {
            e.preventDefault();
            alert('You must agree to the terms and conditions!');
            return false;
        }

        return true;
    });
});

function calculatePasswordStrength(password) {
    let strength = 0;
    const hasUpperCase = /[A-Z]/.test(password);
    const hasLowerCase = /[a-z]/.test(password);
    const hasNumbers = /\d/.test(password);
    const hasSpecialChars = /[!@#$%^&*(),.?":{}|<>]/.test(password);

    // Length contributes up to 50% of the strength
    strength += Math.min(password.length / 16 * 50, 50);

    // Character variety contributes the remaining 50%
    if (hasUpperCase) strength += 10;
    if (hasLowerCase) strength += 10;
    if (hasNumbers) strength += 15;
    if (hasSpecialChars) strength += 15;

    // Cap at 100
    strength = Math.min(strength, 100);

    // Determine strength level
    let level, color;
    if (strength < 30) {
        level = 'Weak';
        color = '#ff4757';
    } else if (strength < 70) {
        level = 'Moderate';
        color = '#ffa502';
    } else if (strength < 90) {
        level = 'Strong';
        color = '#2ed573';
    } else {
        level = 'Very Strong';
        color = '#1dd1a1';
    }

    return {
        percentage: strength,
        text: level,
        color: color
    };
}