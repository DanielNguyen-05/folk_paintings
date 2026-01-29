import os
import base64
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

# Retrieve OpenAI API key from the environment variables
OPEN_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPEN_API_KEY)

# Define the path for the local image
IMAGE_PATH = "img/dongho_0001_chuot-vinh-quy.jpg"

def encode_image(img_path):
  with open(img_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')


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

def call_gpt(client, prompt: str, images: list, model: str):
  contents = [{"type": "input_text", "text": prompt}]

  for img_path in images:
    contents.append({
      "type": "input_image",
      "image_url": f"data:image/jpeg;base64,{encode_image(img_path)}"
    })

  response = client.responses.create(
    model=model,
    input=[{
        "role": "user",
        "content": contents
      }]
  )

  return response.output_text

images = [IMAGE_PATH]

response_output = call_gpt(client, prompt, images, model="gpt-4o-mini")

print(response_output)