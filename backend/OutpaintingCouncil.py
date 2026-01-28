from typing import List, Dict, Any, Tuple
import re
from .llm_client import query_models_parallel, query_model
from .config import COUNCIL_MEMBERS_STAGE1, CHAIRMAN_ID
from typing import Optional

class OutpaintingCouncil:
    """
    Council system for folk painting outpainting task.
    Has 3 stages:
    - Stage 1: Initial outpainting generation from multiple models
    - Stage 2: Sequential completion/perfection of each outpainting response
    - Stage 3: Evaluation and selection of the best outpainting
    """

    def __init__(self):
        self.stage1_models = COUNCIL_MEMBERS_STAGE1
        self.chairman_model = CHAIRMAN_ID
        self.task_type = "outpainting"

    async def run_task(
        self,
        user_query: str,
        image_url: Optional[str] = None,
        image_data: Optional[bytes] = None,
        image_mime_type: str = "image/jpeg"
    ) -> Dict[str, Any]:
        """
        Run the complete 3-stage outpainting process.
        """
        # Stage 1: Collect initial outpainting responses
        stage1_results = await self._stage1_collect_responses(
            user_query, image_url, image_data, image_mime_type
        )

        if not stage1_results:
            return {
                "error": "All models failed to respond in stage 1",
                "stage1_results": [],
                "stage2_results": [],
                "final_result": None
            }

        # Stage 2: Sequentially complete each response
        stage2_results = await self._stage2_complete_responses(
            user_query, stage1_results, image_url, image_data, image_mime_type
        )

        # Stage 3: Evaluate and select the best
        final_result = await self._stage3_evaluate_and_select(
            user_query, stage2_results, image_url, image_data, image_mime_type
        )

        return {
            "stage1_results": stage1_results,
            "stage2_results": stage2_results,
            "final_result": final_result
        }

    async def _stage1_collect_responses(
        self, user_query: str, image_url: Optional[str],
        image_data: Optional[bytes], image_mime_type: str
    ) -> List[Dict[str, Any]]:
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
        messages = [{"role": "user", "content": prompt}]

        responses = await query_models_parallel(
            self.stage1_models, messages, 
            image_data=image_data, 
            image_mime_type=image_mime_type,
            image_url=image_url
        )

        stage1_results = []
        for model_id, response in responses.items():
            if response is not None:
                stage1_results.append({
                    "model": model_id,
                    "response": response.get('content', ''),
                    "task_type": self.task_type
                })
        return stage1_results

    async def _stage2_complete_responses(
        self, user_query: str,
        stage1_results: List[Dict[str, Any]], image_url: Optional[str],
        image_data: Optional[bytes], image_mime_type: str
    ) -> List[Dict[str, Any]]:
        """
        Stage 2: Sequentially complete and perfect each outpainting response from stage 1.
        """
        stage2_results = []

        for result in stage1_results:
            original_model = result['model']
            original_response = result['response']

            # Map stage 1 model to corresponding stage 2 model
            stage2_model = self._get_stage2_model(original_model)

            completion_prompt = f"""You are an expert folk painting outpainter. Look at this image and review/complete the following outpainting JSON to make it perfect.

Initial Response from {original_model}: 
{original_response}

Your task: Complete and perfect this outpainting JSON by:
1. Enhancing the expansion settings with appropriate direction, pixel_amount, and mask_blur values
2. Adding detailed original_style description and seamless_blending_keywords
3. Creating 4 distinct, creative scenarios with unique scenario_ids, descriptions, and detailed prompts
4. Ensuring all scenarios are comprehensive and ready for implementation
5. Making sure the JSON is valid and complete

Provide the same format outpainting JSON:"""

            messages = [{"role": "user", "content": completion_prompt}]
            response = await query_model(
                        stage2_model, messages, 
                        image_url=image_url, 
                        image_data=image_data, 
                        image_mime_type=image_mime_type
                    )
            if response is not None:
                stage2_results.append({
                    "original_model": original_model,
                    "stage2_model": stage2_model,
                    "original_response": original_response,
                    "perfected_response": response.get('content', ''),
                    "task_type": self.task_type
                })
            else:
                # If stage 2 fails, keep the original
                stage2_results.append({
                    "original_model": original_model,
                    "stage2_model": stage2_model,
                    "original_response": original_response,
                    "perfected_response": original_response, 
                    "task_type": self.task_type,
                    "error": "Stage 2 completion failed"
                })

        return stage2_results

    async def _stage3_evaluate_and_select(
        self, user_query: str,
        stage2_results: List[Dict[str, Any]], image_url: Optional[str],
        image_data: Optional[bytes], image_mime_type: str
    ) -> Dict[str, Any]:
        """
        Stage 3: Evaluate all perfected outpainting responses and select the best one.
        """
        if not stage2_results:
            return {"error": "No responses to evaluate"}

        # Create evaluation prompt
        responses_text = "\n\n".join([
            f"Response {chr(65 + i)} (from {result['original_model']}):\n{result['perfected_response']}"
            for i, result in enumerate(stage2_results)
        ])

        evaluation_prompt = f"""You are an expert evaluator of folk painting outpainting JSON configurations. Look at this image and evaluate the following outpainting JSON responses and select the best one.

Responses to evaluate:
{responses_text}

Your task:
1. Evaluate each response based on:
   - Completeness and validity of JSON structure
   - Quality and detail of expansion_settings
   - Appropriateness of context_awareness settings
   - Creativity and variety of scenarios
   - Overall coherence and implementation readiness

2. At the end, clearly state your selection in this exact format:
BEST RESPONSE: Response X (where X is A, B, C, etc.)

Provide your evaluation and final selection:"""

        messages = [{"role": "user", "content": evaluation_prompt}]

        # Use chairman model for evaluation (text-only)
        response = await query_model(
            self.chairman_model, messages, 
            image_url=image_url, 
            image_data=image_data, 
            image_mime_type=image_mime_type
        )

        if response is None:
            # Fallback: select the first response
            return {
                "selected_response": stage2_results[0]['perfected_response'],
                "selected_model": stage2_results[0]['original_model'],
                "evaluation": "Evaluation failed, selected first response as fallback",
                "task_type": self.task_type
            }

        evaluation_text = response.get('content', '')

        # Parse the best response selection
        best_response_label = self._parse_best_response_selection(evaluation_text)

        if best_response_label:
            # Convert label (A, B, C...) to index (0, 1, 2...)
            index = ord(best_response_label.upper()) - ord('A')
            if 0 <= index < len(stage2_results):
                selected = stage2_results[index]
                return {
                    "selected_response": selected['perfected_response'],
                    "selected_model": selected['original_model'],
                    "evaluation": evaluation_text,
                    "task_type": self.task_type
                }

        # Fallback if parsing fails
        return {
            "selected_response": stage2_results[0]['perfected_response'],
            "selected_model": stage2_results[0]['original_model'],
            "evaluation": evaluation_text,
            "task_type": self.task_type,
            "error": "Could not parse best response selection"
        }

    def _get_stage2_model(self, stage1_model: str) -> str:
        """
        Map stage 1 model to corresponding stage 2 model.
        """
        mapping = {
            "gpt_stage1": "gpt_stage2",
            "gemini_stage1": "gemini_stage2"
        }
        return mapping.get(stage1_model, stage1_model)  # fallback to same model

    def _parse_best_response_selection(self, evaluation_text: str) -> str:
        """
        Parse the BEST RESPONSE selection from evaluation text.
        """
        # Look for "BEST RESPONSE: Response X" pattern
        match = re.search(r'BEST RESPONSE:\s*Response\s*([A-Z])', evaluation_text, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        return None