from flask import Flask
import threading
import os
import logging
import time

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Глобальная переменная для отслеживания запуска бота
bot_started = False


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


@app.before_request
def start_bot_on_first_request():
    """Запускаем бота при первом запросе"""
    global bot_started
    if not bot_started:
        bot_started = True
        logger.info("🔄 Starting bot thread on first request...")
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        # Даем боту время на запуск
        time.sleep(3)


if __name__ == "__main__":
    logger.info("🌐 Starting Flask server...")
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"📍 Server will run on port {port}")

    # Запускаем Flask сервер
    app.run(host='0.0.0.0', port=port)