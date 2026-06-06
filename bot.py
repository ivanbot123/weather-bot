import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ВСТАВТЕ ВАШІ ДАНІ СЮДИ ЗАМІСТЬ ТЕКСТУ В ЛАПКАХ:
TOKEN = "8580691804:AAFQV9lKoMMVBdnV5FxCw3yjhCTCxnwJcSM"
WEATHER_KEY = "785d29e86d51b9673548b5f2ff798481"

def get_rain():
    # Ваша функція аналізу дощу, яка використовує WEATHER_KEY
    # Приклад: url = f"https://openweathermap.org{WEATHER_KEY}"
    return "Сьогодні дощу не передбачається ☀️"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привіт! Я бот погоди.")

async def weather_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Погода чудова!")

async def rain_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = get_rain()
    await update.message.reply_text(status)

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("weather", weather_cmd))
    app.add_handler(CommandHandler("rain", rain_cmd))

    print("🤖 Бот запущений 24/7...")
    app.run_polling()

if __name__ == "__main__":
    main()
