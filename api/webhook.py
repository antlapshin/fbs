import asyncio
import json
import logging
from http.server import BaseHTTPRequestHandler

from bot import create_application
from telegram import Update

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Глобальная переменная для кэширования приложения между запросами
_application = None
_initialized = False


async def _get_or_create_application():
    """Получает или создает и инициализирует Telegram Application."""
    global _application, _initialized
    
    if _application is None:
        logger.info("🔧 Creating Telegram application...")
        _application = create_application()
        logger.info("✅ Telegram application created")
    
    if not _initialized:
        logger.info("🚀 Initializing application...")
        await _application.initialize()
        await _application.start()
        _initialized = True
        logger.info("✅ Application initialized and started")
    
    return _application


async def _process_update_async(update_data: dict) -> None:
    """Обрабатывает обновление Telegram асинхронно."""
    # Логируем информацию об обновлении
    if 'message' in update_data and 'from' in update_data['message']:
        user_id = update_data['message']['from'].get('id')
        username = update_data['message']['from'].get('username', 'no username')
        logger.info(f"📨 Processing update from user {user_id} (@{username})")
    
    application = await _get_or_create_application()
    
    # Создаем Update объект из JSON
    update = Update.de_json(update_data, application.bot)
    
    # Обрабатываем обновление
    await application.process_update(update)


class handler(BaseHTTPRequestHandler):
    """Vercel entrypoint. BaseHTTPRequestHandler совместим с @vercel/python."""

    def _send(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802
        """Простой healthcheck."""
        self._send(200, {"status": "ok"})

    def do_POST(self):  # noqa: N802
        """Основной webhook endpoint."""
        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length) if content_length else b""

        try:
            update_data = json.loads(raw_body.decode("utf-8"))
            logger.info(f"📨 Received update: {update_data.get('update_id', 'unknown')}")
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON: {e}")
            self._send(400, {"status": "error", "message": "invalid json"})
            return

        # Сразу возвращаем ответ webhook'у (Telegram требует быстрый ответ)
        self._send(200, {"status": "ok"})
        
        # Обрабатываем обновление в фоне (не блокируем ответ)
        try:
            # Используем asyncio.run() с правильной обработкой
            async def _handle_update():
                try:
                    await _process_update_async(update_data)
                    # Даем время на завершение HTTP запросов
                    await asyncio.sleep(1.0)
                except Exception as e:
                    logger.error(f"Error in _handle_update: {e}")
                    raise
            
            # Запускаем в отдельном потоке, чтобы не блокировать
            import threading
            def _run_async():
                try:
                    asyncio.run(_handle_update())
                except Exception as e:
                    logger.error(f"Error in async thread: {e}")
            
            thread = threading.Thread(target=_run_async, daemon=True)
            thread.start()
            logger.info("✅ Update queued for processing")
                    
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("❌ Failed to queue update: %s", exc)

