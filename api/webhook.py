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

        try:
            # Создаем новый event loop для каждого запроса
            # Это необходимо в serverless окружении Vercel
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Запускаем обработку обновления
                loop.run_until_complete(_process_update_async(update_data))
                
                # Даем время на завершение всех HTTP запросов
                # Ждем завершения всех pending задач
                pending = [t for t in asyncio.all_tasks(loop) if not t.done()]
                if pending:
                    logger.info(f"⏳ Waiting for {len(pending)} pending tasks...")
                    # Ждем завершения с таймаутом
                    try:
                        loop.run_until_complete(asyncio.wait_for(
                            asyncio.gather(*pending, return_exceptions=True),
                            timeout=2.0
                        ))
                    except asyncio.TimeoutError:
                        logger.warning("⚠️ Some tasks didn't complete in time")
                
                logger.info("✅ Update processed successfully")
            finally:
                # Правильно закрываем loop
                try:
                    # Отменяем все оставшиеся задачи
                    for task in asyncio.all_tasks(loop):
                        if not task.done():
                            task.cancel()
                    # Ждем отмены с таймаутом
                    if asyncio.all_tasks(loop):
                        loop.run_until_complete(asyncio.wait_for(
                            asyncio.gather(*asyncio.all_tasks(loop), return_exceptions=True),
                            timeout=1.0
                        ))
                except Exception as e:
                    logger.warning(f"Error during cleanup: {e}")
                finally:
                    loop.close()
                    
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("❌ Webhook processing failed: %s", exc)
            self._send(500, {"status": "error", "message": str(exc)})
            return

        self._send(200, {"status": "ok"})

