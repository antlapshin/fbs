from http.server import BaseHTTPRequestHandler
import json


class handler(BaseHTTPRequestHandler):
    """Обработчик для корневого пути - healthcheck"""
    
    def do_GET(self):
        """Возвращает статус бота"""
        response = {
            "status": "ok",
            "message": "🤖 Magnit Bot is running on Vercel!",
            "webhook": "/api/webhook"
        }
        body = json.dumps(response).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    
    def do_POST(self):
        """POST тоже возвращает статус"""
        self.do_GET()

