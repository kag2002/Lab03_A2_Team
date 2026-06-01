import logging
import sys
from pathlib import Path

# Add project root directory to system path to import security module
root_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

from security.rule_base import validate_message, SecurityContext

logger = logging.getLogger("app.guardrails.input_moderation")

class InputModeration:
    async def check_prompt(self, text: str, context: SecurityContext) -> tuple[bool, str]:
        """
        Validates the input prompt using the checked-out rule-based security module.
        Returns:
          - is_safe: bool (True if allowed, False if blocked)
          - sanitized_text: str
        """
        logger.info(f"Checking input prompt safety for user {context.user_id}: '{text[:50]}...'")
        
        decision = validate_message(text, context)
        
        if not decision.allowed:
            findings_summary = ", ".join([f"{f.rule_id} ({f.severity})" for f in decision.findings])
            logger.warning(f"Input prompt blocked by security rules: {findings_summary}")
            return False, text
            
        sanitized = decision.sanitized_input if decision.sanitized_input is not None else text
        return True, sanitized

input_moderation = InputModeration()
