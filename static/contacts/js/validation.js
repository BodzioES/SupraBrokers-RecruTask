// Client-side validation for the contact form. Mirrors server rules.
(function () {
  const form = document.getElementById('contact-form');
  if (!form) return;

  const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

  function normalizePhone(value) {
    return (value || '').replace(/[\s\-/().]/g, '');
  }

  function isValidPhone(value) {
    return /^(\+48)?\d{9}$/.test(normalizePhone(value));
  }

  function setState(input, valid, message) {
    const feedback = document.querySelector(`[data-error-for="${input.id}"]`);
    input.classList.remove('is-valid', 'is-invalid');
    input.classList.add(valid ? 'is-valid' : 'is-invalid');
    if (feedback) feedback.textContent = valid ? '' : message;
    return valid;
  }

  function validateField(input) {
    const value = input.value.trim();
    if (input.name === 'email') {
      return setState(input, emailRe.test(value), 'Enter a valid e-mail address.');
    }
    if (input.name === 'phone') {
      return setState(input, isValidPhone(value), 'Enter 9 digits, optional +48.');
    }
    if (['first_name', 'last_name', 'city'].includes(input.name)) {
      return setState(input, value.length > 0, 'This field is required.');
    }
    return true;
  }

  ['email', 'phone', 'first_name', 'last_name', 'city'].forEach((name) => {
    const input = form.querySelector(`[name="${name}"]`);
    if (input) input.addEventListener('input', () => validateField(input));
  });

  form.addEventListener('submit', (event) => {
    let valid = true;
    ['email', 'phone', 'first_name', 'last_name', 'city'].forEach((name) => {
      const input = form.querySelector(`[name="${name}"]`);
      if (input && !validateField(input)) valid = false;
    });
    if (!valid) event.preventDefault();
  });
})();
