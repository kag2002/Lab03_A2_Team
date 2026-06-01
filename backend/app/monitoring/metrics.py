import logging
import time

logger = logging.getLogger("app.monitoring.metrics")

class MetricsCollector:
    def __init__(self):
        self.metrics_store = []

    def record_request_metrics(self, path: str, latency_ms: float, prompt_tokens: int, completion_tokens: int):
        """Mock method to record endpoint metrics, processing times, and token usage."""
        total_tokens = prompt_tokens + completion_tokens
        tokens_per_second = (total_tokens / (latency_ms / 1000.0)) if latency_ms > 0 else 0
        
        metric_entry = {
            "timestamp": time.time(),
            "path": path,
            "latency_ms": latency_ms,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "tokens_per_second": tokens_per_second
        }
        
        self.metrics_store.append(metric_entry)
        logger.info(
            f"[Metric] Path: {path} | Latency: {latency_ms:.2f}ms | "
            f"Tokens: {total_tokens} (Prompt: {prompt_tokens}, Gen: {completion_tokens}) | "
            f"Speed: {tokens_per_second:.2f} tokens/sec"
        )
        
    def get_summary(self) -> dict:
        """Returns mock summaries of recorded requests."""
        if not self.metrics_store:
            return {"total_requests": 0}
            
        total_latency = sum(m["latency_ms"] for m in self.metrics_store)
        total_tokens = sum(m["total_tokens"] for m in self.metrics_store)
        
        return {
            "total_requests": len(self.metrics_store),
            "avg_latency_ms": total_latency / len(self.metrics_store),
            "total_tokens_used": total_tokens,
            "avg_tokens_per_request": total_tokens / len(self.metrics_store)
        }

metrics_collector = MetricsCollector()
