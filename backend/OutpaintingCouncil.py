from typing import List, Dict, Any, Tuple
import re
import asyncio  
from .llm_client import query_models_parallel, query_model
from .config import COUNCIL_MEMBERS_STAGE1, COUNCIL_MEMBERS_STAGE2, CHAIRMAN_ID
from typing import Optional
from .prompt import (outpainting_prompt_stage1, 
                     outpainting_prompt_stage2,
                     outpainting_prompt_stage3)

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
        self.stage2_models = COUNCIL_MEMBERS_STAGE2
        self.chairman_model = CHAIRMAN_ID
        self.task_type = "outpainting"

    async def run_task(
        self, user_query: str,
        image_url: Optional[str] = None, image_data: Optional[bytes] = None,
        image_mime_type: str = "image/jpeg") -> Dict[str, Any]:
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
        
        prompt = outpainting_prompt_stage1()

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
        Stage 2 (CROSS-REFINEMENT): 
        EVERY Stage 2 model will refine EVERY Stage 1 response.
        If Stage 1 has M results and Stage 2 has N models, we get M*N refined results.
        """
        stage2_results = []
        tasks = []
        metadata_list = []

        # 1. Tạo danh sách các task (công việc) cần làm
        for s1_result in stage1_results:
            original_model = s1_result['model']
            original_response = s1_result['response']
            
            # Lặp qua TẤT CẢ các model ở Stage 2
            for refiner_model_id in self.stage2_models:
                
                # Tạo prompt
                completion_prompt = outpainting_prompt_stage2(original_model, original_response)
                messages = [{"role": "user", "content": completion_prompt}]
                
                # Đóng gói metadata để đối chiếu sau khi chạy xong
                metadata = {
                    "original_model": original_model,
                    "refiner_model": refiner_model_id,
                    "original_response": original_response
                }
                metadata_list.append(metadata)

                # Tạo coroutine (task) nhưng chưa chạy ngay
                tasks.append(query_model(
                    refiner_model_id, messages, 
                    image_url=image_url, 
                    image_data=image_data, 
                    image_mime_type=image_mime_type
                ))

        # 2. Chạy tất cả các task song song (tăng tốc độ xử lý)
        print(f"STAGE 2: Running {len(tasks)} refinement tasks in parallel...")
        responses = await asyncio.gather(*tasks)

        # 3. Ghép kết quả vào danh sách trả về
        for i, response in enumerate(responses):
            meta = metadata_list[i]
            
            if response is not None:
                stage2_results.append({
                    "original_model": meta["original_model"],     
                    "stage2_model": meta["refiner_model"],        
                    "original_response": meta["original_response"],
                    "perfected_response": response.get('content', ''),
                    "task_type": self.task_type
                })
            else:
                # Nếu lỗi, giữ nguyên bản gốc
                stage2_results.append({
                    "original_model": meta["original_model"],
                    "stage2_model": meta["refiner_model"],
                    "original_response": meta["original_response"],
                    "perfected_response": meta["original_response"], 
                    "task_type": self.task_type,
                    "error": f"Stage 2 refinement failed by {meta['refiner_model']}"
                })

        return stage2_results

    async def _stage3_evaluate_and_select(
        self, user_query: str,
        stage2_results: List[Dict[str, Any]], image_url: Optional[str],
        image_data: Optional[bytes], image_mime_type: str
    ) -> Dict[str, Any]:
        """
        Stage 3: Evaluate candidates. 
        Candidates include:
        1. Unique Original Drafts from Stage 1 (Raw)
        2. All Cross-Refined Versions from Stage 2
        """

        if not stage2_results:
            return {"error": "No responses in stage 2 to evaluate"}
        
        # 1. Chuẩn bị danh sách tất cả các ứng viên (Candidates)
        # Mỗi luồng xử lý sẽ tạo ra 2 ứng viên: Bản gốc (Stage 1) và Bản hoàn thiện (Stage 2)
        candidates = []
        seen_originals = set() # Để tránh đưa trùng lặp bản gốc Stage 1 vào chấm điểm

        for result in stage2_results:
            # 1. Thêm bản gốc (Stage 1) - chỉ thêm 1 lần cho mỗi model gốc
            orig_model = result['original_model']
            if orig_model not in seen_originals:
                candidates.append({
                    "label_info": f"Stage 1 Draft (Author: {orig_model})",
                    "response_text": result['original_response'],
                    "source_model": orig_model,
                    "stage": "Stage 1 (Raw)"
                })
                seen_originals.add(orig_model)
            
            # 2. Thêm bản đã sửa (Stage 2)
            # Label ví dụ: "Stage 2 (GPT -> Gemini)"
            refiner = result['stage2_model']
            candidates.append({
                "label_info": f"Stage 2 Refined ({orig_model} -> {refiner})",
                "response_text": result['perfected_response'],
                "source_model": refiner,
                "stage": f"Stage 2 (Refined by {refiner})"
            })

        # --- Tạo prompt đánh giá ---
        responses_text_parts = []
        for i, cand in enumerate(candidates):
            label = chr(65 + i) # A, B, C...
            responses_text_parts.append(
                f"Response {label} [{cand['label_info']}]:\n{cand['response_text']}"
            )
        
        responses_text = "\n\n" + "="*20 + "\n\n".join(responses_text_parts)

        evaluation_prompt = outpainting_prompt_stage3(responses_text)
        
        # --- Gọi Chairman ---
        messages = [{"role": "user", "content": evaluation_prompt}]
        response = await query_model(
            self.chairman_model, messages, 
            image_url=image_url, 
            image_data=image_data, 
            image_mime_type=image_mime_type
        )

        # --- Xử lý kết quả ---
        if response is None:
            # Fallback
            fallback = stage2_results[0]
            return {
                "selected_response": fallback['perfected_response'],
                "selected_model": fallback['stage2_model'],
                "selected_stage": "Stage 2 (Fallback)",
                "evaluation": "Evaluation failed",
                "task_type": self.task_type
            }

        evaluation_text = response.get('content', '')
        best_response_label = self._parse_best_response_selection(evaluation_text)

        if best_response_label:
            index = ord(best_response_label.upper()) - ord('A')
            if 0 <= index < len(candidates):
                selected = candidates[index]
                return {
                    "selected_response": selected['response_text'],
                    "selected_model": selected['source_model'],
                    "selected_stage": selected['stage'],
                    "evaluation": evaluation_text,
                    "task_type": self.task_type
                }

        # Fallback parsing error
        fallback = stage2_results[0]
        return {
            "selected_response": fallback['perfected_response'],
            "selected_model": fallback['stage2_model'],
            "selected_stage": "Stage 2 (Fallback - Parse Error)",
            "evaluation": evaluation_text,
            "task_type": self.task_type,
            "error": "Could not parse best response selection"
        }

    def _parse_best_response_selection(self, evaluation_text: str) -> str:
        """
        Parse the BEST RESPONSE selection from evaluation text.
        """
        # Look for "BEST RESPONSE: Response X" pattern
        match = re.search(r'BEST RESPONSE:\s*Response\s*([A-Z])', evaluation_text, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        return None