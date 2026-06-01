import logging

logger = logging.getLogger("app.guardrails.output_moderation")

class OutputModeration:
    async def check_response(self, text: str) -> tuple[bool, str]:
        """
        Temporarily pass-through guardrail for LLM response content.
        Returns:
          - is_safe: bool
          - modified_text or original_text: str
        """
        logger.info(f"Checking LLM response safety: '{text[:50]}...'")
        # Dummy pass-through logic: always returns safe
        return True, text

output_moderation = OutputModeration()
