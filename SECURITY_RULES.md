# Security rule base cho chatbot tra cứu điểm tiếng Anh

## Mục tiêu

Rule base này bảo vệ chatbot local ở 3 điểm:

1. Trước khi nhận input người dùng.
2. Trước khi agent gọi tool như `Grade_Search_Tool` hoặc `Study_Plan_Generator`.
3. Trước khi dữ liệu từ tool được đưa lại cho model hoặc trả về người dùng.

Module chính: `security/rule_base.py`.

## Các nhóm rule đã có

- `SEC_PROMPT_INJECTION`: chặn yêu cầu bỏ qua chỉ dẫn, tiết lộ system prompt, jailbreak, bypass bảo mật.
- `SEC_STUDENT_SCOPE` và `SEC_TOOL_STUDENT_SCOPE`: chặn tra cứu điểm của học viên khác nếu user không có quyền.
- `SEC_TOOL_NOT_ALLOWED`: chỉ cho phép agent gọi 5 tool đã định nghĩa: `Grade_Search_Tool`, `Score_Analyzer`, `Learning_Gap_Detector`, `Study_Plan_Generator`, `Stop`.
- `SEC_TOOL_ARGS_*`: chặn tool-call thiếu tham số, thừa tham số hoặc sai schema.
- `SEC_SQL_INJECTION`, `SEC_XSS`, `SEC_PATH_TRAVERSAL`, `SEC_COMMAND_INJECTION`: chặn các mẫu tấn công phổ biến từ bên ngoài.
- `SEC_SECRET_EXFILTRATION`: chặn yêu cầu lấy `.env`, API key, token.
- `SEC_TOOL_RESULT_SECRET_REDACTED`: tự động che các field giống secret trong tool result.
- `SEC_DURATION_RANGE`: giới hạn thời lượng học tối đa 90 ngày để tránh input bất thường.

## Cách tích hợp vào chatbot

Ví dụ khi nhận message:

```python
from security import SecurityContext, validate_message

context = SecurityContext(
    user_id=current_user.id,
    student_id=current_user.student_id,
    allowed_student_ids=frozenset({current_user.student_id}),
)

decision = validate_message(user_message, context)
if not decision.allowed:
    return "Yêu cầu không hợp lệ hoặc vượt phạm vi quyền truy cập."

safe_message = decision.sanitized_input
```

Ví dụ trước khi gọi tool:

```python
from security import validate_tool_call

tool_decision = validate_tool_call(
    "Grade_Search_Tool",
    {"student_id": "SV001", "course_name": "IELTS Mock Test"},
    context,
)

if not tool_decision.allowed:
    raise PermissionError(tool_decision.findings)

result = Grade_Search_Tool(**tool_decision.normalized_args)
```

Ví dụ trước khi dùng tool result:

```python
from security import validate_tool_result

result_decision = validate_tool_result("Grade_Search_Tool", result, context)
if not result_decision.allowed:
    raise PermissionError(result_decision.findings)

safe_result = result_decision.normalized_args
```
