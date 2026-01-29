"""FastAPI backend for LLM Council (Outpainting)."""

from fastapi import FastAPI, HTTPException, Form, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid
import os
import shutil
import cloudinary
import cloudinary.uploader

from . import storage
from .OutpaintingCouncil import OutpaintingCouncil

# --- Cấu hình thư mục lưu ảnh Local ---
LOCAL_IMG_DIR = "local_storage/images"
os.makedirs(LOCAL_IMG_DIR, exist_ok=True)

app = FastAPI(title="Outpainting Council API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

council = OutpaintingCouncil()

# --- Pydantic Models ---
class CreateConversationRequest(BaseModel):
    title: Optional[str] = "New Outpainting Task"

class ConversationMetadata(BaseModel):
    id: str
    created_at: str
    title: str
    message_count: int

class Conversation(BaseModel):
    id: str
    created_at: str
    title: str
    messages: List[Dict[str, Any]]

# --- Endpoints ---

@app.get("/")
async def root():
    return {"status": "ok", "service": "Outpainting Council API"}

@app.get("/api/conversations", response_model=List[ConversationMetadata])
async def list_conversations():
    return storage.list_conversations()

@app.post("/api/conversations", response_model=Conversation)
async def create_conversation(request: CreateConversationRequest):
    conversation_id = str(uuid.uuid4())
    conversation = storage.create_conversation(conversation_id)
    if request.title:
        storage.update_conversation_title(conversation_id, request.title)
    return conversation

@app.get("/api/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: str):
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation

@app.post("/api/conversations/{conversation_id}/message")
async def send_message_and_process(
    conversation_id: str,
    content: str = Form(...), # User Prompt
    image: UploadFile | None = File(None)
):
    """
    Main Endpoint xử lý:
    1. Kiểm tra keyword ("scale", "expand", "outpainting"...).
    2. Nếu có keyword + ảnh -> Lưu Local -> Upload Cloudinary -> Gọi Council.
    3. Nếu không -> Trả về thông báo bình thường (hoặc chat logic khác).
    """
    
    # 1. Validate Conversation
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # 2. Kiểm tra Keywords (Điều kiện kích hoạt Task)
    trigger_keywords = ["scale", "expand", "extend", "outpainting", "mở rộng"]
    is_outpainting_task = any(keyword in content.lower() for keyword in trigger_keywords)

    image_url = None
    local_image_path = None
    image_data = None
    image_mime_type = "image/jpeg"

    # 3. Xử lý ảnh (Chỉ xử lý nếu User có gửi ảnh)
    if image:
        # a. Đọc bytes
        image_data = await image.read()
        
        # Xác định mime type
        filename = image.filename.lower() if image.filename else "image.jpg"
        if filename.endswith('.png'): image_mime_type = "image/png"
        elif filename.endswith('.webp'): image_mime_type = "image/webp"

        # b. LƯU LOCAL
        # Tạo tên file unique để tránh trùng đè
        local_filename = f"{uuid.uuid4()}_{filename}"
        local_image_path = os.path.join(LOCAL_IMG_DIR, local_filename)
        
        with open(local_image_path, "wb") as f:
            f.write(image_data)
        print(f"💾 Đã lưu ảnh local tại: {local_image_path}")

        # c. UPLOAD CLOUDINARY (Để lấy URL public hiển thị trên Web Frontend)
        try:
            # Upload từ bytes data
            upload_result = cloudinary.uploader.upload(
                image_data, 
                folder="outpainting_tasks"
            )
            image_url = upload_result["secure_url"]
        except Exception as e:
            print(f"⚠️ Cloudinary upload failed: {e}")
            # Nếu lỗi upload, ta vẫn chạy tiếp được vì đã có image_data và local path

    # 4. Lưu User Message vào DB
    storage.add_user_message(conversation_id, content, image_url, local_image_path)
    
    # Cập nhật title hội thoại
    if len(conversation["messages"]) == 0:
        short_title = (content[:30] + '...') if len(content) > 30 else content
        storage.update_conversation_title(conversation_id, short_title)

    # 5. QUYẾT ĐỊNH LOGIC XỬ LÝ
    if is_outpainting_task and image_data:
        try:
            print(f"🚀 Detected Outpainting Task for {conversation_id}...")
            
            # Gọi Council (Truyền image_data trực tiếp để AI xử lý nhanh nhất)
            result = await council.run_task(
                user_query=content,
                image_url=image_url,       # Để AI reference nếu cần
                image_data=image_data,     # Dữ liệu ảnh raw (quan trọng cho Gemini REST)
                image_mime_type=image_mime_type
            )
            
            # Lưu kết quả AI
            storage.add_assistant_message(conversation_id, result, task_type="outpainting")
            return result

        except Exception as e:
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Council processing failed: {str(e)}")
            
    else:
        # TRƯỜNG HỢP: Không phải task outpainting hoặc không có ảnh
        # Bạn có thể nối vào một Chatbot bình thường ở đây.
        # Hiện tại tôi sẽ trả về một thông báo đơn giản.
        
        fallback_response = {
            "final_result": {
                "selected_response": "Tôi là AI chuyên về Outpainting (Mở rộng tranh). Vui lòng gửi kèm một bức ảnh và dùng các từ khóa như 'expand', 'scale', 'outpainting' để tôi bắt đầu làm việc.",
                "selected_model": "system",
                "evaluation": "No task triggered"
            }
        }
        
        storage.add_assistant_message(conversation_id, fallback_response, task_type="chat")
        return fallback_response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)