"""
Unit tests for the low-level server logic in mcp_flowise.
"""

import unittest
from unittest.mock import patch
from mcp_flowise.server_lowlevel import validate_server_env, create_prediction_tool


class TestServerLowLevelAdditional(unittest.TestCase):
    """
    Additional tests for server low-level logic.
    """

    # @patch("os.getenv")
    # def test_validate_env_invalid_description_format(self, mock_getenv):
    #     """
    #     Test server environment validation with invalid FLOWISE_CHATFLOW_DESCRIPTIONS format.
    #     """
    #     mock_getenv.side_effect = lambda key, default=None: "invalid_format" if key == "FLOWISE_CHATFLOW_DESCRIPTIONS" else default
    #     with self.assertRaises(SystemExit):
    #         validate_server_env()

    @patch("os.getenv")
    def test_validate_env_missing_description(self, mock_getenv):
        """
        Test server environment validation with missing FLOWISE_CHATFLOW_DESCRIPTIONS.
        """
        mock_getenv.side_effect = lambda key, default=None: None if key == "FLOWISE_CHATFLOW_DESCRIPTIONS" else default
        with self.assertRaises(SystemExit):
            validate_server_env()

    def test_create_tool_invalid_name(self):
        """
        Test dynamic tool creation with invalid tool name (non-alphanumeric characters).
        """
        invalid_name = "Invalid@Name!"
        with self.assertRaises(ValueError) as context:
            create_prediction_tool("mock_chatflow_id", "Mock description", invalid_name)
        self.assertIn("Invalid tool name", str(context.exception))

    def test_create_tool_valid_name(self):
        """
        Test dynamic tool creation with a valid name.
        """
        valid_name = "valid_tool_name"
        try:
            create_prediction_tool("mock_chatflow_id", "Mock description", valid_name)
        except Exception as e:
            self.fail(f"create_prediction_tool raised an unexpected exception: {e}")
