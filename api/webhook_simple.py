"""
Webhook Telegram - Biohacker 2026 (VERSÃO SIMPLIFICADA DE TESTE)
===============================================================
Versão mínima para testar se o Telegram está conseguindo comunicar
"""

import os
import json
import requests
from http.server import BaseHTTPRequestHandler

def get_token():
    """Lê token de ambiente"""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        token = os.getenv("TOKEN", "")
    if not token:
        token = os.getenv("BOT_TOKEN", "")
    return token


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Health check"""
        token = get_token()
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        status = {
            "status": "ok",
            "message": "Webhook Test v2.1",
            "token_exists": bool(token),
            "token_length": len(token) if token else 0,
            "timestamp": __import__('datetime').datetime.now().isoformat()
        }
        
        self.wfile.write(json.dumps(status).encode())
    
    def do_POST(self):
        """Processa webhooks do Telegram"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "No content"}).encode())
                return
            
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # Extrair dados da mensagem
            message = data.get('message', {})
            chat_id = message.get('chat', {}).get('id')
            text = message.get('text', '')
            
            # Pegar token
            token = get_token()
            
            if chat_id and text and token:
                # Enviar resposta via Telegram API
                self.send_telegram_message(chat_id, f"✅ Recebido: {text}", token)
            
            # Sempre responder 200 OK para o Telegram
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode())
            
        except Exception as e:
            print(f"[ERRO] Webhook: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode())
    
    def send_telegram_message(self, chat_id, text, token):
        """Envia mensagem de resposta via Telegram API"""
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': text
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"[ERRO] Enviando: {e}")
            return False


if __name__ == "__main__":
    from http.server import HTTPServer
    server = HTTPServer(('0.0.0.0', 8000), handler)
    print("[TEST] Servidor rodando em http://localhost:8000")
    server.serve_forever()
