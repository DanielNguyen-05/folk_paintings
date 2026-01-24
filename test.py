import os
import json
from openai import OpenAI
import re

# --- 1. CONFIGURATION ---
os.environ["OPENAI_API_KEY"] = ""
# os.environ["OPENAI_API_KEY"] = 
client_openai = OpenAI()

# --- 2. CLASS TO HANDLE GENERATION AND SELECTION ---

class ImageScaleHandler:
    def __init__(self):
        self.client_openai = client_openai
    
    def generate_scale_json(self, prompt: str) -> dict:
        """Gửi yêu cầu đến LLM để sinh ra JSON cho tác vụ mở rộng hình ảnh"""
        # Gửi câu prompt đến OpenAI GPT-4o hoặc mô hình LLM khác
        response = self.client_openai.chat.completions.create(
            model="gpt-4o-mini",  # Hoặc mô hình GPT bạn muốn sử dụng
            messages=[
                {"role": "system", "content": "You are an expert in image processing and JSON formatting."},
                {"role": "user", "content": prompt}
            ]
        )
        
        # Lấy nội dung trả về
        result = response.choices[0].message.content
        print("LLM Response:", result)  # In ra để kiểm tra nội dung trả về

        # Sử dụng regex để tách phần JSON trong văn bản
        json_text = self.extract_json_from_text(result)
        
        if json_text:
            try:
                json_result = json.loads(json_text)  # Chuyển đổi kết quả thành JSON
                return json_result
            except json.JSONDecodeError:
                print("Error parsing JSON from LLM output")
                return None
        else:
            print("No valid JSON found in the response")
            return None
    
    def extract_json_from_text(self, text: str) -> str:
        """Sử dụng regex để tách JSON từ văn bản trả về"""
        json_pattern = r"\{.*\}"  # Biểu thức chính quy để nhận diện JSON
        match = re.search(json_pattern, text)
        
        if match:
            return match.group(0)  # Trả về phần JSON tìm được
        else:
            return None

# --- 3. MAIN CONTROLLER (Sử dụng system để chạy quy trình) ---

class LLMCouncilSystem:
    def __init__(self):
        self.scale_handler = ImageScaleHandler()

    def process_request(self, image_path: str, prompt: str):
        print(f"🚀 Starting process for image scaling. Input image path: {image_path}")

        # 1. Gửi yêu cầu đến LLM để sinh JSON từ prompt
        scale_json = self.scale_handler.generate_scale_json(prompt)
        
        if scale_json:
            print("\n✅ Best JSON selected for image scaling:")
            print(json.dumps(scale_json, indent=4))  # In ra JSON đã chọn

        # Trả lại JSON tốt nhất để sử dụng cho sinh ảnh
        return scale_json


# --- 4. EXECUTION EXAMPLE ---

if __name__ == "__main__":
    system = LLMCouncilSystem()

    # Ví dụ: đường dẫn hình ảnh và câu prompt yêu cầu
    input_img = "dongho_0001_chuot-vinh-quy.jpg"
    user_prompt = """
    I want to scale this image. Please help me create a JSON file that provides a complete and detailed description in the following format:
    {
      "task_type": "outpainting",
      "input_image": "<image_path>",
      "expansion_settings": {
        "direction": "horizontal", 
        "pixel_amount": 512,
        "mask_blur": 12
      },
      "context_awareness": {
        "original_style": "Dong Ho woodblock print",
        "seamless_blending_keywords": [
          "vintage texture", 
          "natural grain", 
          "flat perspective"
        ]
      },
      "scenarios": [
        {
          "scenario_id": "remove_border",
          "description": "Remove the outer border frame from the image",
          "prompt": "Ensure the border is not included in the expanded area."
        },
        {
          "scenario_id": "expand_background",
          "description": "Expand the background using the original style.",
          "prompt": "Continue the traditional design in the expanded area."
        }
      ]
    }
    """

    # Gọi hàm process_request để thực hiện quy trình
    best_json = system.process_request(input_img, user_prompt)
    
    # Bạn có thể sử dụng best_json để sinh hình ảnh hoặc thực hiện các thao tác tiếp theo
