import os
import threading
import requests
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Flask сервер для "розігріву" бота
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "Бот працює!", 200

def run_flask():
    # Render автоматично передає порт у змінну оточення PORT
    port = int(os.environ.get("PORT", 5000))
    app_flask.run(host="0.0.0.0", port=port)

# ТВОЇ НАЛАШТУВАННЯ (краще завантажувати через змінні оточення):
TOKEN = os.environ.get("TELEGRAM_TOKEN", "8580691804:AAFQV9lKoMMVBdnV5FxCw3yjhCTCxnwJcSM")
WEATHER_KEY = os.environ.get("WEATHER_KEY", "785d29e86d51b9673548b5f2ff798481")

def get_rain():
    return "Сьогодні дощу не передбачається ☀️"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привіт! Я бот погоди.")

async def weather_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Погода чудова!")

async def rain_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = get_rain()
    await update.message.reply_text(status)

def main():
    # Запуск Flask у фоновому режимі
    threading.Thread(target=run_flask, daemon=True).start()

    # Запуск Telegram бота
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("weather", weather_cmd))
    app.add_handler(CommandHandler("rain", rain_cmd))

    print("🤖 Бот запущений...")
    app.run_polling()

if __name__ == "__main__":
    main()
