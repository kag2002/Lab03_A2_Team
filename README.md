# EduTrace TOEIC Agent

EduTrace TOEIC Agent là ứng dụng chatbot/agent hỗ trợ **giáo viên** phân tích kết quả TOEIC của học sinh và tạo lộ trình học cá nhân hóa. Giáo viên có thể hỏi bằng ngôn ngữ tự nhiên, ví dụ tra cứu điểm của một học sinh, phân tích kỹ năng yếu, hoặc yêu cầu lập kế hoạch ôn tập theo thời lượng cụ thể.

Dự án được xây dựng theo mô hình fullstack:

- **Frontend**: Next.js + TypeScript, cung cấp giao diện chat.
- **Backend**: FastAPI, xử lý chat API, agent tool loop, guardrails, telemetry và JSON trace log.
- **Data**: CSV local cho điểm TOEIC theo từng kỹ năng.
- **LLM**: OpenAI-compatible chat completion endpoint, cấu hình qua `backend/.env`.

---

## 1. Bài toán

Trong lớp học TOEIC, giáo viên thường có nhiều bảng điểm của học sinh nhưng mất thời gian để phân tích thủ công từng bạn. Một bảng điểm chỉ cho biết học sinh đạt bao nhiêu điểm, nhưng chưa trả lời rõ:

- Học sinh đang yếu kỹ năng nào?
- Lỗ hổng cụ thể nằm ở phần nào của bài TOEIC?
- Nên ưu tiên luyện gì trước?
- Nếu có 2 tuần hoặc 4 tuần thì nên học theo lộ trình nào?

EduTrace giải quyết bài toán này bằng một agent có thể:

```text
Tra cứu điểm TOEIC
→ Phân tích điểm mạnh/yếu
→ Phát hiện lỗ hổng học tập
→ Tạo lộ trình ôn tập cá nhân hóa
```

Persona chính hiện tại là **giáo viên**. Học sinh là đối tượng được phân tích và nhận lộ trình học.

---

## 2. Tính năng chính

- Giao diện chat cho giáo viên.
- Tra cứu điểm TOEIC theo mã học sinh.
- Đọc dữ liệu từ các file CSV trong thư mục `data/`.
- Agent tool loop tối đa 5 lượt để tránh vòng lặp vô hạn.
- Tool-calling cho các bước tra cứu, phân tích, phát hiện lỗ hổng và lập kế hoạch.
- Rule-base security để kiểm tra input, tool call và tool result.
- Output moderation để che secret/API key nếu vô tình xuất hiện.
- Telemetry: latency, prompt tokens, completion tokens, total tokens.
- JSON trace log tại `backend/logs/agent_traces.jsonl` để debug từng giai đoạn xử lý.

---

## 3. Kiến trúc

```text
Teacher
  |
  v
Frontend Next.js
  |
  v
Backend FastAPI /api/chat
  |
  v
Input Moderation + Rule-base Security
  |
  v
LLM Agent Tool Loop
  |
  +--> Grade_Search_Tool
  +--> Score_Analyzer
  +--> Learning_Gap_Detector
  +--> Study_Plan_Generator
  +--> Stop
  |
  v
Output Moderation + Telemetry + JSON Trace
  |
  v
Chat Response
```

---

## 4. Công cụ của agent

| Tool                    | Vai trò                                                      |
| :---------------------- | :----------------------------------------------------------- |
| `Grade_Search_Tool`     | Tra cứu bảng điểm TOEIC của học sinh theo `student_id`.      |
| `Score_Analyzer`        | Phân tích điểm từng kỹ năng và xác định phần mạnh/yếu.       |
| `Learning_Gap_Detector` | Xác định lỗ hổng học tập từ các phần điểm thấp.              |
| `Study_Plan_Generator`  | Tạo lộ trình ôn tập cá nhân hóa theo điểm và thời lượng học. |
| `Stop`                  | Dừng vòng lặp tool khi đã đủ thông tin.                      |

---

## 5. Cấu trúc thư mục

```text
.
├── backend/
│   ├── app/
│   │   ├── guardrails/        # Input/output moderation
│   │   ├── middlewares/       # Request tracking
│   │   ├── monitoring/        # Metrics, logger, JSON trace logger
│   │   ├── routers/           # API routes
│   │   ├── schemas/           # Pydantic schemas
│   │   └── services/          # LLM service, agent tools, grade service
│   ├── requirements.txt
│   └── test_post.py
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── store/
│   │   └── types/
│   └── package.json
├── data/
│   ├── listening.csv
│   ├── reading.csv
│   ├── speaking.csv
│   └── writing.csv
├── security/
│   └── rule_base.py
├── report/
├── scripts/
├── SECURITY_RULES.md
└── RUN.md
```

---

## 6. Yêu cầu hệ thống

- Python 3.10+
- Node.js 18+
- npm
- Git

Khuyến nghị chạy trên PowerShell nếu dùng Windows.

---

## 7. Cấu hình môi trường

Backend cần file:

```text
backend/.env
```

Ví dụ cấu trúc:

```env
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://your-openai-compatible-endpoint/v1
DEFAULT_MODEL=your-model-name
LOG_LEVEL=INFO
```

Lưu ý:

- Không commit `backend/.env`.
- Không đưa API key thật vào `.env.example`.
- `OPENAI_BASE_URL` chỉ nên trỏ tới base `/v1`, vì backend tự ghép thêm `/chat/completions`.

Ví dụ:

```env
OPENAI_BASE_URL=https://example.com/v1
```

Backend sẽ gọi:

```text
https://example.com/v1/chat/completions
```

