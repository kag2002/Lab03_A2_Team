import logging

logger = logging.getLogger("app.services.token_service")

try:
    import tiktoken
    _encoding = tiktoken.get_encoding("cl100k_base")
    HAS_TIKTOKEN = True
except ImportError:
    logger.warning("tiktoken library not found. Falling back to rough estimation.")
    HAS_TIKTOKEN = False

def count_string_tokens(text: str) -> int:
    """Counts the number of tokens in a string using tiktoken, or falls back to standard char-length estimation."""
    if not text:
        return 0
    if HAS_TIKTOKEN:
        try:
            return len(_encoding.encode(text))
        except Exception as e:
            logger.error(f"Error encoding text with tiktoken: {e}")
    # Fallback estimate: ~4 characters per token
    return max(1, len(text) // 4)

def count_messages_tokens(messages: list) -> int:
    """Roughly counts tokens in a list of chat messages."""
    num_tokens = 0
    for message in messages:
        # Standard OpenAI formatting adds ~4 tokens of overhead per message
        num_tokens += 4
        # Add message fields
        content = message.content if hasattr(message, "content") else message.get("content", "")
        role = message.role if hasattr(message, "role") else message.get("role", "")
        num_tokens += count_string_tokens(content)
        num_tokens += count_string_tokens(role)
    # Overhead for the assistant reply initiation
    num_tokens += 2
    return num_tokens
