import asyncio
import os
import json
import sys
import time
from dotenv import load_dotenv

current_dir = os.getcwd()
sys.path.append(current_dir)

load_dotenv()

try:
    from backend.OutpaintingCouncil import OutpaintingCouncil
except ImportError as e:
    print("❌ Lỗi Import: Không tìm thấy module 'backend'.")
    print(f"Chi tiết: {e}")
    sys.exit(1)

# --- Helper: In JSON đẹp (Pretty Print) ---
def print_pretty_json(label, content):
    """
    Cố gắng parse string thành JSON để in ra có thụt đầu dòng.
    Nếu không phải JSON, in nguyên văn string.
    """
    print(f"\n🔹 {label}:")
    print("-" * 40)
    
    if not content:
        print("(Empty content)")
        return

    try:
        # Nếu nội dung là string, thử parse nó
        if isinstance(content, str):
            # Làm sạch chuỗi json (đôi khi LLM trả về markdown ```json ... ```)
            clean_content = content.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(clean_content)
            print(json.dumps(parsed, indent=2, ensure_ascii=False))
        else:
            # Nếu đã là dict/list
            print(json.dumps(content, indent=2, ensure_ascii=False))
    except Exception:
        # Nếu lỗi parse (do LLM trả về text thường), in nguyên văn
        print(content)
    print("-" * 40)

async def run_test_verbose():
    print("\n🚀 BẮT ĐẦU TEST TOÀN DIỆN (FULL VERBOSE MODE)...")
    
    # CẤU HÌNH INPUT
    IMAGE_FILENAME = "img/dongho_0001_chuot-vinh-quy.jpg"  
    USER_QUERY = "Expand this image to the right, adding a beautiful lotus pond in folk art style."
    
    image_path = os.path.join(current_dir, IMAGE_FILENAME)

    # 1. Đọc ảnh
    if not os.path.exists(image_path):
        print(f"❌ Lỗi: Không tìm thấy ảnh tại {image_path}")
        return

    print(f"📸 Đang đọc ảnh: {IMAGE_FILENAME}")
    with open(image_path, "rb") as f:
        image_data = f.read()

    image_mime_type = "image/jpeg" 
    if image_path.lower().endswith(".png"): image_mime_type = "image/png"

    # 2. Khởi tạo
    print("🤖 Đang khởi tạo OutpaintingCouncil...")
    council = OutpaintingCouncil()

    # 3. Chạy Task
    print(f"\n⏳ Đang xử lý Query: '{USER_QUERY}'")
    print("   (Quá trình này sẽ in ra RẤT NHIỀU text, vui lòng cuộn để xem)...")
    
    start_time = time.time()
    
    try:
        result = await council.run_task(
            user_query=USER_QUERY,
            image_data=image_data,
            image_mime_type=image_mime_type
        )
        
        duration = time.time() - start_time

        # ==========================================
        # IN TOÀN BỘ KẾT QUẢ (RAW & FULL)
        # ==========================================

        print("\n" + "█"*50)
        print(f"█ KẾT QUẢ CHI TIẾT (Time: {duration:.2f}s)")
        print("█"*50)

        # 1. IN STAGE 1
        s1_results = result.get("stage1_results", [])
        print(f"\n\n📂 --- STAGE 1 OUTPUT ({len(s1_results)} Models) ---")
        for i, item in enumerate(s1_results):
            print(f"\n📌 Model S1 [{i+1}]: {item.get('model')}")
            print_pretty_json("Draft Response", item.get('response'))

        # 2. IN STAGE 2
        s2_results = result.get("stage2_results", [])
        print(f"\n\n📂 --- STAGE 2 OUTPUT (Cross-Refinement: {len(s2_results)} Versions) ---")
        for i, item in enumerate(s2_results):
            orig = item.get('original_model')
            refiner = item.get('stage2_model')
            print(f"\n📌 Version [{i+1}]: Tác giả gốc '{orig}' ➔ Chỉnh sửa bởi '{refiner}'")
            
            if "error" in item:
                print(f"❌ ERROR: {item.get('error')}")
            else:
                # In ra bản đã sửa
                print_pretty_json("Refined Response", item.get('perfected_response'))

        # 3. IN STAGE 3 (FINAL)
        final = result.get("final_result", {})
        print("\n\n🏆 --- STAGE 3: CHAIRMAN DECISION ---")
        
        if not final:
            print("❌ Không có kết quả Final.")
        else:
            print(f"✅ MODEL ĐƯỢC CHỌN: {final.get('selected_model')}")
            print(f"🏷️  NGUỒN GỐC:      {final.get('selected_stage')} (Quan trọng: xem nó chọn bản Raw hay Refined)")
            print(f"\n📝 LỜI BÌNH CỦA CHAIRMAN:\n{final.get('evaluation')}")
            
            print_pretty_json("🌟 FINAL JSON TO USE", final.get('selected_response'))

        # 4. Lưu file log để backup
        output_file = "full_debug_log.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Đã lưu toàn bộ cấu trúc dữ liệu vào: {output_file}")

    except Exception as e:
        print(f"\n❌ LỖI NGHIÊM TRỌNG: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_test_verbose())