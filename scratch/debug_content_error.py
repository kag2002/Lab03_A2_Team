import asyncio
import sys
import traceback
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.append(str(backend_dir))

# Setup encoding
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from app.services.llm_service import llm_service
from app.routers.chat import AGENT_TOOLS_SCHEMA

async def main():
    # Simulate Turn 3 message payload
    payload_messages = [
        {"role": "system", "content": "You are a secure assistant."},
        {"role": "user", "content": "Hãy tra cứu bảng điểm TOEIC của học sinh SV001 và phân tích ngắn gọn điểm mạnh, điểm yếu."},
        {
            "role": "assistant",
            "tool_calls": [
                {
                    "id": "call_25e4c456f2554d6995179520",
                    "type": "function",
                    "function": {
                        "name": "Grade_Search_Tool",
                        "arguments": '{"student_id": "SV001", "course_name": "TOEIC"}'
                    }
                }
            ]
        },
        {
            "role": "tool",
            "name": "Grade_Search_Tool",
            "tool_call_id": "call_25e4c456f2554d6995179520",
            "content": '{"status": "success", "student_id": "SV001"}'
        },
        {
            "role": "assistant",
            "tool_calls": [
                {
                    "id": "call_115b69c4aac74014b79b8966",
                    "type": "function",
                    "function": {
                        "name": "Score_Analyzer",
                        "arguments": '{"scores": {"Listening": 92, "Reading": 86, "Speaking": 70, "Writing": 90}}'
                    }
                }
            ]
        },
        {
            "role": "tool",
            "name": "Score_Analyzer",
            "tool_call_id": "call_115b69c4aac74014b79b8966",
            "content": '{"status": "success", "analysis_report": "some analysis"}'
        }
    ]

    print("Running debug chat completion call...")
    try:
        res = await llm_service.chat_completion(
            messages=payload_messages,
            temperature=0.7,
            tools=AGENT_TOOLS_SCHEMA
        )
        print("Success! Response:", res)
    except Exception as e:
        print("Exception occurred:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
