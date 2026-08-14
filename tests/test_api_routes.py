import unittest
from fastapi.testclient import TestClient

from api.server import app

client = TestClient(app)


class TestAPIRoutes(unittest.TestCase):
    def test_root_endpoint(self):
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["service"], "Memorize REST API Service")

    def test_list_memories(self):
        response = client.get("/api/memories")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")

    def test_audit_orphan_endpoints(self):
        files_resp = client.get("/api/audit/orphan-files")
        self.assertEqual(files_resp.status_code, 200)
        self.assertEqual(files_resp.json()["status"], "success")

        indexes_resp = client.get("/api/audit/orphan-indexes")
        self.assertEqual(indexes_resp.status_code, 200)

        chunks_resp = client.get("/api/audit/orphan-chunks")
        self.assertEqual(chunks_resp.status_code, 200)

        summary_resp = client.get("/api/audit/summary")
        self.assertEqual(summary_resp.status_code, 200)

    def test_categories_endpoint(self):
        response = client.get("/api/categories")
        self.assertEqual(response.status_code, 200)
        self.assertIn("categories", response.json())

    def test_settings_endpoints(self):
        get_resp = client.get("/api/settings")
        self.assertEqual(get_resp.status_code, 200)
        self.assertIn("settings", get_resp.json())

        post_resp = client.post("/api/settings", json={"use_llm": True, "embedding_model": "bge-m3"})
        self.assertEqual(post_resp.status_code, 200)
        self.assertEqual(post_resp.json()["settings"]["use_llm"], True)
        self.assertEqual(post_resp.json()["settings"]["embedding_model"], "bge-m3")

        # Reset settings
        reset_resp = client.post("/api/settings/reset")
        self.assertEqual(reset_resp.status_code, 200)


if __name__ == "__main__":
    unittest.main()

