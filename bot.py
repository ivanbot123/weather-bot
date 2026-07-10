import json
import os
import requests
from datetime import datetime
from typing import List, Dict, Optional

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# =========================
# НАЛАШТУВАННЯ
# =========================

TOKEN = "8580691804:AAFQV9lKoMMVBdnV5FxCw3yjhCTCxnwJcSM"
USERS_FILE = "users.json"

# Open-Meteo / geocoding
GEOCODE_SEARCH_URL = "https://geocoding-api.open-meteo.com/v1/search"
GEOCODE_REVERSE_URL = "https://geocoding-api.open-meteo.com/v1/reverse"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


# =========================
# ФАЙЛ КОРИСТУВАЧІВ
# =========================

def load_users() -> Dict:
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save_users(users: Dict):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def ensure_user(user_id: int):
    users = load_users()
    uid = str(user_id)
    if uid not in users:
        users[uid] = {
            "place_name": None,
            "admin1": None,
            "latitude": None,
            "longitude": None,
            "show_coords": False,

            # pending mode:
            # None | "manual_place_input" | "choose_place_text" | "choose_place_geo"
            "pending_mode": None,

            # список варіантів для вибору після текстового пошуку або геолокації
            "pending_places": []
        }
        save_users(users)


def get_user_data(user_id: int) -> Dict:
    users = load_users()
    return users.get(str(user_id), {})


def update_user_data(user_id: int, **kwargs):
    users = load_users()
    uid = str(user_id)
    if uid not in users:
        users[uid] = {
            "place_name": None,
            "admin1": None,
            "latitude": None,
            "longitude": None,
            "show_coords": False,
            "pending_mode": None,
            "pending_places": []
        }
    users[uid].update(kwargs)
    save_users(users)


def save_user_place(user_id: int, place_name: str, admin1: str, latitude: float, longitude: float):
    update_user_data(
        user_id,
        place_name=place_name,
        admin1=admin1,
        latitude=latitude,
        longitude=longitude,
        pending_mode=None,
        pending_places=[]
    )


def set_show_coords(user_id: int, value: bool):
    user = get_user_data(user_id)
    update_user_data(
        user_id,
        show_coords=value,
        place_name=user.get("place_name"),
        admin1=user.get("admin1"),
        latitude=user.get("latitude"),
        longitude=user.get("longitude"),
        pending_mode=user.get("pending_mode"),
        pending_places=user.get("pending_places", [])
    )


# =========================
# КНОПКИ
# =========================

def main_menu():
    return ReplyKeyboardMarkup(
        [
            ["🌤 Погода зараз", "📅 Прогноз 3 дні"],
            ["🏘 Змінити населений пункт", "⚙️ Налаштування"],
            ["ℹ️ Допомога"]
        ],
        resize_keyboard=True
    )


def location_keyboard():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("📍 Надіслати геолокацію", request_location=True)],
            ["⬅️ Назад"]
        ],
        resize_keyboard=True
    )


def settings_menu(show_coords: bool):
    coords_text = "📍 Показ координат: Увімк" if show_coords else "📍 Показ координат: Вимк"
    return ReplyKeyboardMarkup(
        [
            [coords_text],
            ["🏠 Мій населений пункт"],
            ["⬅️ Назад"]
        ],
        resize_keyboard=True
    )


def places_choice_keyboard(places: List[Dict]):
    """
    Кнопки для вибору населеного пункту:
    1) до 5 варіантів
    2) кнопка "немає мого населеного пункту"
    """
    rows = []
    for idx, place in enumerate(places[:5], start=1):
        label = format_place_button(place, idx)
        rows.append([label])

    rows.append(["❌ Немає мого населеного пункту"])
    rows.append(["⬅️ Назад"])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


# =========================
# ДОПОМІЖНІ ФУНКЦІЇ
# =========================

def format_place_button(place: Dict, idx: int) -> str:
    name = place.get("name", "Невідомо")
    admin1 = place.get("admin1", "")
    if admin1:
        return f"{idx}. {name}, {admin1}"
    return f"{idx}. {name}"


