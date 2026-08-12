import unittest

from graph.workflow import MemorizeGraphRAGAgent
from storage.db_manager import init_db


class TestGraphWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def test_graph_agent_execution(self):
        agent = MemorizeGraphRAGAgent()
        res = agent.run("What are my technical skills?")

        self.assertEqual(res["status"], "success")
        self.assertIn("reply", res)
        self.assertIn("intent", res)
        self.assertIn("latency_ms", res)

    def test_graph_agent_memory_store(self):
        agent = MemorizeGraphRAGAgent()
        res = agent.run("Please store memory that I love coding in Python and LangGraph")

        self.assertEqual(res["status"], "success")
        self.assertEqual(res["intent"], "store")
        self.assertIn("reply", res)


if __name__ == "__main__":
    unittest.main()
