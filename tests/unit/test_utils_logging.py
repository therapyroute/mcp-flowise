import unittest
from unittest.mock import patch, Mock
from mcp_flowise.utils import redact_api_key, setup_logging
import os
import logging


class TestUtilsLogging(unittest.TestCase):
    """
    Unit tests for logging utilities and API key redaction in utils.py.
    """

    def test_redact_api_key(self):
        """
        Test the redaction of API keys for safe logging.
        """
        self.assertEqual(redact_api_key("1234567890"), "12******90")
        self.assertEqual(redact_api_key("abcd"), "<not set>")  # Too short to redact
        self.assertEqual(redact_api_key("xy"), "<not set>")
        self.assertEqual(redact_api_key(""), "<not set>")
        self.assertEqual(redact_api_key(None), "<not set>")

    @patch("os.makedirs")
    @patch("logging.basicConfig")
    def test_setup_logging_debug(self, mock_basic_config, mock_makedirs):
        """
        Test logging setup with debug mode enabled.
        """
        logger = setup_logging(debug=True, log_dir="test_logs", log_file="test.log")
        self.assertTrue(logger)
        mock_makedirs.assert_called_once_with("test_logs", exist_ok=True)
        mock_basic_config.assert_called_once()
        self.assertEqual(logger.level, logging.DEBUG)

    @patch("os.makedirs")
    @patch("logging.basicConfig")
    def test_setup_logging_info(self, mock_basic_config, mock_makedirs):
        """
        Test logging setup with info mode (default).
        """
        logger = setup_logging(debug=False, log_dir="test_logs", log_file="test.log")
        self.assertTrue(logger)
        mock_makedirs.assert_called_once_with("test_logs", exist_ok=True)
        mock_basic_config.assert_called_once()
        self.assertEqual(logger.level, logging.INFO)

    @patch("os.makedirs", side_effect=PermissionError("No permission to create logs"))
    def test_setup_logging_error(self, mock_makedirs):
        """
        Test logging setup handling when directory creation fails.
        """
        with self.assertLogs(level="ERROR") as log_capture:
            logger = setup_logging(debug=True, log_dir="test_logs", log_file="test.log")
            self.assertTrue(logger)
        self.assertIn("No permission to create logs", log_capture.output[0])


if __name__ == "__main__":
    unittest.main()