def weather_code_to_text(code: int) -> str:
    weather_map = {
        0: "☀️ Ясно",
        1: "🌤 Переважно ясно",
        2: "⛅ Мінлива хмарність",
        3: "☁️ Хмарно",
        45: "🌫 Туман",
        48: "🌫 Паморозь, туман",
        51: "🌦 Слабка мряка",
        53: "🌦 Помірна мряка",
        55: "🌧 Сильна мряка",
        61: "🌧 Невеликий дощ",
        63: "🌧 Дощ",
        65: "🌧 Сильний дощ",
        66: "🌧 Крижаний дощ",
        67: "🌧 Сильний крижаний дощ",
        71: "❄️ Невеликий сніг",
        73: "❄️ Сніг",
        75: "❄️ Сильний сніг",
        77: "❄️ Снігові зерна",
        80: "🌦 Злива",
        81: "🌧 Сильна злива",
        82: "🌧 Дуже сильна злива",
        85: "🌨 Снігові заряди",
        86: "🌨 Сильні снігові заряди",
        95: "⛈ Гроза",
        96: "⛈ Гроза з градом",
        99: "⛈ Сильна гроза з градом",
    }
    return weather_map.get(code, f"Код погоди: {code}")


def wind_direction_text(deg: Optional[float]) -> str:
    if deg is None:
        return "Невідомо"
    directions = ["Пн", "ПнСх", "Сх", "ПдСх", "Пд", "ПдЗх", "Зх", "ПнЗх"]
    index = round(deg / 45) % 8
    return directions[index]


def distance_km(lat1, lon1, lat2, lon2):
    # приблизний haversine
    from math import radians, sin, cos, sqrt, atan2
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


# =========================
# ПОШУК НАСЕЛЕНИХ ПУНКТІВ
# =========================

def search_places_in_ukraine(query: str, count: int = 10) -> List[Dict]:
    """
    Пошук населених пунктів по тексту.
    Повертає список варіантів.
    """
    params = {
        "name": query,
        "count": count,
        "language": "uk",
        "country": "UA"
    }
    try:
        r = requests.get(GEOCODE_SEARCH_URL, params=params, timeout=20)
        data = r.json()
    except:
        return []

    results = data.get("results", [])
    places = []

    for item in results:
        if item.get("country_code") != "UA":
            continue

        place = {
            "name": item.get("name"),
            "admin1": item.get("admin1", ""),
            "latitude": item.get("latitude"),
            "longitude": item.get("longitude"),
        }

        # унікальність по name+admin1+coords
        duplicate = False
        for p in places:
            if (
                p["name"] == place["name"]
                and p["admin1"] == place["admin1"]
                and p["latitude"] == place["latitude"]
                and p["longitude"] == place["longitude"]
            ):
                duplicate = True
                break
        if not duplicate:
            places.append(place)

    return places[:10]


