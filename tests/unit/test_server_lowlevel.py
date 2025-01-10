import unittest
from unittest.mock import patch
from mcp import types
from mcp_flowise.server_lowlevel import create_prediction_tool, validate_server_env, normalize_tool_name, NAME_TO_ID_MAPPING, mcp


class TestServerLowLevel(unittest.IsolatedAsyncioTestCase):

    @patch("mcp_flowise.server_lowlevel.flowise_predict", return_value="Mock prediction result")
    async def test_create_prediction_tool_valid(self, mock_predict):
        """
        Test dynamic tool creation with a valid chatflow ID and description.
        """
        create_prediction_tool("mock_chatflow_id", "Mock description", "MockTool")
        request = types.CallToolRequest(
            method="tools/call",
            params=types.CallToolRequestParams(name="mocktool", arguments={"question": "What is AI?"}),
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
        create_prediction_tool("mock_chatflow_id", "Mock description", "MockTool")
        request = types.CallToolRequest(
            method="tools/call",
            params=types.CallToolRequestParams(name="mocktool", arguments={}),
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

    def test_tool_name_normalization(self):
        """
        Test normalization of tool names.
        """
        normalized = normalize_tool_name("2024-09-26 Chat Zep-Groq")
        self.assertEqual(normalized, "2024_09_26_chat_zep_groq")

    def test_name_to_id_mapping(self):
        """
        Test the mapping of normalized names to chatflow IDs.
        """
        create_prediction_tool("unique_chatflow_id", "Human-readable description", "2024-09-26 Chat Zep-Groq")
        self.assertIn("2024_09_26_chat_zep_groq", NAME_TO_ID_MAPPING)
        self.assertEqual(NAME_TO_ID_MAPPING["2024_09_26_chat_zep_groq"], "unique_chatflow_id")
