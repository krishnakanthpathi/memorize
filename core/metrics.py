import time
import threading
from typing import Any, Dict, List, Optional
from contextlib import contextmanager


class MetricsCollector:
    """
    Thread-safe collector for query latency, graph node execution metrics,
    token usage, and search hit rates.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(MetricsCollector, cls).__new__(cls)
                cls._instance._init_metrics()
            return cls._instance

    def _init_metrics(self):
        self.metrics_lock = threading.Lock()
        self.reset()

    def reset(self):
        with self.metrics_lock:
            self.total_queries: int = 0
            self.successful_queries: int = 0
            self.failed_queries: int = 0
            self.total_tokens_prompt: int = 0
            self.total_tokens_completion: int = 0
            self.node_execution_times: Dict[str, List[float]] = {}
            self.query_latencies_ms: List[float] = []
            self.retrieval_hits: int = 0
            self.offline_mode_executions: int = 0

    def record_query(self, latency_ms: float, success: bool = True, offline: bool = False):
        with self.metrics_lock:
            self.total_queries += 1
            if success:
                self.successful_queries += 1
            else:
                self.failed_queries += 1
            if offline:
                self.offline_mode_executions += 1
            self.query_latencies_ms.append(latency_ms)

    def record_node_timing(self, node_name: str, duration_ms: float):
        with self.metrics_lock:
            if node_name not in self.node_execution_times:
                self.node_execution_times[node_name] = []
            self.node_execution_times[node_name].append(duration_ms)

    def record_tokens(self, prompt_tokens: int = 0, completion_tokens: int = 0):
        with self.metrics_lock:
            self.total_tokens_prompt += prompt_tokens
            self.total_tokens_completion += completion_tokens

    def record_retrieval_hit(self, count: int = 1):
        with self.metrics_lock:
            self.retrieval_hits += count

    @contextmanager
    def time_node(self, node_name: str):
        """Context manager to time a specific graph node execution."""
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            self.record_node_timing(node_name, elapsed_ms)

    def get_summary(self) -> Dict[str, Any]:
        with self.metrics_lock:
            avg_latency = (
                round(sum(self.query_latencies_ms) / len(self.query_latencies_ms), 2)
                if self.query_latencies_ms
                else 0.0
            )

            node_averages = {}
            for node_name, times in self.node_execution_times.items():
                node_averages[node_name] = {
                    "count": len(times),
                    "avg_ms": round(sum(times) / len(times), 2) if times else 0.0,
                    "max_ms": round(max(times), 2) if times else 0.0,
                }

            return {
                "total_queries": self.total_queries,
                "successful_queries": self.successful_queries,
                "failed_queries": self.failed_queries,
                "offline_mode_executions": self.offline_mode_executions,
                "avg_query_latency_ms": avg_latency,
                "total_tokens_prompt": self.total_tokens_prompt,
                "total_tokens_completion": self.total_tokens_completion,
                "total_tokens": self.total_tokens_prompt + self.total_tokens_completion,
                "retrieval_hits": self.retrieval_hits,
                "nodes": node_averages,
            }


metrics_collector = MetricsCollector()