def reverse_places_ukraine(lat: float, lon: float, count: int = 10) -> List[Dict]:
    """
    Reverse geocoding по координатах.
    Повертає кілька кандидатів, якщо API їх дає.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "language": "uk",
        "count": count
    }
    try:
        r = requests.get(GEOCODE_REVERSE_URL, params=params, timeout=20)
        data = r.json()
    except:
        return []

    results = data.get("results", [])
    places = []

    for item in results:
        if item.get("country_code") != "UA":
            continue
        place = {
            "name": item.get("name"),
            "admin1": item.get("admin1", ""),
            "latitude": item.get("latitude"),
            "longitude": item.get("longitude"),
        }

        duplicate = False
        for p in places:
            if (
                p["name"] == place["name"]
                and p["admin1"] == place["admin1"]
                and p["latitude"] == place["latitude"]
                and p["longitude"] == place["longitude"]
            ):
                duplicate = True
                break
        if not duplicate:
            places.append(place)

    return places


def build_geo_candidates(lat: float, lon: float) -> List[Dict]:
    """
    Логіка для геолокації:
    1) беремо reverse-кандидатів
    2) перший reverse результат вважаємо основним
    3) додатково підтягуємо схожі варіанти за назвою основного + найближчі reverse
    4) формуємо фінальний список без дублікатів
    """
    reverse_candidates = reverse_places_ukraine(lat, lon, count=10)
    if not reverse_candidates:
        return []

    main_place = reverse_candidates[0]
    combined = []

    def add_unique(place):
        for p in combined:
            if (
                p["name"] == place["name"]
                and p["admin1"] == place["admin1"]
                and p["latitude"] == place["latitude"]
                and p["longitude"] == place["longitude"]
            ):
                return
        combined.append(place)

    # 1) головний reverse-варіант першим
    add_unique(main_place)

    # 2) інші reverse варіанти
    for p in reverse_candidates[1:]:
        add_unique(p)

    # 3) додатковий пошук по назві головного пункту
    name_matches = search_places_in_ukraine(main_place["name"], count=10)
    for p in name_matches:
        add_unique(p)

    # 4) сортуємо: головний лишається першим, решту приблизно за відстанню до геолокації
    if len(combined) > 1:
        first = combined[0]
        rest = combined[1:]
        rest.sort(key=lambda p: distance_km(lat, lon, p["latitude"], p["longitude"]))
        combined = [first] + rest

    return combined[:5]


# =========================
# ПОГОДА
# =========================

def get_current_weather(lat: float, lon: float) -> Optional[Dict]:
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": ",".join([
            "temperature_2m",
            "relative_humidity_2m",
            "apparent_temperature",
            "surface_pressure",
            "wind_speed_10m",
            "wind_direction_10m",
            "weather_code"
        ]),
        "timezone": "auto"
    }
    try:
        r = requests.get(WEATHER_URL, params=params, timeout=20)
        data = r.json()
    except:
        return None

    current = data.get("current")
    if not current:
        return None

    return {
        "temperature": current.get("temperature_2m"),
        "humidity": current.get("relative_humidity_2m"),
        "feels_like": current.get("apparent_temperature"),
        "pressure": current.get("surface_pressure"),
        "wind_speed": current.get("wind_speed_10m"),
        "wind_direction_deg": current.get("wind_direction_10m"),
        "weather_code": current.get("weather_code"),
        "time": current.get("time"),
    }


def get_forecast_3_days(lat: float, lon: float) -> Optional[List[Dict]]:
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": ",".join([
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum"
        ]),
        "forecast_days": 3,
        "timezone": "auto"
    }
    try:
        r = requests.get(WEATHER_URL, params=params, timeout=20)
        data = r.json()
    except:
        return None

    daily = data.get("daily")
    if not daily:
        return None

    result = []
    for i in range(len(daily["time"])):
        result.append({
            "date": daily["time"][i],
            "weather_code": daily["weather_code"][i],
            "temp_max": daily["temperature_2m_max"][i],
            "temp_min": daily["temperature_2m_min"][i],
            "precipitation": daily["precipitation_sum"][i]
        })
    return result


# =========================
# ФОРМАТУВАННЯ ТЕКСТУ
# =========================

def format_current_weather(user_data: Dict, weather: Dict) -> str:
    place = user_data.get("place_name")
    admin1 = user_data.get("admin1") or ""
    show_coords = user_data.get("show_coords", False)
    lat = user_data.get("latitude")
    lon = user_data.get("longitude")

    direction = wind_direction_text(weather.get("wind_direction_deg"))
    weather_text = weather_code_to_text(weather.get("weather_code"))

    text = f"🌤 <b>Погода зараз</b>\n\n📍 <b>{place}</b>"
    if admin1:
        text += f", {admin1}"

    text += "\n\n"
    text += (
        f"{weather_text}\n\n"
        f"🌡 <b>Температура:</b> {weather.get('temperature')}°C\n"
        f"🥵 <b>Відчувається як:</b> {weather.get('feels_like')}°C\n"
        f"💧 <b>Вологість:</b> {weather.get('humidity')}%\n"
        f"🌬 <b>Вітер:</b> {weather.get('wind_speed')} км/год\n"
        f"🧭 <b>Напрям вітру:</b> {direction} ({weather.get('wind_direction_deg')}°)\n"
        f"🧪 <b>Тиск:</b> {weather.get('pressure')} гПа\n"
    )
