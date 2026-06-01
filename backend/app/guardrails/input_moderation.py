import logging

logger = logging.getLogger("app.guardrails.input_moderation")

class InputModeration:
    async def check_prompt(self, text: str) -> tuple[bool, str]:
        """
        Temporarily pass-through guardrail for user input.
        Returns:
          - is_safe: bool
          - modified_text or original_text: str
        """
        logger.info(f"Checking input prompt safety: '{text[:50]}...'")
        # Dummy pass-through logic: always returns safe
        return True, text

input_moderation = InputModeration()
