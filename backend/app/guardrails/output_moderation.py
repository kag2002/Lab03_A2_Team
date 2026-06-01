import logging
import sys
from pathlib import Path

# Add project root directory to system path to import security module
root_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

from security.rule_base import redact_secrets

logger = logging.getLogger("app.guardrails.output_moderation")

class OutputModeration:
    async def check_response(self, text: str) -> tuple[bool, str]:
        """
        Scans LLM response and redacts any sensitive API keys or credentials.
        Returns:
          - is_safe: bool (always True for output, but content is sanitized)
          - sanitized_text: str
        """
        logger.info(f"Checking LLM response safety: '{text[:50]}...'")
        
        sanitized = redact_secrets(text)
        if sanitized != text:
            logger.warning("Redacted sensitive credentials or keys from LLM output response.")
            
        return True, sanitized

output_moderation = OutputModeration()
