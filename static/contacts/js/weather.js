// Lazy weather loading: one request per distinct city.
// Backend caches coordinates (24h) and weather (45 min).
(function () {
  const loaded = new Map();

  function metricsText(data) {
    const parts = [];
    if (data.temperature != null) parts.push(`${data.temperature}°C`);
    if (data.humidity != null) parts.push(`${data.humidity}%`);
    if (data.wind_speed != null) parts.push(`${data.wind_speed} km/h`);
    return parts.join(' · ') || 'n/a';
  }

  function fillSlot(slot, data) {
    slot.textContent = metricsText(data);
    slot.classList.remove('text-muted');
  }

  function failSlot(slot) {
    slot.textContent = 'n/a';
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
      if (loaded.has(city)) {
        const data = loaded.get(city);
        if (data) fillSlot(slot, data);
        else failSlot(slot);
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
          loaded.set(city, data);
          citySlots.forEach((slot) => {
            if (data) fillSlot(slot, data);
            else failSlot(slot);
          });
        })
        .catch(() => {
          loaded.set(city, null);
          citySlots.forEach(failSlot);
        });
    });
  }

  window.refreshWeather = refreshWeather;
  document.addEventListener('DOMContentLoaded', () => refreshWeather(document));
})();
