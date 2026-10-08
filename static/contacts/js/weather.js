// Lazy weather loading: one request per distinct city.
// Backend caches coordinates (30 days) and weather (45 min).
(function () {
  const loaded = new Map();

  // WMO weather code -> [lucide icon, short description].
  function condition(code) {
    if (code === 0 || code === 1) return ['sun', 'Clear sky'];
    if (code === 2) return ['cloud-sun', 'Partly cloudy'];
    if (code === 3) return ['cloud', 'Overcast'];
    if (code === 45 || code === 48) return ['cloud-fog', 'Fog'];
    if (code >= 51 && code <= 57) return ['cloud-drizzle', 'Drizzle'];
    if ([61, 63, 65, 66, 67, 80, 81, 82].includes(code)) {
      return ['cloud-rain', 'Rain'];
    }
    if ([71, 73, 75, 77, 85, 86].includes(code)) {
      return ['cloud-snow', 'Snow'];
    }
    if (code !== null && code !== undefined && code >= 95) {
      return ['cloud-lightning', 'Thunderstorm'];
    }
    return ['cloud-sun', 'Weather'];
  }

  function metricsText(data) {
    const parts = [];
    if (data.temperature != null) parts.push(`${data.temperature}°C`);
    if (data.humidity != null) parts.push(`${data.humidity}%`);
    if (data.wind_speed != null) parts.push(`${data.wind_speed} km/h`);
    return parts.join(' · ') || 'n/a';
  }

  function fillSlot(slot, data) {
    const [icon, label] = condition(data.weather_code);
    slot.innerHTML =
      `<span title="${label}"><i data-lucide="${icon}"></i></span> ` +
      `<span>${metricsText(data)}</span>`;
    slot.classList.remove('text-muted');
    if (window.lucide) window.lucide.createIcons();
  }

  function failSlot(slot) {
    slot.innerHTML =
      '<span class="text-muted" title="Weather unavailable">no data</span>';
  }

  // Scan root for new weather slots. Already-loaded cities fill instantly.
  function refreshWeather(root) {
    const slots = (root || document).querySelectorAll('.weather-slot[data-city]');
    if (!slots.length) return;
    const fresh = new Map();
    slots.forEach((slot) => {
      // Skip slots handled before, so re-scans never duplicate requests.
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
      slot.innerHTML = '<span class="weather-skeleton" aria-hidden="true"></span>';
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
