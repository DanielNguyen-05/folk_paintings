"""JSON-based storage for conversations."""

import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from .config import DATA_DIR

def ensure_data_dir():
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)

def get_conversation_path(conversation_id: str) -> str:
    return os.path.join(DATA_DIR, f"{conversation_id}.json")

def create_conversation(conversation_id: str) -> Dict[str, Any]:
    ensure_data_dir()
    conversation = {
        "id": conversation_id,
        "created_at": datetime.utcnow().isoformat(),
        "title": "New Session",
        "messages": []
    }
    save_conversation(conversation)
    return conversation

def get_conversation(conversation_id: str) -> Optional[Dict[str, Any]]:
    path = get_conversation_path(conversation_id)
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_conversation(conversation: Dict[str, Any]):
    ensure_data_dir()
    path = get_conversation_path(conversation['id'])
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(conversation, f, indent=2, ensure_ascii=False)

def list_conversations() -> List[Dict[str, Any]]:
    ensure_data_dir()
    conversations = []
    if os.path.exists(DATA_DIR):
        for filename in os.listdir(DATA_DIR):
            if filename.endswith('.json'):
                try:
                    path = os.path.join(DATA_DIR, filename)
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        conversations.append({
                            "id": data["id"],
                            "created_at": data["created_at"],
                            "title": data.get("title", "New Conversation"),
                            "message_count": len(data["messages"])
                        })
                except Exception:
                    continue
    conversations.sort(key=lambda x: x["created_at"], reverse=True)
    return conversations

def add_user_message(
    conversation_id: str, 
    content: str, 
    image_url: Optional[str] = None,
    local_image_path: Optional[str] = None
):
    """
    Lưu tin nhắn User kèm Cloudinary URL và đường dẫn file Local.
    """
    conversation = get_conversation(conversation_id)
    if conversation is None:
        raise ValueError(f"Conversation {conversation_id} not found")

    message = {
        "role": "user",
        "content": content,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if image_url:
        message["image_url"] = image_url
    
    if local_image_path:
        message["local_image_path"] = local_image_path

    conversation["messages"].append(message)
    save_conversation(conversation)

def add_assistant_message(
    conversation_id: str,
    council_result: Dict[str, Any],
    task_type: str = "outpainting"
):
    """
    Lưu kết quả trả về từ Assistant (AI).
    """
    conversation = get_conversation(conversation_id)
    if conversation is None:
        raise ValueError(f"Conversation {conversation_id} not found")
    
    # Lấy nội dung text hiển thị (fallback nếu UI chỉ hiển thị text đơn giản)
    display_content = "Task completed."
    if task_type == "chat":
        display_content = council_result.get("final_result", {}).get("selected_response", "")
    elif task_type == "outpainting":
        final = council_result.get("final_result", {})
        if final:
             display_content = "Outpainting Prompt Generated Successfully."

    conversation["messages"].append({
        "role": "assistant",
        "content": display_content,
        "task_type": task_type,
        "timestamp": datetime.utcnow().isoformat(),
        "council_response": council_result 
    })

    save_conversation(conversation)

def update_conversation_title(conversation_id: str, title: str):
    conversation = get_conversation(conversation_id)
    if conversation is None: return
    conversation["title"] = title
    save_conversation(conversation)