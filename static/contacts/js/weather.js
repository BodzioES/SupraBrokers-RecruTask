// Lazy weather loading: one request per distinct city.
// Backend caches coordinates (24h) and weather (45 min).
(function () {
  const loadedCities = new Map();

  function format(data) {
    const parts = [];
    if (data.temperature != null) parts.push(`${data.temperature}°C`);
    if (data.humidity != null) parts.push(`${data.humidity}%`);
    if (data.wind_speed != null) parts.push(`${data.wind_speed} km/h`);
    return parts.join(' · ') || 'n/a';
  }

  // Scan root for new weather slots. Already-loaded cities fill instantly.
  function refreshWeather(root) {
    const slots = (root || document).querySelectorAll('.weather-slot[data-city]');
    if (!slots.length) return;
    const fresh = new Map();
    slots.forEach((slot) => {
      if (slot.dataset.loaded) return;
      const city = (slot.dataset.city || '').trim();
      if (!city) return;
      slot.dataset.loaded = '1';
      if (loadedCities.has(city)) {
        slot.textContent = loadedCities.get(city);
        slot.classList.remove('text-muted');
        return;
      }
      slot.textContent = '…';
      if (!fresh.has(city)) fresh.set(city, []);
      fresh.get(city).push(slot);
    });
    fresh.forEach((citySlots, city) => {
      fetch(`/weather/?city=${encodeURIComponent(city)}`)
        .then((response) => (response.ok ? response.json() : null))
        .then((data) => {
          const text = data ? format(data) : 'n/a';
          loadedCities.set(city, text);
          citySlots.forEach((slot) => {
            slot.textContent = text;
            slot.classList.remove('text-muted');
          });
        })
        .catch(() => {
          citySlots.forEach((slot) => {
            slot.textContent = 'n/a';
          });
        });
    });
  }

  window.refreshWeather = refreshWeather;
  document.addEventListener('DOMContentLoaded', () => refreshWeather(document));
})();