---

## 8. Chạy backend

Mở terminal tại thư mục gốc project:

```powershell
cd backend
```

Tạo virtual environment nếu chưa có:

```powershell
python -m venv .venv
```

Kích hoạt môi trường:

```powershell
.\.venv\Scripts\Activate.ps1
```

Nếu PowerShell chặn activate script:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Cài dependencies:

```powershell
pip install -r requirements.txt
```

Chạy backend:

```powershell
python -m uvicorn app.main:app --port 8000 --reload
```

Backend chạy tại:

```text
http://127.0.0.1:8000
```

Kiểm tra backend:

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/api/health
http://127.0.0.1:8000/api/metrics
```

---

## 9. Chạy frontend

Mở terminal thứ hai tại thư mục gốc project:

```powershell
cd frontend
```

Cài dependencies:

```powershell
npm install
```

Chạy frontend:

```powershell
npm run dev
```

Frontend chạy tại:

```text
http://localhost:3000
```

Trang chat:

```text
http://localhost:3000/chat
```

Frontend hiện gọi backend tại:

```text
http://127.0.0.1:8000/api
```

Vì vậy backend cần chạy ở port `8000`.

---

## 10. Thứ tự chạy khuyến nghị

Terminal 1:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --port 8000 --reload
```

Terminal 2:

```powershell
cd frontend
npm run dev
```

Sau đó mở:

```text
http://localhost:3000/chat
```

---

## 11. Kiểm thử nhanh backend

Sau khi backend đang chạy, mở terminal khác:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python test_post.py
```

Nếu thành công, terminal sẽ in response từ `/api/chat` với status `200`.

---

## 12. Telemetry và trace log

Backend ghi metrics tại endpoint:

```text
http://127.0.0.1:8000/api/metrics
```

Trace log theo từng request được ghi vào:

```text
backend/logs/agent_traces.jsonl
```

Mỗi dòng là một JSON object gồm các stage như:

```text
request_received
input_moderation
system_prompt_built
agent_loop_started
llm_call
tool_call_started
tool_call_finished
final_synthesis_started
final_synthesis_finished
output_moderation
metrics_recorded
```

File log runtime đã được ignore bằng `.gitignore`.

---

## 13. Bảo mật và guardrails

Rule-base chính nằm tại:

```text
security/rule_base.py
```

Các nhóm rule hiện có:

- Chặn prompt injection.
- Chặn yêu cầu lấy `.env`, API key, token.
- Chặn SQL injection, XSS, path traversal, command injection.
- Kiểm tra quyền truy cập học sinh theo `SecurityContext`.
- Chỉ cho phép agent gọi tool trong allowlist.
- Kiểm tra schema tham số tool.
- Kiểm tra tool result để tránh trả nhầm dữ liệu học sinh khác.
- Redact secret trong output/tool result.

Tài liệu chi tiết:

```text
SECURITY_RULES.md
```

---

## 14. Lỗi thường gặp

### Backend báo `ModuleNotFoundError: No module named 'fastapi'`

Bạn đang chạy sai Python hoặc chưa kích hoạt virtual environment.

Chạy lại:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --port 8000 --reload
```

### `test_post.py` báo `WinError 10061`

Không có backend nào đang chạy ở `127.0.0.1:8000`.

Hãy chạy backend trước:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --port 8000 --reload
```

### Frontend không gửi được tin nhắn

Kiểm tra backend:

```text
http://127.0.0.1:8000/api/health
```

Nếu health không mở được, backend chưa chạy hoặc sai port.

Nếu mở frontend bằng link network như:

```text
http://172.x.x.x:3000
```

cần lưu ý frontend đang gọi backend qua:

```text
http://127.0.0.1:8000/api
```

Nếu mở từ máy khác trong mạng LAN, `127.0.0.1` sẽ trỏ về chính máy đang mở browser, không phải máy chạy backend.

### Next.js báo blocked cross-origin dev resource

Nếu mở frontend bằng IP LAN, Next.js dev server có thể báo:

```text
Blocked cross-origin request to Next.js dev resource
```

Cách đơn giản nhất khi chạy cùng máy là mở:

```text
http://localhost:3000/chat
```

### Backend trả lỗi `500 Internal Server Error`

Nếu backend chạy được nhưng `/api/chat` trả lỗi `500`, nguyên nhân thường gặp là cấu hình LLM endpoint hoặc API key trong `backend/.env` không còn hợp lệ, hết hạn, sai base URL, hoặc endpoint tạm thời không truy cập được.

Trong trường hợp này, hãy liên hệ **nhóm tác giả** để được cấp lại file `.env` hoặc thông tin endpoint/API key mới.

Sau khi cập nhật `.env`, cần restart backend:

```powershell
Ctrl + C
python -m uvicorn app.main:app --port 8000 --reload
```

---

## 15. Git hook và AI logging của khóa học

Repo vẫn giữ các script logging của khóa học trong thư mục `scripts/`.

Cài hook trên Windows:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup_hooks.ps1
```

Cài hook trên Linux/macOS/Git Bash:

```bash
bash scripts/setup_hooks.sh
```

Nếu push báo remote có thay đổi mới:

```powershell
git pull --rebase origin main
git push
```

---

## 16. Báo cáo

Báo cáo nhóm và báo cáo cá nhân nằm trong:

```text
report/group_report/
report/individual_reports/
```

---

## 17. Team

**Team bàn A02 (team 8)**

- Trần Đức Đăng Khôi
- Nguyễn Thụy Như Quỳnh
- Lê Thiên Khang
- Phạm Thành Nam
