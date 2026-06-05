import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "8580691804:AAFQV9lKoMMVBdnV5FxCw3yjhCTCxnwJcSM"
API_KEY = "785d29e86d51b9673548b5f2ff798481"

CITY = "Novoyavorivsk"


# 🌤 Погода
def get_weather():
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric&lang=ua"
        data = requests.get(url, timeout=10).json()

        if "main" not in data:
            return "❌ Не можу отримати погоду"

        temp = data["main"]["temp"]
        desc = data["weather"][0]["description"]

        return f"🌤 {temp}°C\n☁️ {desc}"

    except:
        return "❌ Помилка запиту"


# 🌧 Дощ
def get_rain():
    try:
        url = f"https://api.openweathermap.org/data/2.5/forecast?q={CITY}&appid={API_KEY}&units=metric&lang=ua"
        data = requests.get(url, timeout=10).json()

        for item in data["list"][:6]:
            if "rain" in item:
                return "🌧 Скоро буде дощ! Візьми парасолю ☔"

        return "🌤 Дощу найближчим часом не буде"

    except:
        return "❌ Не можу перевірити дощ"


# 🤖 Команди
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привіт 😎\n\n/weather - погода\n/rain - дощ"
    )


async def weather_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_weather())


async def rain_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_rain())


# 🚀 Запуск
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("weather", weather_cmd))
    app.add_handler(CommandHandler("rain", rain_cmd))

    print("Bot running...")

    app.run_polling()


if __name__ == "__main__":
    main()
