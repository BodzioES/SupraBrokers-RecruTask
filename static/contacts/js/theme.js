// Light/dark theme toggle persisted in localStorage. Default: light.
(function () {
  const KEY = 'sb-theme';
  const button = document.getElementById('theme-toggle');

  function iconFor(theme) {
    return theme === 'dark'
      ? '<i class="bi bi-sun-fill"></i>'
      : '<i class="bi bi-moon-fill"></i>';
  }

  function current() {
    return document.documentElement.getAttribute('data-bs-theme') || 'light';
  }

  function paint() {
    if (button) button.innerHTML = iconFor(current());
  }

  if (button) {
    button.addEventListener('click', () => {
      const next = current() === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-bs-theme', next);
      try {
        localStorage.setItem(KEY, next);
      } catch (e) {}
      paint();
    });
  }
  paint();
})();
