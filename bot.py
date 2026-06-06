import os
import threading
import requests
from flask import Flask
from waitress import serve
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# 1. Веб-сервер для того, щоб хостинг не вимикав бота
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "Бот працює 24/7!", 200

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    serve(app_flask, host="0.0.0.0", port=port)

# 2. НАЛАШТУВАННЯ (Встав свої дані сюди)
TOKEN = "8580691804:AAFQV9lKoMMVBdnV5FxCw3yjhCTCxnwJcSM"
WEATHER_KEY = "785d29e86d51b9673548b5f2ff798481"
CITY = "Novoyavorivsk"  # Напиши своє місто англійською (наприклад: Lviv, Odesa, Kharkiv)

# 3. Реальна функція перевірки погоди через OpenWeatherMap API
def get_rain():
    try:
        # Запит до API OpenWeatherMap (погода на зараз)
        url = f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={WEATHER_KEY}&units=metric&lang=uk"
        response = requests.get(url).json()
        
        # Перевіряємо, чи правильний ключ і чи знайшло місто
        if response.get("cod") != 200:
            return f"❌ Помилка API: {response.get('message', 'Невідома помилка')}"
        
        # Отримуємо опис погоди та температуру
        weather_description = response["weather"][0]["description"]
        temp = round(response["main"]["temp"])
        
        # Перевіряємо, чи є в описі згадка про дощ чи зливу
        main_weather = response["weather"][0]["main"].lower()
        
        if "rain" in main_weather or "drizzle" in main_weather:
            return f"🌧 У місті {CITY} зараз йде дощ ({weather_description}). Температура: {temp}°C. Візьми парасольку! ☔️"
        elif "snow" in main_weather:
            return f"❄️ У місті {CITY} йде сніг. Температура: {temp}°C. Вдягайся тепліше! 🧣"
        else:
            return f"☀️ У місті {CITY} дощу немає. Зараз там: {weather_description}. Температура: {temp}°C."
            
    except Exception as e:
        return f"⚠️ Не вдалося отримати дані про погоду: {e}"

# 4. Команди для Телеграм-бота
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привіт! Я твій погодний бот. 🌤\n\n"
        "Доступні команди:\n"
        "/weather - Дізнатися погоду\n"
        "/rain - Перевірити, чи потрібна парасолька"
    )

async def weather_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = get_rain()
    await update.message.reply_text(status)

async def rain_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Використовуємо ту саму функцію, бо вона аналізує наявність дощу
    status = get_rain()
    await update.message.reply_text(status)

def main():
    # Фоновий запуск веб-сервера
    threading.Thread(target=run_flask, daemon=True).start()

    # Запуск бота
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("weather", weather_cmd))
    app.add_handler(CommandHandler("rain", rain_cmd))

    print("🤖 Бот успішно запущений...")
    app.run_polling()

if __name__ == "__main__":
    main()
