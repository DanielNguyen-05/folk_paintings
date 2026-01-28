import httpx
import random
import asyncio
import base64
from typing import List, Dict, Any, Optional
from .config import MODEL_REGISTRY

async def query_model(
    model_id: str,
    messages: List[Dict[str, str]],
    timeout: float = 60.0,
    retries: int = 3,
    image_data: Optional[bytes] = None,
    image_mime_type: str = "image/jpeg",
    image_url: Optional[str] = None 
) -> Optional[Dict[str, Any]]:
    config = MODEL_REGISTRY.get(model_id)
    if not config:
        print(f"Error: Model ID '{model_id}' not found.")
        return None

    provider = config["provider"]

    # Xử lý Logic Image: Nếu có URL mà chưa có Data, thử tải ảnh về
    # Điều này giúp Google Gemini (REST) có thể xử lý được ảnh từ URL
    if image_url and not image_data and provider == "google":
        image_data, image_mime_type = await _download_image_from_url(image_url)

    # Vòng lặp thử lại (Retry Loop)
    for attempt in range(retries):
        try:
            if provider == "openai":
                return await _call_openai_style(config, messages, timeout, image_url=image_url, image_data=image_data)
            elif provider == "google":
                # Ưu tiên dùng REST API cho mọi trường hợp để giảm phụ thuộc thư viện
                return await _call_google_rest(config, messages, timeout, image_data, image_mime_type)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"⚠️ {model_id} bị 429. Đợi {wait_time:.1f}s rồi thử lại...")
                await asyncio.sleep(wait_time)
                continue
            else:
                print(f"Error querying {model_id}: {e}")
                return None
        except Exception as e:
            print(f"Error querying {model_id}: {str(e)}")
            return None
    
    return None

async def _download_image_from_url(url: str) -> tuple[Optional[bytes], str]:
    """Helper: Tải ảnh từ URL để chuyển cho các model không hỗ trợ URL trực tiếp"""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=10.0)
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "image/jpeg")
            return resp.content, content_type
    except Exception as e:
        print(f"Warning: Failed to download image from {url}: {e}")
        return None, "image/jpeg"

async def _call_openai_style(config, messages, timeout, image_url: str = None, image_data: bytes = None): 
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
    }
    
    final_messages = []
    
    if image_url or image_data:
            # Lấy message cuối cùng của user
            # Lưu ý: Cần copy messages để tránh sửa đổi list gốc
            final_messages = [msg for msg in messages[:-1]] 
            last_msg = messages[-1]
            
            content_payload = [{"type": "text", "text": last_msg["content"]}]

            if image_url:
                # Ưu tiên URL nếu có (tiết kiệm bandwidth upload)
                content_payload.append({
                    "type": "image_url",
                    "image_url": {"url": image_url, "detail": "auto"}
                })
            elif image_data:
                # Nếu là file local, dùng Base64
                b64_image = base64.b64encode(image_data).decode('utf-8')
                content_payload.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{b64_image}", # Format chuẩn cho OpenAI
                        "detail": "auto"
                    }
                })

            final_messages.append({
                "role": "user",
                "content": content_payload
            })
    payload = {
        "model": config["model"],
        "messages": final_messages,
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
            'model_used': config['model']
        }

async def _call_google_rest(config, messages, timeout, image_data: bytes = None, image_mime_type: str = "image/jpeg"):
    """
    Xử lý gọi Google Gemini qua REST API.
    Hỗ trợ cả Text và Image (dưới dạng Inline Data base64).
    """
    
    # Chuẩn bị nội dung cho Google
    # Lưu ý: Google REST API cấu trúc content là danh sách các parts
    parts = []
    
    # 1. Thêm hình ảnh nếu có (phải đưa lên trước text theo khuyến nghị)
    if image_data:
        b64_image = base64.b64encode(image_data).decode('utf-8')
        parts.append({
            "inline_data": {
                "mime_type": image_mime_type,
                "data": b64_image
            }
        })

    # 2. Thêm text từ message cuối cùng của user
    # (Google thường xử lý tốt nhất khi gộp prompt lại, nhưng ở đây ta lấy msg cuối)
    last_user_msg = next((m for m in reversed(messages) if m["role"] == "user"), None)
    if last_user_msg:
        parts.append({"text": last_user_msg["content"]})
    else:
        # Fallback nếu không tìm thấy user msg (hiếm gặp)
        parts.append({"text": "Please process this request."})

    google_contents = [{
        "role": "user",
        "parts": parts
    }]

    # Xử lý system prompt (nếu có) bằng cách đưa vào system_instruction (cho các model mới)
    # hoặc gộp vào user prompt (cho model cũ). Ở đây dùng cách gộp đơn giản nếu cần.
    
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
        
        try:
            content = data['candidates'][0]['content']['parts'][0]['text']
            return {
                'content': content,
                'model_used': config['model']
            }
        except (KeyError, IndexError):
            # Log raw response để debug nếu cần
            # print(f"Debug Google Resp: {data}")
            return {'content': "Error: Empty response from Gemini", 'model_used': config['model']}

async def query_models_parallel(
    model_ids: List[str],
    messages: List[Dict[str, str]],
    image_data: Optional[bytes] = None,
    image_mime_type: str = "image/jpeg",
    image_url: Optional[str] = None 
) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Gọi song song nhiều model ID khác nhau.
    """
    tasks = [
        query_model(
            mid, messages, 
            image_data=image_data, 
            image_mime_type=image_mime_type, 
            image_url=image_url
        ) 
        for mid in model_ids
    ]
    responses = await asyncio.gather(*tasks)
    return {mid: resp for mid, resp in zip(model_ids, responses)}