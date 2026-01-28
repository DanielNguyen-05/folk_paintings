import os
import base64
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

OPEN_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPEN_API_KEY)

IMAGE_URL = "https://res.cloudinary.com/dvxmaiofh/image/upload/v1769313938/llm_council/iyh1xp24rmjsk8bxsvaz.jpg"
IMAGE_PATH ="img/dongho_0001_chuot-vinh-quy.jpg"

with open(IMAGE_PATH, "rb") as image_file:
  image_b64 = base64.b64encode(image_file.read()).decode('utf-8')

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

response = client.responses.create(
  model="gpt-4o-mini",
  input=[
    {
      "role": "user",
      "content": [
        { "type": "input_text", "text": prompt },
        {
            "type": "input_image",
            "image_url": IMAGE_URL
        }
      ]
    }
  ]
)

print(response)
