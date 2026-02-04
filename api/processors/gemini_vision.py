"""
Gemini Vision Integration - Análise de Fotos
=============================================
Analisa fotos de refeições e identifica alimentos

Data: 2026-02-03
"""

import os
import json
import base64
import requests
from typing import Dict, Any, Optional
from io import BytesIO

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_VISION_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"


def analyze_meal_photo(image_data: bytes, mime_type: str = "image/jpeg") -> Dict[str, Any]:
    """
    Analisa foto de refeição usando Gemini Vision
    
    Args:
        image_data: Bytes da imagem
        mime_type: Tipo MIME (image/jpeg, image/png)
    
    Returns:
        Dict com análise dos alimentos
    """
    if not GEMINI_API_KEY:
        return {
            "success": False,
            "error": "GEMINI_API_KEY não configurada",
            "analysis": ""
        }
    
    try:
        # Codificar imagem em base64
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        
        # Prompt para análise de refeição
        prompt = """Analise esta foto de refeição e identifique os alimentos visíveis.

Forneça:
1. Lista de alimentos identificados
2. Quantidades estimadas em gramas
3. Descrição do preparo (grelhado, cozido, frito, etc)
4. Estimativa calórica total

Responda em português, formato estruturado.

Exemplo:
Alimentos identificados:
- Arroz branco: ~150g (cozido)
- Feijão carioca: ~100g (cozido)
- Peito de frango: ~120g (grelhado)
- Salada (alface/tomate): ~80g

Estimativa: ~650 kcal | Proteínas: ~40g | Carboidratos: ~75g | Gorduras: ~18g

Seja preciso nas estimativas baseado no tamanho do prato e referências visuais."""

        # Construir payload
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": image_b64
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": 1024
            }
        }
        
        # Fazer requisição
        url = f"{GEMINI_VISION_URL}?key={GEMINI_API_KEY}"
        
        response = requests.post(
            url,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Extrair texto da resposta
            candidates = result.get("candidates", [])
            if candidates:
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                
                analysis_text = ""
                for part in parts:
                    analysis_text += part.get("text", "")
                
                return {
                    "success": True,
                    "analysis": analysis_text,
                    "raw_response": result
                }
            else:
                return {
                    "success": False,
                    "error": "Sem candidatos na resposta",
                    "raw_response": result
                }
        else:
            return {
                "success": False,
                "error": f"API Error {response.status_code}: {response.text}",
                "analysis": ""
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "analysis": ""
        }


def extract_structured_meal_data(analysis_text: str) -> Dict[str, Any]:
    """
    Extrai dados estruturados do texto de análise do Gemini
    
    Args:
        analysis_text: Texto da análise do Gemini
    
    Returns:
        Dict estruturado com alimentos
    """
    # Implementação simplificada (pode ser melhorada com regex ou NLP adicional)
    lines = analysis_text.split('\n')
    
    alimentos = []
    total_calorias = 0
    total_proteinas = 0
    
    for line in lines:
        line = line.strip()
        if line.startswith('-') or line.startswith('•'):
            # Tentar extrair alimento e quantidade
            # Exemplo: "- Arroz branco: ~150g (cozido)"
            parts = line[1:].strip().split(':')
            if len(parts) >= 2:
                nome = parts[0].strip()
                resto = ':'.join(parts[1:]).strip()
                
                # Tentar extrair gramas
                import re
                match = re.search(r'(\d+)g', resto)
                quantidade = int(match.group(1)) if match else 0
                
                alimentos.append({
                    "nome": nome,
                    "quantidade_g": quantidade,
                    "descricao": resto
                })
        
        # Tentar extrair calorias totais
        if "kcal" in line.lower():
            import re
            match = re.search(r'(\d+)\s*kcal', line.lower())
            if match:
                total_calorias = int(match.group(1))
    
    return {
        "alimentos": alimentos,
        "total_calorias_estimada": total_calorias,
        "analise_completa": analysis_text
    }


def analyze_meal_from_telegram(file_url: str, bot_token: str) -> Dict[str, Any]:
    """
    Baixa foto do Telegram e analisa
    
    Args:
        file_url: URL do arquivo do Telegram
        bot_token: Token do bot
    
    Returns:
        Dict com análise
    """
    try:
        # Baixar foto
        response = requests.get(file_url, timeout=30)
        if response.status_code != 200:
            return {
                "success": False,
                "error": f"Erro ao baixar foto: {response.status_code}",
                "analysis": ""
            }
        
        # Analisar
        result = analyze_meal_photo(response.content)
        
        # Se sucesso, extrair dados estruturados
        if result["success"]:
            structured = extract_structured_meal_data(result["analysis"])
            result["structured"] = structured
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "analysis": ""
        }


if __name__ == "__main__":
    print("[TESTE] Gemini Vision Integration")
    print("Limite gratuito: 1,500 imagens/mês")
    print("Para testar, forneça uma imagem")
    print()
    print("Exemplo de uso:")
    print("python gemini_vision.py")
    print()
    print("Ou teste via webhook com foto real")
