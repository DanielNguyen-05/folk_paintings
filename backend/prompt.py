
def outpainting_prompt_stage1():
    prompt = f"""Return ONLY valid JSON (no markdown, no extra text).
I want to scale/expand this image using outpainting by adding detailed scenery or elements around the image, NOT decorating its borders. Please fill in the following JSON template with the most detailed information.

{{
  "task_type": "outpainting",
  "expansion_settings": {{
    "direction": "",
    "pixel_amount": 0,
    "mask_blur": 0
  }},
  "context_awareness": {{
    "original_style": "",
    "seamless_blending_keywords": []
  }},
  "scenarios": [
    {{
      "scenario_id": "",
      "description": "",
      "prompt": ""
    }},
    {{
      "scenario_id": "",
      "description": "",
      "prompt": ""
    }},
    {{
      "scenario_id": "",
      "description": "",
      "prompt": ""
    }},
    {{
      "scenario_id": "",
      "description": "",
      "prompt": ""
    }}
  ]
}}
"""
    return prompt

def outpainting_prompt_stage2(original_model, original_response):
    prompt = f"""You are an expert folk painting outpainter. Look at this image and review/complete the following outpainting JSON to make it perfect.

Initial Response from {original_model}: 
{original_response}

Your task: Complete and perfect this outpainting JSON by:
1. Enhancing the expansion settings with appropriate direction, pixel_amount, and mask_blur values
2. Adding detailed original_style description and seamless_blending_keywords
3. Describe creative and detailed surrounding scenarios without affecting the original image.

Provide the same format outpainting JSON:
"""
    return prompt

def outpainting_prompt_stage3(responses_text):
    prompt = f"""You are an expert evaluator of folk painting outpainting JSON configurations. 
I have several candidates for the outpainting configuration. Some are **Initial Versions (Stage 1)** and some are **Refined Versions (Stage 2)**.

Your goal is to compare them and select the single best JSON configuration that yields the most artistic, seamless, and culturally appropriate outpainting for a Vietnamese traditional folk painting.

Responses to evaluate:
{responses_text}

Your task:
1. Evaluate each response based on:
   - **JSON Validity:** Must be strictly valid JSON.
   - **Expansion Settings:** Logic of direction and pixel amount.
   - **Context Awareness:** How well it captures the "folk" style (keywords, blending).
   - **Creativity:** The quality of the scenarios.
   - **Comparison:** specific check if the Refined Version actually improved upon the Initial Draft or if it over-complicated things.

2. At the end, clearly state your selection in this exact format:
BEST RESPONSE: Response X (where X is A, B, C, etc.)

Provide your evaluation and final selection:
"""
    return prompt


def storyGeneration_prompt():
    prompt =""
    return prompt
