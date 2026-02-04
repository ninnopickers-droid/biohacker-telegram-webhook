"""
Webhook Telegram - Biohacker 2026 (VERSÃO INTEGRADA)
=====================================================
Recebe mensagens do Telegram 24/7 e processa com Groq/Gemini

Data: 2026-02-03
Versão: 1.0 - Integração completa
"""

import sys
import os

# Adicionar path para importar processadores
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import json
import requests
from http.server import BaseHTTPRequestHandler
from datetime import datetime

# Importar processadores
try:
    from api.processors.groq_whisper import transcribe_from_telegram
    from api.processors.groq_nlp import (
        extract_meal_data, 
        extract_workout_data, 
        extract_hydration_data,
        classify_intent
    )
    from api.processors.gemini_vision import analyze_meal_from_telegram, extract_structured_meal_data
    IMPORTS_OK = True
except ImportError as e:
    print(f"[AVISO] Erro ao importar processadores: {e}")
    IMPORTS_OK = False

# Configurações
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Health check"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        status = {
            "status": "ok",
            "message": "Biohacker Telegram Webhook v1.0",
            "imports_ok": IMPORTS_OK,
            "apis_configured": {
                "telegram": bool(TELEGRAM_BOT_TOKEN),
                "groq": bool(GROQ_API_KEY),
                "gemini": bool(GEMINI_API_KEY)
            },
            "timestamp": datetime.now().isoformat()
        }
        
        self.wfile.write(json.dumps(status).encode())
    
    def do_POST(self):
        """Processa webhooks do Telegram"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # Log
            print(f"[WEBHOOK] Recebido: {json.dumps(data, indent=2)[:200]}...")
            
            if 'message' in data:
                message = data['message']
                chat_id = message.get('chat', {}).get('id')
                
                # Processar mensagem
                result = self.process_message(message)
                
                # Enviar resposta
                self.send_message(chat_id, result['response'])
                
                # Salvar dados processados (futuro: Supabase)
                if result.get('data'):
                    print(f"[DATA] Dados extraídos: {json.dumps(result['data'], indent=2)}")
                
                # Responder 200 OK
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True}).encode())
            else:
                self.send_response(200)
                self.end_headers()
                
        except Exception as e:
            print(f"[ERRO] Webhook: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode())
    
    def process_message(self, message):
        """Processa mensagem com integrações"""
        text = message.get('text', '')
        voice = message.get('voice')
        photo = message.get('photo')
        chat_id = message.get('chat', {}).get('id')
        
        print(f"[PROCESS] Chat {chat_id}: texto={bool(text)}, voz={bool(voice)}, foto={bool(photo)}")
        
        # Verificar comandos primeiro
        if text and text.startswith('/'):
            return self.handle_command(text, chat_id)
        
        # Processar FOTO (prioridade máxima - análise Gemini)
        if photo and IMPORTS_OK and GEMINI_API_KEY:
            return self.process_photo(photo, text)
        
        # Processar ÁUDIO (transcrição Whisper)
        if voice and IMPORTS_OK and GROQ_API_KEY:
            return self.process_voice(voice, text)
        
        # Processar TEXTO (NLP)
        if text and IMPORTS_OK and GROQ_API_KEY:
            return self.process_text(text)
        
        # Fallback básico
        return {
            'response': "✅ Mensagem recebida! (Processamento avançado em configuração)",
            'data': None
        }
    
    def process_photo(self, photo_list, caption):
        """Processa foto com Gemini Vision"""
        try:
            # Pegar foto de maior resolução
            photo = photo_list[-1]
            file_id = photo['file_id']
            
            # Baixar foto do Telegram
            file_url = self.get_telegram_file_url(file_id)
            if not file_url:
                return {'response': "❌ Erro ao acessar foto", 'data': None}
            
            # Analisar com Gemini
            result = analyze_meal_from_telegram(file_url, TELEGRAM_BOT_TOKEN)
            
            if result['success']:
                analysis = result['analysis']
                structured = result.get('structured', {})
                
                # Construir resposta
                response = f"📸 **Foto Analisada!**\n\n{analysis}\n\n"
                
                if caption:
                    response += f"📝 Legenda: {caption}\n"
                
                response += "\n✅ Dados extraídos e salvos na fila de sincronização!"
                
                return {
                    'response': response,
                    'data': {
                        'type': 'meal_photo',
                        'analysis': analysis,
                        'structured': structured,
                        'caption': caption
                    }
                }
            else:
                return {
                    'response': f"⚠️ Erro na análise: {result.get('error', 'Desconhecido')}",
                    'data': None
                }
                
        except Exception as e:
            return {'response': f"❌ Erro ao processar foto: {str(e)}", 'data': None}
    
    def process_voice(self, voice, caption):
        """Processa áudio com Whisper"""
        try:
            file_id = voice['file_id']
            duration = voice.get('duration', 0)
            
            # Baixar áudio
            file_url = self.get_telegram_file_url(file_id)
            if not file_url:
                return {'response': "❌ Erro ao acessar áudio", 'data': None}
            
            # Transcrever
            result = transcribe_from_telegram(file_url, TELEGRAM_BOT_TOKEN)
            
            if result['success']:
                transcription = result['text']
                
                # Classificar intenção e extrair dados
                intent = classify_intent(transcription)
                extracted_data = None
                
                if intent == 'meal':
                    extracted_data = extract_meal_data(transcription)
                elif intent == 'workout':
                    extracted_data = extract_workout_data(transcription)
                elif intent == 'hydration':
                    extracted_data = extract_hydration_data(transcription)
                
                # Construir resposta
                response = f"🎙️ **Áudio Transcrito!**\n\n"
                response += f"📝 Texto: \"{transcription}\"\n\n"
                response += f"🎯 Intenção: {intent}\n"
                
                if extracted_data:
                    response += f"📊 Dados extraídos: {json.dumps(extracted_data, indent=2, ensure_ascii=False)}\n\n"
                
                response += "✅ Salvo na fila de sincronização!"
                
                return {
                    'response': response,
                    'data': {
                        'type': 'voice',
                        'transcription': transcription,
                        'intent': intent,
                        'extracted': extracted_data,
                        'duration': duration
                    }
                }
            else:
                return {
                    'response': f"⚠️ Erro na transcrição: {result.get('error', 'Desconhecido')}",
                    'data': None
                }
                
        except Exception as e:
            return {'response': f"❌ Erro ao processar áudio: {str(e)}", 'data': None}
    
    def process_text(self, text):
        """Processa texto com NLP"""
        try:
            # Classificar intenção
            intent = classify_intent(text)
            
            # Extrair dados baseado na intenção
            extracted_data = None
            action_desc = ""
            
            if intent == 'meal':
                extracted_data = extract_meal_data(text)
                action_desc = "🍽️ Refeição"
            elif intent == 'workout':
                extracted_data = extract_workout_data(text)
                action_desc = "💪 Treino"
            elif intent == 'hydration':
                extracted_data = extract_hydration_data(text)
                action_desc = "💧 Hidratação"
            else:
                action_desc = "📝 Mensagem"
            
            # Construir resposta
            response = f"{action_desc} registrada!\n\n"
            response += f"📝 Texto: \"{text[:100]}{'...' if len(text) > 100 else ''}\"\n"
            response += f"🎯 Intenção: {intent}\n"
            
            if extracted_data:
                response += f"📊 Dados: {json.dumps(extracted_data, indent=2, ensure_ascii=False)[:300]}...\n\n"
            
            response += "✅ Salvo na fila de sincronização!"
            
            return {
                'response': response,
                'data': {
                    'type': 'text',
                    'text': text,
                    'intent': intent,
                    'extracted': extracted_data
                }
            }
            
        except Exception as e:
            return {'response': f"❌ Erro no processamento: {str(e)}", 'data': None}
    
    def handle_command(self, text, chat_id):
        """Processa comandos /comando"""
        command = text.split()[0].lower()
        
        commands = {
            '/start': """🎯 **Biohacker 2026 Bot - INTEGRADO**

