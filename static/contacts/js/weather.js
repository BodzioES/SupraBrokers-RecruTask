// Lazy weather loading: one request per distinct city per page load.
// Backend caches coordinates (24h) and weather (45 min).
(function () {
  const slots = document.querySelectorAll('.weather-slot[data-city]');
  if (!slots.length) return;

  const byCity = new Map();
  slots.forEach((slot) => {
    const city = (slot.dataset.city || '').trim();
    if (!city) return;
    slot.textContent = '…';
    if (!byCity.has(city)) byCity.set(city, []);
    byCity.get(city).push(slot);
  });

  function format(data) {
    const parts = [];
    if (data.temperature != null) parts.push(`${data.temperature}°C`);
    if (data.humidity != null) parts.push(`${data.humidity}%`);
    if (data.wind_speed != null) parts.push(`${data.wind_speed} km/h`);
    return parts.join(' · ') || 'n/a';
  }

  byCity.forEach((citySlots, city) => {
    fetch(`/weather/?city=${encodeURIComponent(city)}`)
      .then((response) => (response.ok ? response.json() : null))
      .then((data) => {
        const text = data ? format(data) : 'n/a';
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
})();
