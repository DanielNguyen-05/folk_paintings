import httpx
import json
import random
import asyncio
from typing import List, Dict, Any, Optional
from .config import MODEL_REGISTRY

async def query_model(
    model_id: str,
    messages: List[Dict[str, str]],
    timeout: float = 60.0,
    retries: int = 3  # Thêm số lần thử lại
) -> Optional[Dict[str, Any]]:
    config = MODEL_REGISTRY.get(model_id)
    if not config:
        print(f"Error: Model ID '{model_id}' not found.")
        return None

    provider = config["provider"]

    # Vòng lặp thử lại (Retry Loop)
    for attempt in range(retries):
        try:
            if provider in ["openai", "openai_compatible"]:
                return await _call_openai_style(config, messages, timeout)
            elif provider == "google":
                return await _call_google_rest(config, messages, timeout)
        except httpx.HTTPStatusError as e:
            # Nếu gặp lỗi 429 (Too Many Requests), đợi và thử lại
            if e.response.status_code == 429:
                wait_time = (2 ** attempt) + random.uniform(0, 1) # Đợi 1s, 2s, 4s...
                print(f"⚠️ {model_id} bị 429. Đợi {wait_time:.1f}s rồi thử lại...")
                await asyncio.sleep(wait_time)
                continue # Quay lại đầu vòng lặp
            else:
                print(f"Error querying {model_id}: {e}")
                return None
        except Exception as e:
            print(f"Error querying {model_id}: {str(e)}")
            return None
    
    return None

async def _call_openai_style(config, messages, timeout):
    """Xử lý gọi API chuẩn OpenAI (Dùng cho GPT và Local Ollama/vLLM)"""
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": config["model"],
        "messages": messages,
        "temperature": 0.7
    }

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            config["base_url"],
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        
        return {
            'content': data['choices'][0]['message']['content'],
            # OpenAI trả về usage stats, có thể lưu nếu cần
            'model_used': config['model']
        }


async def _call_google_rest(config, messages, timeout):
    """Xử lý gọi Google Gemini qua REST API (Không cần cài thư viện google-genai)"""
    
    # 1. Chuyển đổi format messages từ OpenAI style -> Google style
    google_contents = []
    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        # Google yêu cầu system prompt xử lý riêng hoặc gộp vào user, ở đây ta gộp đơn giản
        if msg["role"] == "system":
            role = "user" 
            
        google_contents.append({
            "role": role,
            "parts": [{"text": msg["content"]}]
        })

    # URL cho Google API key nằm ở query param
    url = f"{config['base_url']}/{config['model']}:generateContent?key={config['api_key']}"
    
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": google_contents,
        "generationConfig": {"temperature": 0.7}
    }

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        
        # Trích xuất text từ response phức tạp của Google
        try:
            content = data['candidates'][0]['content']['parts'][0]['text']
            return {
                'content': content,
                'model_used': config['model']
            }
        except (KeyError, IndexError):
            return {'content': "Error: Empty response from Gemini", 'model_used': config['model']}


async def query_models_parallel(
    model_ids: List[str],
    messages: List[Dict[str, str]]
) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Gọi song song nhiều model ID khác nhau.
    """
    import asyncio
    
    # Tạo tasks
    tasks = [query_model(mid, messages) for mid in model_ids]
    
    # Chạy song song
    responses = await asyncio.gather(*tasks)
    
    # Ghép kết quả vào dict {model_id: response}
    return {mid: resp for mid, resp in zip(model_ids, responses)}