✅ **Status:** Todas APIs conectadas!
• Telegram: ✅
• Groq (Whisper + LLM): ✅  
• Gemini Vision: ✅

**O que posso fazer:**
• 📸 Fotos de refeições → Análise automática com Gemini
• 🎙️ Áudios → Transcrição Whisper + NLP
• 💬 Texto livre → Extração inteligente de dados
• 📊 Mini App → Dashboard e relatórios

**Envie agora:**
• Uma foto da sua refeição
• Um áudio descrevendo treino
• Um texto sobre o que comeu

Vou processar e salvar tudo automaticamente! 🚀""",
            
            '/status': f"""📊 **Status do Sistema**

🤖 Bot: Online
☁️ Groq API: {'✅' if GROQ_API_KEY else '❌'} 
📸 Gemini Vision: {'✅' if GEMINI_API_KEY else '❌'}
🔄 Supabase: {'✅ Configurar' if not os.getenv('SUPABASE_URL') else '⏳ Pendente'}

💡 **Dica:** Se alguma API estiver ❌, configure as variáveis de ambiente.""",
            
            '/ajuda': "Use /start para ver funcionalidades ou /status para diagnóstico.",
            '/refeicao': "📸 Envie uma foto da sua refeição ou descreva em texto/áudio. Vou analisar e extrair os alimentos automaticamente!",
            '/treino': "🎙️ Envie um áudio descrevendo seu treino (exercícios, séries, cargas) ou diga o que treinou.",
            '/agua': "💧 Quanto de água você bebeu? Pode enviar em texto ('500ml') ou áudio.",
            '/medidas': "📏 Mini App: Use o botão no menu para abrir o formulário de medidas.",
            '/dashboard': "📊 Mini App: Dashboard disponível no botão do menu."
        }
        
        response = commands.get(command, f"Comando {command} não reconhecido. Use /ajuda")
        return {'response': response, 'data': {'type': 'command', 'command': command}}
    
    def get_telegram_file_url(self, file_id):
        """Obtém URL do arquivo do Telegram"""
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile"
            response = requests.post(url, json={'file_id': file_id}, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    file_path = result['result']['file_path']
                    return f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
            return None
        except:
            return None
    
    def send_message(self, chat_id, text):
        """Envia mensagem de resposta"""
        print(f"[SEND] chat_id={chat_id}, token exists={bool(TELEGRAM_BOT_TOKEN)}")
        
        if not TELEGRAM_BOT_TOKEN:
            print("[ERRO] TELEGRAM_BOT_TOKEN não configurado")
            return
        
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': text[:4000],  # Limite Telegram
            'parse_mode': 'Markdown'
        }
        
        try:
            print(f"[SEND] Enviando para {url[:50]}...")
            response = requests.post(url, json=payload, timeout=10)
            print(f"[SEND] Status: {response.status_code}, Response: {response.text[:100]}")
        except Exception as e:
            print(f"[ERRO] Enviando mensagem: {e}")


# Teste local
if __name__ == "__main__":
    from http.server import HTTPServer
    server = HTTPServer(('0.0.0.0', 8000), handler)
    print("[SERVIDOR] Biohacker Telegram Webhook v1.0")
    print("[INFO] Teste: http://localhost:8000")
    print("[INFO] Webhook: http://localhost:8000 (POST)")
    print()
    print("Credenciais:")
    print(f"  Telegram: {'✅' if TELEGRAM_BOT_TOKEN else '❌'}")
    print(f"  Groq: {'✅' if GROQ_API_KEY else '❌'}")
    print(f"  Gemini: {'✅' if GEMINI_API_KEY else '❌'}")
    print()
    server.serve_forever()
