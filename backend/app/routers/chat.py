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

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    start_time = time.time()
    
    # 1. Input Moderation Guardrail
    for msg in request.messages:
        is_safe, checked_text = await input_moderation.check_prompt(msg.content)
        if not is_safe:
            raise HTTPException(status_code=400, detail="User message failed input safety moderation.")
        msg.content = checked_text  # Update with sanitized text if modified
        
    # 2. LLM Call via LLM Service
    try:
        llm_res = await llm_service.chat_completion(
            messages=request.messages,
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
