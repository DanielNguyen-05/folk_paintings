import asyncio
import os
import json
import sys
from dotenv import load_dotenv

current_dir = os.getcwd()
sys.path.append(current_dir)

load_dotenv()

try:
    from backend.OutpaintingCouncil import OutpaintingCouncil
except ImportError as e:
    print("❌ Lỗi Import: Không tìm thấy module 'backend'.")
    print(f"Chi tiết: {e}")
    print("👉 Hãy chắc chắn bạn đang chạy lệnh python tại thư mục gốc chứa folder 'backend'.")
    sys.exit(1)

async def run_test():
    print("🚀 Bắt đầu Test Outpainting Council...")
    
    IMAGE_FILENAME = "img/dongho_0001_chuot-vinh-quy.jpg"  
    USER_QUERY = "Expand this image to the right, adding a beautiful lotus pond."
    # ==========================================

    image_path = os.path.join(current_dir, IMAGE_FILENAME)

    # Kiểm tra file ảnh
    if not os.path.exists(image_path):
        print(f"❌ Lỗi: Không tìm thấy file ảnh tại '{image_path}'")
        print("👉 Vui lòng copy một file ảnh .jpg hoặc .png vào cùng thư mục với file test này.")
        return

    # 2. Đọc file ảnh dưới dạng bytes (Giả lập việc nhận file từ API)
    print(f"📸 Đang đọc ảnh từ: {IMAGE_FILENAME}")
    with open(image_path, "rb") as f:
        image_data = f.read()

    # Xác định mime type đơn giản
    image_mime_type = "image/jpeg"
    if image_path.lower().endswith(".png"):
        image_mime_type = "image/png"
    elif image_path.lower().endswith(".webp"):
        image_mime_type = "image/webp"

    # 3. Khởi tạo Council
    print("🤖 Đang khởi tạo OutpaintingCouncil...")
    try:
        council = OutpaintingCouncil()
    except Exception as e:
        print(f"❌ Lỗi khởi tạo Council: {e}")
        print("👉 Kiểm tra lại file .env xem đã có API KEY chưa.")
        return

    # 4. Chạy Task
    print("\n⏳ Đang gửi request tới AI (Stage 1 -> Stage 2 -> Stage 3)...")
    print("   (Vui lòng đợi khoảng 30-60 giây...)")
    
    try:
        # Gọi hàm run_task giống hệt như cách main.py gọi
        result = await council.run_task(
            user_query=USER_QUERY,
            image_data=image_data,
            image_mime_type=image_mime_type
        )

        # 5. Hiển thị kết quả
        print("\n" + "="*50)
        print("✅ TÁC VỤ HOÀN TẤT!")
        print("="*50)
        
        if "error" in result:
            print(f"⚠️  SERVER TRẢ VỀ LỖI: {result.get('error')}")
        else:
            final = result.get("final_result", {})
            print(f"\n🏆 MODEL ĐƯỢC CHỌN: {final.get('selected_model')}")
            print(f"📝 LÝ DO (Evaluation): {final.get('evaluation')}")
            
            print("\n📄 KẾT QUẢ JSON FINAL:")
            print("-" * 30)
            print(final.get('selected_response'))
            print("-" * 30)

            # Lưu kết quả ra file JSON để debug
            output_file = "result_debug.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\n💾 Đã lưu log chi tiết vào file: {output_file}")

    except Exception as e:
        print(f"\n❌ Exception Runtime: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Yêu cầu Python 3.7+
    asyncio.run(run_test())