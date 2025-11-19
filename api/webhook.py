import asyncio
import json
import logging
import threading
from http.server import BaseHTTPRequestHandler

from bot import initialize_application, process_update_with_application


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_loop = asyncio.new_event_loop()
_application = None
_ready_event = threading.Event()


def _loop_runner():
    """Фоновый поток, который крутит event loop для Telegram Application."""
    asyncio.set_event_loop(_loop)

    async def _bootstrap():
        global _application
        _application = await initialize_application()
        logger.info("✅ Telegram application initialized for webhook mode")
        _ready_event.set()

    _loop.create_task(_bootstrap())
    _loop.run_forever()


threading.Thread(target=_loop_runner, daemon=True, name="TelegramLoop").start()


def _process_update(update_data: dict) -> None:
    """Прокидывает обновление в приложение внутри фонового event loop."""
    if not _ready_event.wait(timeout=10):
        raise RuntimeError("Telegram application failed to initialize")

    async def _run():
        await process_update_with_application(update_data, _application)

    future = asyncio.run_coroutine_threadsafe(_run(), _loop)
    future.result(timeout=20)


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
        except json.JSONDecodeError:
            self._send(400, {"status": "error", "message": "invalid json"})
            return

        try:
            _process_update(update_data)
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Webhook processing failed: %s", exc)
            self._send(500, {"status": "error", "message": "webhook failure"})
            return

        self._send(200, {"status": "ok"})

