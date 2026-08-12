import unittest

from engine.llm_factory import LLMFactory, OfflineFallbackLLM
from langchain_core.messages import HumanMessage


class TestLLMFactory(unittest.TestCase):
    def test_llm_factory_fallback(self):
        llm = LLMFactory.get_llm(provider="none")
        self.assertIsInstance(llm, OfflineFallbackLLM)

        res = llm.invoke([HumanMessage(content="Hello")])
        self.assertIn("Zero-LLM Offline Mode", res.content)


if __name__ == "__main__":
    unittest.main()
