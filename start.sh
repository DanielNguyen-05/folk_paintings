#!/bin/bash

# --- CẤU HÌNH ---
# Hãy đảm bảo bạn đã tạo venv và cài thư viện (pip install -r requirements.txt ...)
# Nếu chưa active venv, bỏ comment dòng dưới (Mac/Linux):
source .venv/bin/activate 

echo "🚀 Starting LLM Council..."

# 1. Kiểm tra Ollama đã chạy chưa
if ! pgrep -x "ollama" > /dev/null && ! pgrep -x "Ollama" > /dev/null; then
    echo "⚠️  Ollama chưa chạy! Hãy mở app Ollama lên trước."
    # Trên Mac có thể thử mở tự động: open -a Ollama
fi

echo ""

# 2. Start Backend
# Dùng 'python' thay vì 'uv run python' để tương thích tốt hơn
echo "🔥 Starting backend on http://localhost:8001..."
python -m backend.main &
BACKEND_PID=$!

# Đợi chút cho backend khởi động
sleep 2

# 3. Start Frontend
echo "🎨 Starting frontend on http://localhost:5173..."
cd frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "=================================================="
echo "✓ LLM Council is running!"
echo "  Backend:  http://localhost:8001"
echo "  Frontend: http://localhost:5173"
echo "=================================================="
echo "Press Ctrl+C to stop."

# Trap để tắt cả 2 khi bấm Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM
wait