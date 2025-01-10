import unittest
from unittest.mock import patch
from mcp import types
from mcp_flowise.server_lowlevel import create_prediction_tool, validate_server_env, mcp


class TestServerLowLevel(unittest.IsolatedAsyncioTestCase):

    @patch("mcp_flowise.server_lowlevel.flowise_predict", return_value="Mock prediction result")
    async def test_create_prediction_tool_valid(self, mock_predict):
        """
        Test dynamic tool creation with a valid chatflow ID and description.
        """
        create_prediction_tool("mock_chatflow_id", "Mock description")
        request = types.CallToolRequest(
            method="tools/call",
            params=types.CallToolRequestParams(name="predict_mock_chatflow_id", arguments={"question": "What is AI?"}),
        )
        handler = mcp.request_handlers[types.CallToolRequest]
        response = await handler(request)

        # Ensure the mocked flowise_predict was called
        mock_predict.assert_called_once_with("mock_chatflow_id", "What is AI?")
        self.assertIn("Mock prediction result", response.root.content[0].text)

    async def test_create_prediction_tool_missing_question(self):
        """
        Test error handling when 'question' is missing in request.
        """
        create_prediction_tool("mock_chatflow_id", "Mock description")
        request = types.CallToolRequest(
            method="tools/call",
            params=types.CallToolRequestParams(name="predict_mock_chatflow_id", arguments={}),
        )
        handler = mcp.request_handlers[types.CallToolRequest]
        response = await handler(request)
        self.assertIn('Missing "question" argument', response.root.content[0].text)

    @patch("os.getenv", side_effect=lambda key, default=None: {"FLOWISE_CHATFLOW_DESCRIPTIONS": "mock_chatflow_id:Mock description"}.get(key, default))
    def test_validate_server_env(self, mock_getenv):
        """
        Test environment variable validation logic.
        """
        descriptions, api_key, endpoint = validate_server_env()
        self.assertEqual(descriptions, "mock_chatflow_id:Mock description")
        self.assertEqual(api_key, "")
        self.assertEqual(endpoint, "http://localhost:3000")
