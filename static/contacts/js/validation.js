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

  // Live initials preview (same algorithm as Contact.initials/avatar_color).
  const preview = document.getElementById('avatar-preview');
  function updatePreview() {
    if (!preview) return;
    const firstInput = form.querySelector('[name="first_name"]');
    const lastInput = form.querySelector('[name="last_name"]');
    const first = (firstInput ? firstInput.value : '').trim().charAt(0).toUpperCase();
    const last = (lastInput ? lastInput.value : '').trim().charAt(0).toUpperCase();
    const combined = `${firstInput ? firstInput.value : ''}${lastInput ? lastInput.value : ''}`.toLowerCase();
    let total = 0;
    for (const char of combined) total += char.codePointAt(0);
    preview.className = `avatar avatar-c${total % 8}`;
    preview.textContent = `${first}${last}` || '?';
  }

  ['email', 'phone', 'first_name', 'last_name', 'city'].forEach((name) => {
    const input = form.querySelector(`[name="${name}"]`);
    if (input) {
      input.addEventListener('input', () => {
        validateField(input);
        if (name === 'first_name' || name === 'last_name') updatePreview();
      });
    }
  });
  updatePreview();
  // The add/edit modal fills fields programmatically (no input events).
  form.addEventListener('avatar-refresh', updatePreview);

  form.addEventListener('submit', (event) => {
    let valid = true;
    ['email', 'phone', 'first_name', 'last_name', 'city'].forEach((name) => {
      const input = form.querySelector(`[name="${name}"]`);
      if (input && !validateField(input)) valid = false;
    });
    if (!valid) event.preventDefault();
  });
})();
