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


if __name__ == "__main__":
    unittest.main()
