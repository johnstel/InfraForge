import asyncio
import unittest

import httpx

from src.web import app


class WebHealthEndpointTest(unittest.TestCase):
    def test_health_endpoint_returns_sql_check_response(self):
        async def request_health():
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                return await client.get("/api/health?check=sql")

        response = asyncio.run(request_health())

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["check"], "sql")
        self.assertEqual(payload["result"]["status"], "unhealthy")
        self.assertIn("AZURE_SQL_CONNECTION_STRING", payload["result"]["message"])


if __name__ == "__main__":
    unittest.main()
