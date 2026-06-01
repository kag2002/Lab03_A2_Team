import httpx
import json
import logging
from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from app.config import settings

logger = logging.getLogger("app.services.llm_service")

class LLMService:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = settings.OPENAI_BASE_URL.rstrip("/")
        self.default_model = settings.DEFAULT_MODEL

    async def chat_completion(
        self,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = None,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> dict:
        """
        Asynchronously calls the OpenAI-compatible endpoint with support for tool definitions.
        Returns a dict containing:
          - reply: str (or None if only tool_calls are present)
          - tool_calls: list (or None if no tools are called)
          - model: str
          - usage: dict (prompt_tokens, completion_tokens, total_tokens)
        """
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.default_model,
            "messages": [
                {
                    "role": m.role if hasattr(m, "role") else m.get("role"), 
                    "content": m.content if hasattr(m, "content") else m.get("content"),
                    # Preserve tool_calls and name for tool loop history
                    **({"tool_calls": m.get("tool_calls")} if isinstance(m, dict) and m.get("tool_calls") else {}),
                    **({"name": m.get("name")} if isinstance(m, dict) and m.get("name") else {}),
                    **({"tool_call_id": m.get("tool_call_id")} if isinstance(m, dict) and m.get("tool_call_id") else {})
                }
                for m in messages
            ],
            "temperature": temperature
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if tools is not None:
            payload["tools"] = tools

        logger.info(f"Calling LLM API at {url} using model {self.default_model} with {len(messages)} messages...")
        if tools:
            logger.info(f"Passing {len(tools)} tool schemas to the model...")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                if response.status_code != 200:
                    logger.error(f"LLM API returned error status {response.status_code}: {response.text}")
                    raise HTTPException(status_code=response.status_code, detail=f"LLM API Error: {response.text}")
                
                res_data = response.json()
                message_data = res_data["choices"][0]["message"]
                reply = message_data.get("content")
                tool_calls = message_data.get("tool_calls")
                model_used = res_data.get("model", self.default_model)
                usage = res_data.get("usage", {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                })
                
                return {
                    "reply": reply,
                    "tool_calls": tool_calls,
                    "model": model_used,
                    "usage": usage
                }
            except httpx.RequestError as e:
                logger.error(f"HTTP request failed: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to connect to LLM API: {str(e)}")

llm_service = LLMService()
