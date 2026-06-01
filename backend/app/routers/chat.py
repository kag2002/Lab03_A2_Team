import time
import logging
from fastapi import APIRouter, HTTPException
from app.schemas.chat import ChatRequest, ChatResponse, ChatResponseUsage
from app.guardrails.input_moderation import input_moderation
from app.guardrails.output_moderation import output_moderation
from app.services.llm_service import llm_service
from app.services.token_service import count_messages_tokens, count_string_tokens
from app.monitoring.metrics import metrics_collector

logger = logging.getLogger("app.routers.chat")
router = APIRouter(prefix="/api")

FORMATTING_GUARDRAILS = """
# CHỈ THỊ BẮT BUỘC VỀ ĐỊNH DẠNG ĐẦU RA (OUTPUT FORMATTING GUARDRAILS)

Bạn là một trợ lý AI hoạt động trong hệ thống Chatbot Stream thời gian thực. Để tránh làm vỡ giao diện (UI) của Frontend, bạn TUYỆT ĐỐI phải tuân thủ các quy tắc định dạng Markdown chuẩn hóa dưới đây trong mọi phản hồi:

## 1. QUY TẮC KHỐI MÃ (CODE BLOCKS)
* **Phải có tên ngôn ngữ:** Luôn luôn chỉ định rõ ngôn ngữ lập trình ngay sau dấu backtick mở (Ví dụ: ```python, ```javascript, ```html). KHÔNG ĐƯỢC để trống hoặc chỉ ghi chung chung là ```code.
* **Cú pháp đóng/mở:** Dấu mở (```) và dấu đóng (```) phải nằm trên một dòng riêng biệt. Không viết dính liền với code hoặc văn bản thô.
* **Không lồng khối mã:** Không bao giờ viết một khối mã khác bên trong một khối mã đang có.

## 2. QUY TẮC ĐỊNH DẠNG BẢNG (TABLES)
* **Cú pháp Markdown chuẩn:** Luôn sử dụng cú pháp bảng chuẩn của GitHub Flavored Markdown (GFM). Phải có đầy đủ dòng phân cách tiêu đề `|---|---|`.
* **Không viết văn bản thô dính liền:** Luôn để một dòng trống trước khi bắt đầu một bảng và một dòng trống sau khi kết thúc bảng.
* **Đóng bảng ngay lập tức:** Đảm bảo mỗi dòng trong bảng đều bắt đầu bằng dấu `|` và kết thúc bằng dấu `|`. Không để lửng lơ cú pháp ở cuối dòng.

## 3. QUY TẮC CÔNG THỨC TOÁN HỌC (LATEX)
* **Inline Math:** Đối với công thức nằm trên cùng một dòng văn bản, chỉ được dùng MỘT dấu đô-la (Ví dụ: $E = mc^2$).
* **Block Math:** Đối với công thức độc lập nằm riêng một dòng, phải dùng ĐÚNG HAI dấu đô-la ở đầu và cuối, và đặt trên dòng riêng (Ví dụ: $$\\sum_{i=1}^{n} i$$).
* **Tuyệt đối cấm:** Không tự ý dùng các ký tự lạ hoặc dùng dấu backslash `\\[ ... \\]` để viết công thức toán vì bộ parser Frontend sẽ bị lỗi.

## 4. QUY TẮC XUỐNG DÒNG VÀ ĐOẠN VĂN (SPACING & LINE BREAKS)
* **Ngắt đoạn rõ ràng:** Giữa các phân đoạn văn bản, giữa tiêu đề (Headers) và nội dung phải cách nhau chính xác MỘT dòng trống.
* **Không lạm dụng dấu xuống dòng:** Không xuống dòng vô tội vạ khi chưa hết câu hoặc chưa hết ý, điều này làm luồng stream bị giật cục trên UI.

## 5. NGUYÊN TẮC STREAMING AN TOÀN
* KHÔNG ĐƯỢC sinh ra các ký tự thô điều hướng hệ thống (như lộ dấu backtick \\`, lộ dấu gạch đứng | ở cuối câu khi câu đó không thuộc bảng/code).
* Nếu người dùng yêu cầu viết mã HTML/JS, hãy đặt toàn bộ chúng vào trong Code Block chuyên biệt. Tuyệt đối không viết trực tiếp mã HTML ra ngoài văn bản thô để tránh lỗi bảo mật XSS.
"""

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    start_time = time.time()
    
    # 1. Input Moderation Guardrail
    for msg in request.messages:
        is_safe, checked_text = await input_moderation.check_prompt(msg.content)
        if not is_safe:
            raise HTTPException(status_code=400, detail="User message failed input safety moderation.")
        msg.content = checked_text  # Update with sanitized text if modified
        
    # Inject Output Formatting Guardrails to system prompt
    payload_messages = []
    system_msg_index = -1
    for idx, msg in enumerate(request.messages):
        if msg.role == "system":
            system_msg_index = idx
            break
            
    if system_msg_index != -1:
        # Append to existing system prompt
        original_system_msg = request.messages[system_msg_index]
        updated_content = f"{original_system_msg.content}\n\n{FORMATTING_GUARDRAILS}"
        for idx, msg in enumerate(request.messages):
            if idx == system_msg_index:
                payload_messages.append({"role": "system", "content": updated_content})
            else:
                payload_messages.append({"role": msg.role, "content": msg.content})
    else:
        # Prepend new system prompt
        payload_messages.append({"role": "system", "content": FORMATTING_GUARDRAILS.strip()})
        for msg in request.messages:
            payload_messages.append({"role": msg.role, "content": msg.content})

    # 2. LLM Call via LLM Service
    try:
        llm_res = await llm_service.chat_completion(
            messages=payload_messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in LLM call: {e}")
        raise HTTPException(status_code=500, detail=f"LLM Service Error: {str(e)}")

        
    reply = llm_res["reply"]
    model_used = llm_res["model"]
    usage_data = llm_res["usage"]
    
    # 3. Output Moderation Guardrail
    is_safe_output, sanitized_reply = await output_moderation.check_response(reply)
    if not is_safe_output:
        logger.warning("LLM response failed output safety moderation.")
        sanitized_reply = "[Content removed due to output safety moderation policy.]"

    # Compute latency
    total_latency_ms = (time.time() - start_time) * 1000

    # Ensure token counts are filled (fallbacks if API does not return usage)
    prompt_tokens = usage_data.get("prompt_tokens") or count_messages_tokens(request.messages)
    completion_tokens = usage_data.get("completion_tokens") or count_string_tokens(sanitized_reply)
    total_tokens = usage_data.get("total_tokens") or (prompt_tokens + completion_tokens)
    
    # 4. Record Metrics
    metrics_collector.record_request_metrics(
        path="/api/chat",
        latency_ms=total_latency_ms,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens
    )
    
    response_usage = ChatResponseUsage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens
    )
    
    return ChatResponse(
        reply=sanitized_reply,
        model=model_used,
        usage=response_usage,
        latency_ms=total_latency_ms
    )
