import requests
import time
import threading
import os
import logging

logger = logging.getLogger(__name__)


def keep_alive():
    """Периодически пингует сервер чтобы предотвратить остановку"""
    url = os.environ.get('RENDER_URL', 'https://fbs-garb.onrender.com')

    while True:
        try:
            response = requests.get(f"{url}/ping", timeout=10)
            logger.info(f"🔄 Keep-alive ping: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Keep-alive error: {e}")

        # Пингуем каждые 5 минут
        time.sleep(300)


def start_keep_alive():
    """Запускает keep-alive в отдельном потоке"""
    thread = threading.Thread(target=keep_alive, daemon=True)
    thread.start()
    logger.info("🔄 Keep-alive started")