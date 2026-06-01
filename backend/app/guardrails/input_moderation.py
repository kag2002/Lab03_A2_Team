import logging
import sys
from pathlib import Path

# Add project root directory to system path to import security module
root_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

from security.rule_base import validate_message, SecurityContext
from app.services.llm_service import llm_service

logger = logging.getLogger("app.guardrails.input_moderation")

class InputModeration:
    async def check_prompt(self, text: str, context: SecurityContext) -> tuple[bool, str, str]:
        """
        Validates the input prompt using the checked-out rule-based security module 
        and an LLM-based off-topic check.
        Returns:
          - is_safe: bool (True if allowed, False if blocked)
          - sanitized_text: str
          - error_message: str (If blocked, the reason)
        """
        logger.info(f"Checking input prompt safety for user {context.user_id}: '{text[:50]}...'")
        
        # 1. Rule-based check
        decision = validate_message(text, context)
        if not decision.allowed:
            findings_summary = ", ".join([f"{f.rule_id} ({f.severity})" for f in decision.findings])
            logger.warning(f"Input prompt blocked by security rules: {findings_summary}")
            return False, text, "[HỆ THỐNG BẢO MẬT] Tin nhắn của bạn đã bị từ chối do vi phạm quy tắc an toàn thông tin hoặc truy cập trái phép dữ liệu học sinh."
            
        sanitized = decision.sanitized_input if decision.sanitized_input is not None else text
        
        # 2. LLM Topic Check (Off-topic prevention)
        system_prompt = (
            "Bạn là một hệ thống kiểm duyệt chủ đề. Hãy xác định xem tin nhắn của người dùng có thuộc một trong "
            "các chủ đề hợp lệ sau không: giáo dục, trường học, điểm số, ôn thi, chứng chỉ tiếng Anh (TOEIC, IELTS...), "
            "định hướng học tập, hoặc là các câu chào hỏi lịch sự thông thường.\n\n"
            "Nếu tin nhắn thuộc chủ đề hợp lệ, chỉ trả về đúng 1 từ: SAFE\n"
            "Nếu tin nhắn hỏi về các chủ đề không liên quan (ví dụ: viết code chung chung không liên quan học ngoại ngữ, kể chuyện cười, chính trị, thể thao, game, bạo lực, tư vấn tình cảm...), "
            "chỉ trả về đúng 1 từ: OFF_TOPIC"
        )
        
        try:
            llm_res = await llm_service.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.1,
                max_tokens=10
            )
            reply = llm_res.get("reply", "").strip().upper()
            if "OFF_TOPIC" in reply:
                logger.warning(f"Input prompt blocked by off-topic filter: {text[:50]}...")
                return False, text, "[CẢNH BÁO] Tôi là trợ lý học tập AI. Tôi chỉ có thể hỗ trợ các vấn đề liên quan đến tra cứu điểm số, ôn thi, học tập và giáo dục. Vui lòng không hỏi các chủ đề ngoài lề."
        except Exception as e:
            logger.error(f"Error calling LLM for topic check: {e}")
            # If LLM fails, we allow it to proceed to not block user entirely on error
            pass
            
        return True, sanitized, ""

input_moderation = InputModeration()
