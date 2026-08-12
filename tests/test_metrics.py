import unittest
from core.metrics import MetricsCollector


class TestMetricsCollector(unittest.TestCase):
    def setUp(self):
        self.collector = MetricsCollector()
        self.collector.reset()

    def test_record_query_and_nodes(self):
        self.collector.record_query(latency_ms=120.5, success=True, offline=True)
        self.collector.record_node_timing("retriever", 45.2)
        self.collector.record_tokens(prompt_tokens=100, completion_tokens=50)

        summary = self.collector.get_summary()
        self.assertEqual(summary["total_queries"], 1)
        self.assertEqual(summary["successful_queries"], 1)
        self.assertEqual(summary["offline_mode_executions"], 1)
        self.assertEqual(summary["avg_query_latency_ms"], 120.5)
        self.assertEqual(summary["total_tokens"], 150)
        self.assertIn("retriever", summary["nodes"])


if __name__ == "__main__":
    unittest.main()
