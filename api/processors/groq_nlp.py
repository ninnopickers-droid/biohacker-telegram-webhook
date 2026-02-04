"""
Groq LLM Integration - NLP e Extração de Dados
================================================
Processa texto natural e extrai dados estruturados

Data: 2026-02-03
"""

import os
import json
import requests
from typing import Dict, Any, Optional

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"


def extract_meal_data(text: str) -> Dict[str, Any]:
    """
    Extrai dados de refeição de texto natural
    
    Args:
        text: Texto descrevendo a refeição
    
    Returns:
        Dict estruturado com alimentos e quantidades
    """
    prompt = f"""Analise este texto e extraia dados da refeição em formato JSON.

Texto: "{text}"

Extraia:
1. Tipo de refeição (café_da_manha, almoço, jantar, lanche)
2. Lista de alimentos com quantidades estimadas em gramas
3. Horário se mencionado
4. Observações relevantes

Responda APENAS com JSON válido, exemplo:
{{
    "tipo": "almoço",
    "horario": "12:30",
    "alimentos": [
        {{"nome": "arroz_branco", "quantidade_g": 150, "descricao": "cozido"}},
        {{"nome": "feijao_carioca", "quantidade_g": 100, "descricao": ""}},
        {{"nome": "peito_frango", "quantidade_g": 120, "descricao": "grelhado"}},
        {{"nome": "salada_verde", "quantidade_g": 80, "descricao": "alface e tomate"}}
    ],
    "observacoes": ""
}}

JSON:"""
    
    return _call_groq(prompt, model="llama-3.1-8b-instant")


def extract_workout_data(text: str) -> Dict[str, Any]:
    """
    Extrai dados de treino de texto natural
    
    Args:
        text: Texto descrevendo o treino
    
    Returns:
        Dict estruturado com exercícios
    """
    prompt = f"""Analise este texto e extraia dados do treino em formato JSON.

Texto: "{text}"

Extraia:
1. Grupo muscular (peito, costas, pernas, ombros, bracos, etc)
2. Lista de exercícios com séries, repetições e carga
3. Horário se mencionado
4. Observações (RPE, técnica, etc)

Responda APENAS com JSON válido, exemplo:
{{
    "grupo_muscular": "peito",
    "horario": "18:00",
    "exercicios": [
        {{"nome": "supino_reto", "series": 4, "repeticoes": "8-10", "carga_kg": 80}},
        {{"nome": "crucifixo_halteres", "series": 3, "repeticoes": 12, "carga_kg": 20}},
        {{"nome": "supino_inclinado", "series": 3, "repeticoes": 10, "carga_kg": 60}}
    ],
    "observacoes": "Foco na contração, RPE 8-9"
}}

JSON:"""
    
    return _call_groq(prompt, model="llama-3.1-8b-instant")


def extract_hydration_data(text: str) -> Dict[str, Any]:
    """
    Extrai dados de hidratação
    
    Args:
        text: Texto sobre consumo de água
    
    Returns:
        Dict com quantidade e tipo
    """
    prompt = f"""Analise e extraia dados de hidratação em JSON.

Texto: "{text}"

Extraia:
1. Quantidade em ml
2. Tipo (agua, cha, cafe, suco, etc)
3. Horário se mencionado

Exemplo:
{{
    "tipo": "agua",
    "quantidade_ml": 500,
    "horario": "14:30",
    "observacoes": ""
}}

JSON:"""
    
    return _call_groq(prompt, model="llama-3.1-8b-instant")


def classify_intent(text: str) -> str:
    """
    Classifica a intenção do usuário
    
    Args:
        text: Texto do usuário
    
    Returns:
        Categoria: meal, workout, hydration, question, greeting, other
    """
    prompt = f"""Classifique a intenção deste texto em UMA palavra:
- meal (refeição)
- workout (treino)
- hydration (hidratacao)
- supplement (suplemento)
- question (duvida)
- greeting (saudacao)
- other (outro)

Texto: "{text}"

Resposta (apenas uma palavra):"""
    
    result = _call_groq(prompt, model="gemma2-9b-it", json_mode=False)
    intent = result.get("text", "other").strip().lower()
    
    valid_intents = ["meal", "workout", "hydration", "supplement", "question", "greeting", "other"]
    return intent if intent in valid_intents else "other"


def _call_groq(prompt: str, model: str = "llama-3.1-8b-instant", json_mode: bool = True) -> Dict[str, Any]:
    """Chama API Groq"""
    
    if not GROQ_API_KEY:
        return {"success": False, "error": "GROQ_API_KEY não configurada"}
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 1000
    }
    
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    
    try:
        response = requests.post(
            GROQ_CHAT_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            if json_mode:
                try:
                    return json.loads(content)
                except:
                    return {"success": False, "error": "JSON inválido", "raw": content}
            else:
                return {"success": True, "text": content}
        else:
            return {
                "success": False,
                "error": f"API Error {response.status_code}: {response.text}"
            }
            
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    # Testes
    print("[TESTE] Groq LLM Integration\n")
    
    # Teste 1: Refeição
    text1 = "Almocei 200g de arroz com feijão e um peito de frango grelhado"
    print(f"Texto: {text1}")
    result1 = extract_meal_data(text1)
    print(f"Resultado: {json.dumps(result1, indent=2, ensure_ascii=False)}\n")
    
    # Teste 2: Treino
    text2 = "Treinei peito hoje, supino reto 4 séries de 8 com 80kg"
    print(f"Texto: {text2}")
    result2 = extract_workout_data(text2)
    print(f"Resultado: {json.dumps(result2, indent=2, ensure_ascii=False)}\n")
    
    # Teste 3: Classificação
    text3 = "Bebi 500ml de água agora"
    print(f"Texto: {text3}")
    result3 = classify_intent(text3)
    print(f"Intenção: {result3}\n")
