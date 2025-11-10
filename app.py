from flask import Flask
import threading
import os
import logging
import time

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.route('/')
def home():
    return "🤖 Magnit Bot is running on Render!"


@app.route('/health')
def health():
    return "OK"


@app.route('/ping')
def ping():
    return "pong"


def run_bot():
    """Запускает Telegram бота"""
    try:
        # Импортируем здесь чтобы избежать циклических импортов
        from bot import main as bot_main
        logger.info("🚀 Starting Telegram bot...")
        bot_main()
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")
        import traceback
        traceback.print_exc()


# Запускаем бота в отдельном потоке при старте приложения
bot_thread = None


@app.before_first_request
def start_bot():
    global bot_thread
    if bot_thread is None or not bot_thread.is_alive():
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        logger.info("✅ Bot thread started")


if __name__ == "__main__":
    # Запускаем бот при старте
    start_bot()

    # Запускаем Flask сервер
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"🌐 Starting Flask server on port {port}")
    app.run(host='0.0.0.0', port=port)