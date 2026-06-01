# Hướng dẫn Khởi chạy Dự án Chatbot MVP (Fullstack)

Dự án này chứa ứng dụng Chatbot MVP hoàn chỉnh tích hợp mô hình **MiMo-v2.5-pro** của Xiaomi, bao gồm:
1. **Backend**: FastAPI (Python) chịu trách nhiệm xác thực, lọc an toàn (guardrails), tính toán token và đo lường telemetry.
2. **Frontend**: Next.js 14 + Tailwind CSS (TypeScript) cung cấp giao diện trò chuyện tối giản, sang trọng và lưu trữ lịch sử cuộc gọi cục bộ.

---

## 📋 Yêu cầu hệ thống

Trước khi bắt đầu, hãy đảm bảo máy tính của bạn đã cài đặt:
- **Python 3.10+** (đã thêm vào biến PATH)
- **Node.js 18+** & **npm** (để quản lý gói frontend)
- **Git** (để đồng bộ và push bài làm)

---

## 🚀 Các bước khởi chạy dự án (Khi mới Clone về)

### Bước 1: Thiết lập Git Hook (Bắt buộc cho khóa học)
Để hệ thống tự động ghi nhận nhật ký (log) các câu lệnh AI nộp về máy chủ chấm điểm khi bạn `git push`:

- **Trên Windows (PowerShell với quyền Admin)**:
  ```powershell
  powershell -ExecutionPolicy Bypass -File scripts\setup_hooks.ps1
  ```
- **Trên Linux / macOS / Git Bash**:
  ```bash
  bash scripts/setup_hooks.sh
  ```

---

### Bước 2: Cài đặt và Chạy Backend (FastAPI)

1. Di chuyển vào thư mục `backend/`:
   ```bash
   cd backend
   ```
2. Tạo tệp tin môi trường `.env` từ file mẫu:
   - Sao chép tệp `.env.example` thành `.env`.
   - Đảm bảo các cấu hình Mimo API chính xác:
     ```ini
     ANTHROPIC_API_KEY=tp-s53cpwgzz4ms1zmrlboyax7xgbrcaj473vadwwoak17zyeh8
     OPENAI_API_KEY=tp-s53cpwgzz4ms1zmrlboyax7xgbrcaj473vadwwoak17zyeh8
     OPENAI_BASE_URL=https://token-plan-sgp.xiaomimimo.com/v1
     ANTHROPIC_BASE_URL=https://token-plan-sgp.xiaomimimo.com/anthropic
     DEFAULT_MODEL=mimo-v2.5-pro
     ```
3. Cài đặt các thư viện Python cần thiết:
   ```bash
   pip install -r requirements.txt
   ```
4. Khởi chạy máy chủ Backend:
   ```bash
   python -m uvicorn app.main:app --port 8000 --reload
   ```
   *Máy chủ Backend sẽ lắng nghe tại địa chỉ: **`http://127.0.0.1:8000`***

---

### Bước 3: Cài đặt và Chạy Frontend (Next.js)

Mở một cửa sổ Terminal mới song song:

1. Di chuyển vào thư mục `frontend/`:
   ```bash
   cd frontend
   ```
2. Cài đặt toàn bộ các gói thư viện NPM:
   ```bash
   npm install
   ```
3. Khởi chạy máy chủ giao diện ở chế độ nhà phát triển (Turbopack):
   ```bash
   npm run dev
   ```
   *Giao diện Chatbot sẽ hoạt động tại địa chỉ: **`http://localhost:3000`***

---

## 🛠️ Kiểm thử & Xác minh hoạt động

1. Truy cập địa chỉ **`http://localhost:3000`** trên trình duyệt của bạn (sẽ tự động chuyển hướng đến `/chat`).
2. Nhấp chọn một trong **4 thẻ gợi ý prompts mẫu** (ví dụ: *Giải thích Đệ quy*) hoặc tự nhập tin nhắn bất kỳ.
3. **Kiểm tra huy hiệu Telemetry**: Dưới mỗi bong bóng câu trả lời của AI Robot sẽ xuất hiện một thanh thông tin hiển thị chính xác:
   - 🚀 Tốc độ sinh từ (`tok/s`)
   - ⏱️ Thời gian phản hồi độ trễ (`s`)
   - 🧩 Tổng lượng token tiêu thụ (`tokens`)
4. **Xem thống kê toàn hệ thống**: Truy cập **`http://127.0.0.1:8000/api/metrics`** hoặc nhấp vào nút **Báo cáo hiệu năng API** ở cuối Sidebar để xem thống kê trung bình về độ trễ và lượng token tiêu thụ trong toàn bộ phiên hoạt động.
