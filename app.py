from flask import Flask
import threading
import os
import logging
import time
import asyncio

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Глобальные переменные
bot_started = False
bot_thread = None

# Импортируем keep-alive
try:
    from keep_alive import start_keep_alive
except ImportError:
    def start_keep_alive():
        logger.info("❌ Keep-alive module not found")


@app.route('/')
def home():
    global bot_started, bot_thread
    logger.info("📞 GET request to /")

    if not bot_started and bot_thread is None:
        logger.info("🔄 Starting bot for the first time...")
        start_bot_thread()

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
        logger.info("🔧 Importing bot module...")
        from bot import simple_main
        logger.info("🚀 Starting Telegram bot...")

        # Запускаем асинхронную функцию
        asyncio.run(simple_main())

    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")
        import traceback
        traceback.print_exc()


def start_bot_thread():
    """Запускает бота в отдельном потоке"""
    global bot_started, bot_thread

    bot_started = True
    logger.info("🔄 Starting bot thread...")
    bot_thread = threading.Thread(target=run_bot, daemon=True, name="BotThread")
    bot_thread.start()
    logger.info(f"📊 Bot thread started: {bot_thread.is_alive()}")

    # Запускаем keep-alive
    start_keep_alive()


# Запускаем бота автоматически при старте приложения
@app.before_request
def auto_start_bot():
    """Автоматически запускаем бота при первом запросе"""
    global bot_started, bot_thread
    if not bot_started and bot_thread is None:
        logger.info("🏁 Auto-starting bot on first request...")
        start_bot_thread()


if __name__ == "__main__":
    logger.info("🌐 Starting Flask server...")
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"📍 Server will run on port {port}")

    # Проверяем наличие токена
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if token:
        logger.info("✅ TELEGRAM_BOT_TOKEN is set")
    else:
        logger.error("❌ TELEGRAM_BOT_TOKEN is not set!")

    # Запускаем Flask сервер
    app.run(host='0.0.0.0', port=port, debug=False)