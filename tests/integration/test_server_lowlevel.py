import unittest
from mcp import types
from mcp_flowise.server_lowlevel import create_prediction_tool, mcp

class TestServerLowLevelIntegration(unittest.IsolatedAsyncioTestCase):
    async def test_real_api_call(self):
        """
        Integration test with the real Flowise API.
        """
        create_prediction_tool("mock_chatflow_id", "Mock description")
        request = types.CallToolRequest(
            method="tools/call",
            params=types.CallToolRequestParams(name="predict_mock_chatflow_id", arguments={"question": "What is AI?"}),
        )
        handler = mcp.request_handlers[types.CallToolRequest]
        response = await handler(request)
        self.assertIn("Error:", response.root.content[0].text)  # Adjust for your API's real response.
