"""
Webhook Telegram - Biohacker 2026 (VERSÃO SIMPLIFICADA DE TESTE)
===============================================================
Versão mínima para testar se o Telegram está conseguindo comunicar
"""

import os
import json
import requests
from http.server import BaseHTTPRequestHandler

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Health check"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        status = {
            "status": "ok",
            "message": "Webhook Test v2.0",
            "token_exists": bool(TELEGRAM_BOT_TOKEN),
            "token_length": len(TELEGRAM_BOT_TOKEN) if TELEGRAM_BOT_TOKEN else 0,
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
            
            print(f"[WEBHOOK] Recebido: {json.dumps(data, indent=2)[:300]}")
            
            # Extrair dados da mensagem
            message = data.get('message', {})
            chat_id = message.get('chat', {}).get('id')
            text = message.get('text', '')
            
            print(f"[WEBHOOK] chat_id={chat_id}, text={text}")
            
            if chat_id and text:
                # Resposta simples
                response_text = f"✅ Recebido: {text}\n\nChat ID: {chat_id}"
                
                # Enviar resposta
                self.send_telegram_message(chat_id, response_text)
            
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
    
    def send_telegram_message(self, chat_id, text):
        """Envia mensagem de resposta via Telegram API"""
        print(f"[SEND] Tentando enviar para chat_id={chat_id}")
        print(f"[SEND] Token exists: {bool(TELEGRAM_BOT_TOKEN)}")
        
        if not TELEGRAM_BOT_TOKEN:
            print("[SEND] ERRO: Token não configurado!")
            return False
        
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': text
        }
        
        try:
            print(f"[SEND] POST para Telegram API...")
            response = requests.post(url, json=payload, timeout=10)
            print(f"[SEND] Status: {response.status_code}")
            print(f"[SEND] Response: {response.text}")
            return response.status_code == 200
        except Exception as e:
            print(f"[SEND] ERRO: {e}")
            return False


if __name__ == "__main__":
    from http.server import HTTPServer
    server = HTTPServer(('0.0.0.0', 8000), handler)
    print("[TEST] Servidor rodando em http://localhost:8000")
    server.serve_forever()
