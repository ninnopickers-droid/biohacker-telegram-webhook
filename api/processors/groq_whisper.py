"""
Groq Whisper Integration - Transcrição de Áudio
=================================================
Converte mensagens de voz do Telegram em texto

Data: 2026-02-03
"""

import os
import requests
import base64
from typing import Optional, Dict, Any

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_WHISPER_URL = "https://api.groq.com/openai/v1/audio/transcriptions"


def transcribe_audio(file_path: str, language: str = "pt") -> Dict[str, Any]:
    """
    Transcreve arquivo de áudio usando Groq Whisper
    
    Args:
        file_path: Caminho do arquivo de áudio (.ogg, .mp3, etc)
        language: Código do idioma (pt, en, es)
    
    Returns:
        Dict com: text, language, duration, confidence
    """
    if not GROQ_API_KEY:
        return {
            "success": False,
            "error": "GROQ_API_KEY não configurada",
            "text": ""
        }
    
    try:
        with open(file_path, 'rb') as audio_file:
            files = {
                'file': (os.path.basename(file_path), audio_file, 'audio/ogg')
            }
            
            data = {
                'model': 'whisper-large-v3',
                'language': language,
                'response_format': 'json'
            }
            
            headers = {
                'Authorization': f'Bearer {GROQ_API_KEY}'
            }
            
            response = requests.post(
                GROQ_WHISPER_URL,
                headers=headers,
                files=files,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "text": result.get("text", ""),
                    "language": result.get("language", language),
                    "duration": result.get("duration", 0),
                    "confidence": 0.95  # Whisper é muito preciso
                }
            else:
                return {
                    "success": False,
                    "error": f"API Error {response.status_code}: {response.text}",
                    "text": ""
                }
                
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "text": ""
        }


def transcribe_from_telegram(file_url: str, bot_token: str, language: str = "pt") -> Dict[str, Any]:
    """
    Baixa áudio do Telegram e transcreve
    
    Args:
        file_url: URL do arquivo do Telegram
        bot_token: Token do bot
        language: Idioma
    
    Returns:
        Dict com resultado da transcrição
    """
    try:
        # Baixar áudio do Telegram
        response = requests.get(file_url, timeout=30)
        if response.status_code != 200:
            return {
                "success": False,
                "error": f"Erro ao baixar áudio: {response.status_code}",
                "text": ""
            }
        
        # Salvar temporariamente
        temp_path = "/tmp/voice_message.ogg"
        with open(temp_path, 'wb') as f:
            f.write(response.content)
        
        # Transcrever
        result = transcribe_audio(temp_path, language)
        
        # Limpar arquivo temporário
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "text": ""
        }


if __name__ == "__main__":
    # Teste
    import sys
    sys.path.insert(0, '..')
    
    print("[TESTE] Groq Whisper Integration")
    print("Para testar, defina GROQ_API_KEY e execute:")
    print("python groq_whisper.py")
    print()
    print("Limite gratuito: 20 requests/minuto, 1.44M tokens/dia")
