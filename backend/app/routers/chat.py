import time
import json
import logging
import sys
import uuid
from pathlib import Path
from fastapi import APIRouter, HTTPException
from app.schemas.chat import ChatRequest, ChatResponse, ChatResponseUsage
from app.guardrails.input_moderation import input_moderation
from app.guardrails.output_moderation import output_moderation
from app.services.llm_service import llm_service
from app.services.token_service import count_messages_tokens, count_string_tokens
from app.monitoring.metrics import metrics_collector
from app.monitoring.trace_logger import json_trace_logger, safe_preview, utc_now_iso
from app.services.agent_tools import agent_tools

# Add project root directory to system path to import security module
root_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

from security.rule_base import SecurityContext

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

# Define agent tools schemas in standard OpenAI format
AGENT_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "Grade_Search_Tool",
            "description": "Tra cứu bảng điểm TOEIC đầy đủ của học sinh theo mã student_id (dạng SVXXX) và tên kỳ thi (ví dụ: 'TOEIC'). Bạn PHẢI chạy công cụ này trước tiên để có thông tin điểm thực tế của học sinh.",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {
                        "type": "string",
                        "description": "Mã định danh học sinh, ví dụ 'SV001', 'SV002'..."
                    },
                    "course_name": {
                        "type": "string",
                        "description": "Tên kỳ thi/học phần, truyền vào 'TOEIC'"
                    }
                },
                "required": ["student_id", "course_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "Score_Analyzer",
            "description": "Phân tích điểm số chi tiết các kỹ năng (Listening, Reading, Speaking, Writing) trên thang điểm 0-100 để đánh giá điểm mạnh, điểm yếu chính xác.",
            "parameters": {
                "type": "object",
                "properties": {
                    "scores": {
                        "type": "object",
                        "description": "Mẫu dữ liệu: {'Listening': 90, 'Reading': 85, 'Speaking': 70, 'Writing': 90}",
                        "additionalProperties": {
                            "type": "number"
                        }
                    }
                },
                "required": ["scores"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "Learning_Gap_Detector",
            "description": "Nhận diện lỗ hổng kiến thức học tập dựa trên danh sách các phần thi nhỏ có điểm số hoặc tỷ lệ làm đúng thấp (ví dụ: P3, P7, Ngữ pháp).",
            "parameters": {
                "type": "object",
                "properties": {
                    "low_score_parts": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "Danh sách các phần hoặc kỹ năng có điểm thấp."
                    }
                },
                "required": ["low_score_parts"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "Study_Plan_Generator",
            "description": "Lập kế hoạch lộ trình học tập CÁ NHÂN HÓA dựa trên điểm thực tế từng kỹ năng. QUAN TRỌNG: mỗi phần tử trong weak_topics PHẢI có định dạng 'TenKyNang:diem' để hệ thống tạo kế hoạch phù hợp mức độ, ví dụ: ['Listening:62', 'Reading:45', 'Speaking:70']. Không được truyền tên kỹ năng đơn thuần mà thiếu điểm số.",
            "parameters": {
                "type": "object",
                "properties": {
                    "weak_topics": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "Danh sách kỹ năng yếu theo định dạng 'TenKyNang:diem_thuc_te', ví dụ ['Listening:62', 'Reading:45']. Điểm lấy từ kết quả Grade_Search_Tool."
                    },
                    "duration": {
                        "type": "string",
                        "description": "Thời lượng học, ví dụ '2 tuần', '4 weeks', '30 ngày'..."
                    }
                },
                "required": ["weak_topics", "duration"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "Stop",
            "description": "Dừng vòng lặp gọi công cụ sau khi đã giải quyết xong yêu cầu tra cứu và phân tích điểm cho người dùng.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    start_time = time.time()
    request_id = str(uuid.uuid4())
    trace = {
        "request_id": request_id,
        "started_at": utc_now_iso(),
        "endpoint": "/api/chat",
        "model": llm_service.default_model,
        "context": {},
        "stages": []
    }

    def add_stage(stage: str, status: str = "ok", **data):
        trace["stages"].append({
            "timestamp": utc_now_iso(),
            "elapsed_ms": round((time.time() - start_time) * 1000, 2),
            "stage": stage,
            "status": status,
            **safe_preview(data)
        })
    
    # 1. Initialize Security Context based on request meta
    context = SecurityContext(
        user_id=request.user_id,
        student_id=request.student_id,
        allowed_student_ids=frozenset(request.allowed_student_ids or []),
        role=request.role or "student"
    )
    trace["context"] = {
        "user_id": context.user_id,
        "role": context.role,
        "student_id": context.student_id,
        "allowed_student_ids": sorted(context.allowed_student_ids)
    }
    add_stage(
        "request_received",
        message_count=len(request.messages),
        roles=[msg.role for msg in request.messages],
        temperature=request.temperature,
        max_tokens=request.max_tokens
    )
    
    # 2. Input Moderation Guardrail
    for msg in request.messages:
        if msg.role == "user":
            is_safe, checked_text = await input_moderation.check_prompt(msg.content, context)
            if not is_safe:
                total_latency_ms = (time.time() - start_time) * 1000
                add_stage(
                    "input_moderation",
                    "blocked",
                    role=msg.role,
                    content_preview=msg.content,
                    sanitized_preview=checked_text
                )
                response = ChatResponse(
                    reply="[HỆ THỐNG BẢO MẬT] Tin nhắn của bạn đã bị từ chối do vi phạm quy tắc an toàn thông tin hoặc truy cập trái phép dữ liệu học sinh ngoài phạm vi được cấp quyền.",
                    model=llm_service.default_model,
                    usage=ChatResponseUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
                    latency_ms=total_latency_ms
                )
                trace["finished_at"] = utc_now_iso()
                trace["status"] = "blocked"
                trace["latency_ms"] = total_latency_ms
                trace["response"] = {
                    "reply_preview": response.reply,
                    "usage": response.usage.model_dump(),
                    "latency_ms": response.latency_ms
                }
                json_trace_logger.write_trace(trace)
                return response
            add_stage(
                "input_moderation",
                "passed",
                role=msg.role,
                content_preview=msg.content,
                sanitized_preview=checked_text
            )
            msg.content = checked_text  # Update with sanitized text if modified

    # Build initial message chain with system instructions
    system_prompt = (
        f"{FORMATTING_GUARDRAILS.strip()}\n\n"
        "Bạn là Trợ lý Học tập AI đắc lực. Bạn hỗ trợ tra cứu điểm số TOEIC 4 kỹ năng của học sinh "
        "và xây dựng lộ trình ôn tập cá nhân hóa.\n"
        "QUY TẮC BẢO MẬT:\n"
        "1. Chỉ truy cập và hiển thị thông tin khi học sinh được phép truy cập theo đúng phạm vi phân quyền.\n"
        "2. Luôn sử dụng các công cụ an toàn hệ thống (Grade_Search_Tool, Score_Analyzer, v.v.) để tra cứu thay vì tự suy đoán.\n"
        "3. Trả lời bằng tiếng Việt lịch sự, thân thiện và tuân thủ các quy tắc định dạng đầu ra (Markdown, Spacing)."
    )
    
    payload_messages = [{"role": "system", "content": system_prompt}]
    for msg in request.messages:
        payload_messages.append({"role": msg.role, "content": msg.content})
    add_stage(
        "system_prompt_built",
        payload_message_count=len(payload_messages),
        system_prompt_preview=system_prompt
    )

    # 3. Agent Tool Loop execution (Max 5 turns)
    loop_count = 0
    total_prompt_tokens = 0
    total_completion_tokens = 0
    final_reply = ""
    
    while loop_count < 5:
        loop_count += 1
        logger.info(f"Agent Loop turn {loop_count}/5 initiated...")
        add_stage(
            "agent_loop_started",
            loop=loop_count,
            payload_message_count=len(payload_messages)
        )
        
        try:
            llm_res = await llm_service.chat_completion(
                messages=payload_messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                tools=AGENT_TOOLS_SCHEMA
            )
        except Exception as e:
            import traceback
            tb_str = traceback.format_exc()
            logger.error(f"Unexpected error in LLM call: {e}\n{tb_str}")
            add_stage(
                "llm_call",
                "error",
                loop=loop_count,
                error=str(e)
            )
            trace["finished_at"] = utc_now_iso()
            trace["status"] = "error"
            trace["latency_ms"] = (time.time() - start_time) * 1000
            json_trace_logger.write_trace(trace)
            raise HTTPException(status_code=500, detail=f"LLM Service Error: {str(e)}\n{tb_str}")

        usage_data = llm_res.get("usage") or {}
        total_prompt_tokens += usage_data.get("prompt_tokens", 0)
        total_completion_tokens += usage_data.get("completion_tokens", 0)

        reply = llm_res.get("reply")
        tool_calls = llm_res.get("tool_calls")
        add_stage(
            "llm_call",
            "completed",
            loop=loop_count,
            reply_preview=reply,
            tool_call_count=len(tool_calls or []),
            tool_names=[
                call.get("function", {}).get("name")
                for call in (tool_calls or [])
            ],
            usage=usage_data
        )

        # Record assistant turn in payload
        assistant_turn = {"role": "assistant"}
        if reply is not None:
            assistant_turn["content"] = reply
        if tool_calls is not None:
            assistant_turn["tool_calls"] = tool_calls
        payload_messages.append(assistant_turn)

        if reply:
            final_reply = reply

        if not tool_calls:
            logger.info("No tool calls requested by model. Agent loop finalized.")
            add_stage(
                "agent_loop_finished",
                reason="no_tool_calls",
                loop=loop_count
            )
            break

        # Process each requested tool call
        stop_called = False
        for tool_call in tool_calls:
            tool_name = tool_call["function"]["name"]
            call_id = tool_call["id"]
            
            try:
                args = json.loads(tool_call["function"]["arguments"])
            except Exception:
                args = {}
                add_stage(
                    "tool_arguments_parse",
                    "error",
                    loop=loop_count,
                    tool_name=tool_name,
                    call_id=call_id,
                    raw_arguments=tool_call["function"].get("arguments")
                )

            if tool_name == "Stop":
                stop_called = True

            # Safely execute the tool
            logger.info(f"Executing tool '{tool_name}' for call '{call_id}'...")
            add_stage(
                "tool_call_started",
                loop=loop_count,
                tool_name=tool_name,
                call_id=call_id,
                args=args
            )
            tool_result = await agent_tools.execute_tool(tool_name, args, context)
            add_stage(
                "tool_call_finished",
                loop=loop_count,
                tool_name=tool_name,
                call_id=call_id,
                result=tool_result
            )

            # Record tool output in history
            payload_messages.append({
                "role": "tool",
                "name": tool_name,
                "tool_call_id": call_id,
                "content": json.dumps(tool_result, ensure_ascii=False)
            })

        if stop_called:
            logger.info("Stop tool invoked by agent. Breaking tool loop.")
            add_stage(
                "agent_loop_finished",
                reason="stop_tool_called",
                loop=loop_count
            )
            break

    # If the last turn was a tool output and we haven't summarized, run one final turn to construct response
    if not final_reply or (payload_messages and payload_messages[-1]["role"] == "tool"):
        logger.info("Running final synthesis call to summarize tool results...")
        add_stage(
            "final_synthesis_started",
            payload_message_count=len(payload_messages)
        )
        try:
            llm_res = await llm_service.chat_completion(
                messages=payload_messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                tools=None
            )
            usage_data = llm_res.get("usage") or {}
            total_prompt_tokens += usage_data.get("prompt_tokens", 0)
            total_completion_tokens += usage_data.get("completion_tokens", 0)
            final_reply = llm_res.get("reply") or ""
            add_stage(
                "final_synthesis_finished",
                reply_preview=final_reply,
                usage=usage_data
            )
        except Exception as e:
            logger.error(f"Synthesis completion failed: {e}")
            final_reply = "Xin lỗi, đã xảy ra lỗi trong quá trình tổng hợp kết quả phân tích điểm."
            add_stage(
                "final_synthesis_finished",
                "error",
                error=str(e),
                fallback_reply=final_reply
            )

    # 4. Output Moderation Guardrail (Sanitize secrets / API keys)
    is_safe_output, sanitized_reply = await output_moderation.check_response(final_reply)
    add_stage(
        "output_moderation",
        "passed" if is_safe_output else "blocked",
        reply_preview=final_reply,
        sanitized_preview=sanitized_reply
    )

    # Calculate final latency
    total_latency_ms = (time.time() - start_time) * 1000

    # Fallback default tokens if they evaluate to zero
    if total_prompt_tokens == 0:
        total_prompt_tokens = count_messages_tokens(request.messages)
    if total_completion_tokens == 0:
        total_completion_tokens = count_string_tokens(sanitized_reply)
    total_tokens = total_prompt_tokens + total_completion_tokens
    
    # 5. Record final session metrics
    metrics_collector.record_request_metrics(
        path="/api/chat",
        latency_ms=total_latency_ms,
        prompt_tokens=total_prompt_tokens,
        completion_tokens=total_completion_tokens
    )
    add_stage(
        "metrics_recorded",
        latency_ms=total_latency_ms,
        prompt_tokens=total_prompt_tokens,
        completion_tokens=total_completion_tokens,
        total_tokens=total_tokens
    )
    
    response_usage = ChatResponseUsage(
        prompt_tokens=total_prompt_tokens,
        completion_tokens=total_completion_tokens,
        total_tokens=total_tokens
    )
    
    response = ChatResponse(
        reply=sanitized_reply,
        model=llm_service.default_model,
        usage=response_usage,
        latency_ms=total_latency_ms
    )
    trace["finished_at"] = utc_now_iso()
    trace["status"] = "completed"
    trace["latency_ms"] = total_latency_ms
    trace["response"] = {
        "reply_preview": sanitized_reply,
        "usage": response_usage.model_dump(),
        "latency_ms": total_latency_ms
    }
    json_trace_logger.write_trace(trace)
    return response
