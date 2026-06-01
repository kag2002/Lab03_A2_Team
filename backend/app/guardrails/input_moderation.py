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
            "Bạn là một hệ thống kiểm duyệt chủ đề. Nhiệm vụ của bạn là chặn các chủ đề HOÀN TOÀN KHÔNG LIÊN QUAN (ví dụ: nấu ăn, thể thao, game, chính trị, bạo lực, tư vấn tình cảm, viết code chung chung...).\n"
            "Các chủ đề HỢP LỆ bao gồm: giáo dục, trường học, học sinh, sinh viên, mã ID, tra cứu điểm số, ôn thi, chứng chỉ tiếng Anh, hoặc các câu chào hỏi thông thường.\n\n"
            "QUY TẮC:\n"
            "- Nếu tin nhắn thuộc chủ đề hợp lệ hoặc bạn KHÔNG CHẮC CHẮN (ví dụ câu hỏi quá ngắn nhưng không có từ khóa cấm), hãy trả về: SAFE\n"
            "- CHỈ khi tin nhắn rõ ràng hỏi về chủ đề không liên quan, mới trả về: OFF_TOPIC\n"
            "Chỉ trả về đúng 1 từ SAFE hoặc OFF_TOPIC, không giải thích gì thêm."
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
