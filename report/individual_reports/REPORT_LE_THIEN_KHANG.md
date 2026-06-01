# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Lê Thiên Khang
- **Student ID**: 2A202600726
- **Date**: 01/06/2026

---

## I. Technical Contribution (15 Points)

*Mô tả đóng góp kỹ thuật cụ thể vào codebase.*

- **Modules Implemented**:
  - **Frontend (Next.js 14 + TypeScript):** `ChatBox.tsx`, `ChatInput.tsx`, `ChatMessage.tsx`, `Sidebar.tsx` — xây dựng toàn bộ giao diện chatbot.
  - **Backend (FastAPI + Python):** `chat.py` — triển khai vòng lặp Agent Tool Loop (tối đa 5 lượt) với tool-calling.
  - **Agent Tools:** `agent_tools.py` — implement 4 tool: `Grade_Search_Tool`, `Score_Analyzer`, `Learning_Gap_Detector`, `Study_Plan_Generator` với cá nhân hóa theo điểm thực tế.
  - **Local Storage:** `useLocalStorage.ts` — lưu lịch sử hội thoại trên trình duyệt, khôi phục khi tải lại trang.
  - **Local API / Data:** `grade_service.py` — đọc dữ liệu điểm TOEIC từ file CSV local (`data/`) thay vì gọi API bên ngoài.
  - **Security:** Tích hợp `rule_base.py` — kiểm tra IDOR, chặn prompt injection, SQL injection, XSS. Thêm bộ lọc off-topic bằng LLM phụ trong `input_moderation.py`.

- **Code Highlights**:
  - Agent Tool Loop trong `chat.py` : Vòng lặp tối đa 5 turn, mỗi turn LLM quyết định gọi tool hay trả lời. Nếu turn cuối vẫn là tool output → gọi thêm 1 lần synthesis để tổng hợp.
  - `SKILL_PLAYBOOK` trong `agent_tools.py`: Dictionary 3 tầng `skill → tier (low/mid/high) → plan`, cung cấp lộ trình ôn tập cá nhân hóa theo điểm từng kỹ năng.
  - Progress UI trong `useChatStream.ts`: 5-step loading indicator (`Đang xử lý` → `Tra cứu dữ liệu` → `Phân tích điểm` → `Xây dựng lộ trình` → `Hoàn tất`).

- **Documentation**: Frontend gửi request kèm `user_id`, `student_id`, `role` → Backend tạo `SecurityContext` → Input Moderation kiểm tra → Agent Loop: LLM nhận tool schemas → gọi tool → `execute_tool()` thực thi (validate security trước/sau) → kết quả trả về LLM → lặp đến khi gọi `Stop` hoặc hết 5 turn.

---

## II. Debugging Case Study (10 Points)

*Phân tích một sự cố gặp phải trong quá trình phát triển.*

- **Problem Description**: Bộ lọc off-topic (LLM-based) chặn nhầm câu hỏi hợp lệ như *"tôi muốn tham khảo thông tin sinh viên điểm id là 1"*. Người dùng bị block liên tục dù đang hỏi đúng chủ đề tra cứu điểm.

- **Log Source**:
  ```
  WARNING - Input prompt blocked by off-topic filter: tôi muốn tham khảo thông tin sinh viên điểm id là 1...
  ```

- **Diagnosis**: System prompt của LLM kiểm duyệt dùng whitelist cứng (chỉ liệt kê TOEIC, IELTS, ôn thi...). Câu hỏi tự nhiên chứa "id", "sinh viên", "tham khảo" không khớp whitelist nên bị phân loại OFF_TOPIC. Nguyên nhân gốc: thiếu nguyên tắc "mặc định an toàn" (default-safe).

- **Solution**: Viết lại prompt theo hướng "blacklist" thay vì "whitelist": chỉ chặn khi câu hỏi **rõ ràng** thuộc chủ đề cấm (nấu ăn, game, chính trị...). Thêm quy tắc: *"Nếu không chắc chắn → SAFE"*. Kết quả: câu hỏi tra cứu điểm hoạt động bình thường.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Suy ngẫm về sự khác biệt giữa Chatbot và ReAct Agent.*

1. **Reasoning**: Agent suy luận đa bước — khi hỏi *"Tra điểm SV001 và lập lộ trình"*, agent tự chia thành 4 bước: gọi `Grade_Search_Tool` → `Score_Analyzer` → `Learning_Gap_Detector` → `Study_Plan_Generator`. Chatbot thường chỉ trả lời chung chung mà không truy xuất dữ liệu thật.

2. **Reliability**: Agent kém hơn chatbot với câu hỏi đơn giản ("Xin chào", "Cảm ơn") — vì vẫn cố gọi tool không cần thiết, gây chậm 2-3s. Khi LLM API timeout, agent loop 5 turn có thể mất 30-60s, chatbot chỉ cần 1 lần gọi.

3. **Observation**: Feedback từ tool ảnh hưởng trực tiếp đến bước tiếp theo. Ví dụ: `Grade_Search_Tool` trả điểm Reading = 35 → agent gọi `Study_Plan_Generator` với tier "low" (kế hoạch nền tảng). Nếu điểm = 80 → tier "high" (chiến lược nâng cao). Cơ chế observation-driven giúp cá nhân hóa sát thực tế hơn chatbot trả mẫu cố định.

---

## IV. Future Improvements (5 Points)

*Hướng mở rộng cho hệ thống AI agent cấp production.*

- **Scalability**: Tách Agent Tool Loop ra worker queue (Celery/Redis) để xử lý bất đồng bộ, tránh block API server. Thêm caching kết quả tool call giảm truy vấn lặp.
- **Safety**: Triển khai "Supervisor LLM" kiểm tra output agent trước khi trả về — phát hiện hallucination. Bổ sung rate-limiting per user chống lạm dụng.
- **Performance**: Dùng Vector DB (Qdrant/Pinecone) lưu embedding tool descriptions — khi có nhiều tool, LLM chỉ nhận top-K phù hợp, giảm token usage.

---

> [!NOTE]
> Nộp báo cáo bằng cách đổi tên file thành `REPORT_LE_THIEN_KHANG.md` và đặt vào thư mục này.
