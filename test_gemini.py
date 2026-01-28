from google import genai
import os
from google.genai.types import Part
from dotenv import load_dotenv
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY_6")
client = genai.Client(api_key=GEMINI_API_KEY)

# Đường dẫn ảnh local
IMAGE_PATH ="img/dongho_0000_em-be-om-ga.jpeg"
IMAGE_URL = "https://res.cloudinary.com/dvxmaiofh/image/upload/v1769313938/llm_council/iyh1xp24rmjsk8bxsvaz.jpg"

with open(IMAGE_PATH, "rb") as f:
  image = Part.from_bytes(data=f.read(), mime_type='image/jpeg')

prompt = """Return ONLY valid JSON (no markdown, no extra text).
  I want to scale/expand this image using outpainting by adding detailed scenery or elements around the image, NOT decorating its borders. Please fill in the following JSON template with the most detailed information.

  {
    "task_type": "outpainting",
    "input_image_meaning": "",
    "expansion_settings": {
      "direction": "", 
      "pixel_amount":,
      "mask_blur":
    },
    "context_awareness": {
      "original_style": "",
      "seamless_blending_keywords": []
    },
    "scenarios": [
      {
        "scenario_id": "",
        "description": "",
        "prompt": ""
      },
      {
        "scenario_id": "",
        "description": "",
        "prompt": ""
      },
      {
        "scenario_id": "",
        "description": "",
        "prompt": ""
      },
      {
        "scenario_id": "",
        "description": "",
        "prompt": ""
      }
    ]
  }
"""

response = client.models.generate_content(
  model="gemini-flash-latest", 
  contents = [prompt, image]
)


print(response.text)