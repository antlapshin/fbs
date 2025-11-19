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

        # Обрабатываем обновление синхронно, но возвращаем ответ быстро
        try:
            # Создаем новый event loop для обработки
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Запускаем обработку обновления
                logger.info("🔄 Processing update...")
                loop.run_until_complete(_process_update_async(update_data))
                logger.info("✅ Update processed, waiting for HTTP requests...")
                
                # Даем время на завершение HTTP запросов к Telegram API
                # Но не ждем слишком долго (таймаут 3 секунды)
                pending = [t for t in asyncio.all_tasks(loop) if not t.done()]
                if pending:
                    logger.info(f"⏳ Waiting for {len(pending)} pending HTTP requests...")
                    try:
                        loop.run_until_complete(asyncio.wait_for(
                            asyncio.gather(*pending, return_exceptions=True),
                            timeout=3.0
                        ))
                        logger.info("✅ All HTTP requests completed")
                    except asyncio.TimeoutError:
                        logger.warning("⚠️ Some HTTP requests didn't complete in time (this is OK)")
                
            except Exception as e:
                logger.error(f"❌ Error processing update: {e}", exc_info=True)
                raise
            finally:
                # Правильно закрываем loop
                try:
                    # Отменяем все оставшиеся задачи
                    remaining = [t for t in asyncio.all_tasks(loop) if not t.done()]
                    if remaining:
                        logger.info(f"🔄 Cancelling {len(remaining)} remaining tasks...")
                        for task in remaining:
                            task.cancel()
                        try:
                            loop.run_until_complete(asyncio.wait_for(
                                asyncio.gather(*remaining, return_exceptions=True),
                                timeout=1.0
                            ))
                        except asyncio.TimeoutError:
                            pass
                except Exception as e:
                    logger.warning(f"Error during cleanup: {e}")
                finally:
                    loop.close()
            
            # Возвращаем успешный ответ
            self._send(200, {"status": "ok"})
                    
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("❌ Webhook processing failed: %s", exc)
            self._send(500, {"status": "error", "message": str(exc)})
            return

