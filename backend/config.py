import os
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Không cần key cho local, hoặc tùy cấu hình
LOCAL_API_URL = "http://localhost:11434/v1" # Ví dụ chạy Ollama hoặc vLLM

# --- ĐỊNH NGHĨA HỘI ĐỒNG (COUNCIL) ---
# Mỗi thành viên được định nghĩa rõ: Provider (nhà cung cấp), Model Name, và Endpoint
MODEL_REGISTRY = {
    "scholar_gpt": {
        "provider": "openai",
        "model": "gpt-3.5",
        "api_key": OPENAI_API_KEY,
        "base_url": "https://api.openai.com/v1/chat/completions"
    },
    "artist_gemini": {
        "provider": "google",
        "model": "gemini-flash-latest",
        "api_key": GEMINI_API_KEY,
        # Google dùng REST API khác biệt, xử lý trong llm_client.py
        "base_url": "https://generativelanguage.googleapis.com/v1beta/models" 
    },
    # "local_historian": {
    #     "provider": "openai_compatible",
    #     "model": "qwen2.5:3b",
    #     "api_key": "ollama",
    #     "base_url": f"{LOCAL_API_URL}/chat/completions"
    # }
}

# Danh sách các Key trong MODEL_REGISTRY sẽ tham gia hội đồng
COUNCIL_MEMBERS = [
    "scholar_gpt",
    "artist_gemini",
    "local_historian"
]

# Ai là chủ tịch? (Dùng key trong registry)
CHAIRMAN_ID = "artist_gemini" 

# Thư mục dữ liệu
DATA_DIR = "data/conversations"

# Cấu hình Cloudinary để lưu trữ ảnh
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET,
)