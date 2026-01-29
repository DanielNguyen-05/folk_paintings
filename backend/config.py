import os
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
load_dotenv()

OPENAI_API_KEY_S1 = os.getenv("OPENAI_API_KEY")
OPENAI_API_KEY_S2 = os.getenv("OPENAI_API_KEY") 
GEMINI_API_KEY_S1 = os.getenv("GEMINI_API_KEY_S1") 
GEMINI_API_KEY_S2 = os.getenv("GEMINI_API_KEY_S2")
CHAIRMAN_API_KEY = os.getenv("CHAIRMAN_API_KEY")

MODEL_REGISTRY = {
    # --- CHAIRMAN ---
    "gemini_chairman": {
        "provider": "google",
        "model": "gemini-flash-latest",
        "api_key": CHAIRMAN_API_KEY,
        "base_url": "https://generativelanguage.googleapis.com/v1beta/models" 
    },

    # --- STAGE 1 ---
    "gpt_stage1": {
        "provider": "openai",
        "model": "gpt-4o-mini",
        "api_key": OPENAI_API_KEY_S1,
        "base_url": "https://api.openai.com/v1/chat/completions"
    },
    "gemini_stage1": {
        "provider": "google",
        "model": "gemini-flash-latest",
        "api_key": GEMINI_API_KEY_S1,
        "base_url": "https://generativelanguage.googleapis.com/v1beta/models" 
    },
    
    # --- STAGE 2 ---
    "gpt_stage2": {
        "provider": "openai",
        "model": "gpt-4o-mini", # Hoặc model mạnh hơn nếu cần
        "api_key": OPENAI_API_KEY_S2,
        "base_url": "https://api.openai.com/v1/chat/completions"
    },
    "gemini_stage2": {
        "provider": "google",
        "model": "gemini-flash-latest", 
        "api_key": GEMINI_API_KEY_S2,
        "base_url": "https://generativelanguage.googleapis.com/v1beta/models"
    },
}

COUNCIL_MEMBERS_STAGE1 = ["gpt_stage1", "gemini_stage1"]
COUNCIL_MEMBERS_STAGE2 = ["gpt_stage2", "gemini_stage2"]

CHAIRMAN_ID = "gemini_chairman" 

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