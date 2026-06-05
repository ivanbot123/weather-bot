import requests
from telegram.ext import Application, CommandHandler

TOKEN = "8580691804:AAFQV9lKoMMVBdnV5FxCw3yjhCTCxnwJcSM"
API_KEY = "785d29e86d51b9673548b5f2ff798481"

CITY = "Novoyavorivsk"

def weather():
    url = f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric&lang=ua"
    data = requests.get(url).json()

    return f"🌤 {data['main']['temp']}°C\n☁️ {data['weather'][0]['description']}"

async def start(update, context):
    await update.message.reply_text("Привіт 😎 /weather")

async def w(update, context):
    await update.message.reply_text(weather())

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("weather", w))

print("Bot running")
app.run_polling()
