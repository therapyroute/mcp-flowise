"""
Unit tests for the low-level server logic in mcp_flowise.
"""

import unittest
from unittest.mock import patch
from mcp_flowise.server_lowlevel import parse_chatflow_descriptions, create_prediction_tool, normalize_tool_name


class TestServerLowLevel(unittest.TestCase):
    """
    Unit tests for server_lowlevel module functions.
    """

    @patch("os.getenv")
    def test_parse_chatflow_descriptions_valid(self, mock_getenv):
        """
        Test parsing of valid FLOWISE_CHATFLOW_DESCRIPTIONS.
        """
        mock_getenv.return_value = (
            "example_id:example_description,another_id:another_description"
        )

        expected = [
            {"id": "example_id", "description": "example_description"},
            {"id": "another_id", "description": "another_description"},
        ]
        result = parse_chatflow_descriptions()
        self.assertEqual(result, expected)

    @patch("os.getenv")
    def test_parse_chatflow_descriptions_invalid(self, mock_getenv):
        """
        Test parsing of invalid FLOWISE_CHATFLOW_DESCRIPTIONS.
        """
        mock_getenv.return_value = "invalid_format"
        with self.assertRaises(ValueError):
            parse_chatflow_descriptions()

    @patch("os.getenv")
    def test_parse_chatflow_descriptions_empty(self, mock_getenv):
        """
        Test parsing when FLOWISE_CHATFLOW_DESCRIPTIONS is not set.
        """
        mock_getenv.return_value = None
        with self.assertRaises(ValueError):
            parse_chatflow_descriptions()

    def test_create_prediction_tool(self):
        """
        Test creation of a prediction tool.
        """
        chatflow_id = "example_id"
        description = "example_description"

        # Call the function
        tool = create_prediction_tool(chatflow_id, description)

        # Assertions
        expected_name = normalize_tool_name(description)
        self.assertEqual(tool.name, expected_name)
        self.assertEqual(tool.description, description)
        self.assertIn("question", tool.inputSchema["properties"])

    def test_create_prediction_tool_invalid_name(self):
        """
        Test creation of a tool with invalid characters in chatflow_id.
        """
        invalid_chatflow_id = "invalid@id!"
        description = "Mock Description"

        with self.assertRaises(ValueError):
            create_prediction_tool(invalid_chatflow_id, description)


if __name__ == "__main__":
    unittest.main()
