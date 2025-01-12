"""
Unit tests for the low-level server logic in mcp_flowise.
"""

import unittest
from unittest.mock import patch, MagicMock
from mcp_flowise.server_lowlevel import  run_server, dispatcher_handler
from mcp_flowise.utils import normalize_tool_name, fetch_chatflows
from mcp import types
import asyncio


class TestServerLowLevel(unittest.TestCase):
    """
    Unit tests for server_lowlevel module functions.
    """

    @patch("mcp_flowise.utils.fetch_chatflows")
    @patch("mcp_flowise.server_lowlevel.mcp")
    def test_run_server_with_no_chatflows(self, mock_mcp, mock_fetch_chatflows):
        """
        Test server behavior when no chatflows are fetched.
        """
        mock_fetch_chatflows.return_value = []  # Simulate no chatflows returned
        with self.assertRaises(SystemExit):  # The server should exit
            run_server()

    @patch("mcp_flowise.server_lowlevel.NAME_TO_ID_MAPPING", {"tool_1": "id1"})
    @patch("mcp_flowise.server_lowlevel.flowise_predict")
    def test_dispatcher_handler_valid_request(self, mock_flowise_predict):
        """
        Test dispatcher handler with a valid tool request.
        """
        mock_flowise_predict.return_value = "Prediction result"

        request = MagicMock()
        request.params.name = "tool_1"
        request.params.arguments = {"question": "What is Flowise?"}

        result = asyncio.run(dispatcher_handler(request))
        self.assertEqual(result.root.content[0].text, "Prediction result")

    @patch("mcp_flowise.server_lowlevel.NAME_TO_ID_MAPPING", {})
    def test_dispatcher_handler_invalid_tool(self):
        """
        Test dispatcher handler with an invalid tool name.
        """
        request = MagicMock()
        request.params.name = "unknown_tool"
        request.params.arguments = {"question": "What is Flowise?"}

        result = asyncio.run(dispatcher_handler(request))
        self.assertIn("Unknown tool requested", result.root.content[0].text)

    @patch("mcp_flowise.server_lowlevel.NAME_TO_ID_MAPPING", {"tool_1": "id1"})
    def test_dispatcher_handler_missing_question(self):
        """
        Test dispatcher handler with a missing 'question' argument.
        """
        request = MagicMock()
        request.params.name = "tool_1"
        request.params.arguments = {}  # Missing 'question'

        result = asyncio.run(dispatcher_handler(request))
        self.assertIn("Missing \"question\" argument", result.root.content[0].text)


if __name__ == "__main__":
    unittest.main()
