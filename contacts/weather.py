"""Weather integration: Nominatim geocoding + Open-Meteo current weather."""

import json
import time
import unicodedata
import urllib.parse
import urllib.request

from django.conf import settings
from django.core.cache import cache

# Marker for failed lookups so broken cities do not hammer the APIs.
# A string on purpose: cache backends pickle values, so identity (is)
# would not survive a round trip, but equality does.
_MISS = '\x00weather-miss'


def normalize_city_key(city: str) -> str:
    """Lowercase ASCII key so Krakow and Kraków share the cache entry."""
    normalized = unicodedata.normalize('NFKD', city.strip().lower())
    stripped = ''.join(c for c in normalized if not unicodedata.combining(c))
    return stripped.replace('ł', 'l')


def _fetch_json(url: str) -> object:
    request = urllib.request.Request(
        url, headers={'User-Agent': settings.WEATHER_USER_AGENT}
    )
    with urllib.request.urlopen(request, timeout=settings.WEATHER_HTTP_TIMEOUT) as response:
        return json.loads(response.read().decode('utf-8'))


def get_coordinates(city: str) -> tuple[float, float] | None:
    """Resolve city name to (lat, lon) via Nominatim. Cached 24h."""
    key = f'geo:{normalize_city_key(city)}'
    cached = cache.get(key)
    if cached == _MISS:
        return None
    if cached is not None:
        return tuple(cached)

    params = urllib.parse.urlencode({'q': city, 'format': 'json', 'limit': 1})
    data = _fetch_json(f'https://nominatim.openstreetmap.org/search?{params}')
    if not data:
        cache.set(key, _MISS, settings.WEATHER_NEGATIVE_CACHE_TIMEOUT)
        return None
    coords = (float(data[0]['lat']), float(data[0]['lon']))
    cache.set(key, coords, settings.WEATHER_GEO_CACHE_TIMEOUT)
    return coords


def get_weather(lat: float, lon: float) -> dict | None:
    """Fetch current weather via Open-Meteo. Cached 45 min."""
    lat, lon = round(lat, 2), round(lon, 2)
    key = f'weather:{lat},{lon}'
    cached = cache.get(key)
    if cached == _MISS:
        return None
    if cached is not None:
        return dict(cached)

    params = urllib.parse.urlencode(
        {
            'latitude': lat,
            'longitude': lon,
            'current': (
                'temperature_2m,relative_humidity_2m,'
                'wind_speed_10m,weather_code'
            ),
            'timezone': 'auto',
        }
    )
    data = _fetch_json(f'https://api.open-meteo.com/v1/forecast?{params}')
    current = (data or {}).get('current')
    if not current:
        cache.set(key, _MISS, settings.WEATHER_NEGATIVE_CACHE_TIMEOUT)
        return None
    result = {
        'temperature': current.get('temperature_2m'),
        'humidity': current.get('relative_humidity_2m'),
        'wind_speed': current.get('wind_speed_10m'),
        'weather_code': current.get('weather_code'),
        'fetched_at': time.time(),
    }
    cache.set(key, result, settings.WEATHER_CACHE_TIMEOUT)
    return dict(result)


def get_city_weather(city: str) -> dict | None:
    """Full lookup: city -> coords -> weather. Returns None when unknown."""
    if not city or not city.strip():
        return None
    coords = get_coordinates(city)
    if coords is None:
        return None
    return get_weather(*coords)
