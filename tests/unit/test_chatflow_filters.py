import os
import unittest
from unittest.mock import patch
from mcp_flowise.utils import filter_chatflows


class TestChatflowFilters(unittest.TestCase):
    """
    Unit tests for chatflow filtering logic in mcp_flowise.utils.
    """

    def setUp(self):
        """
        Reset the environment variables for filtering logic.
        """
        os.environ.pop("FLOWISE_WHITELIST_ID", None)
        os.environ.pop("FLOWISE_BLACKLIST_ID", None)
        os.environ.pop("FLOWISE_WHITELIST_NAME_REGEX", None)
        os.environ.pop("FLOWISE_BLACKLIST_NAME_REGEX", None)

    def test_no_filters(self):
        """
        Test that all chatflows are returned when no filters are set.
        """
        chatflows = [
            {"id": "chatflow1", "name": "First Chatflow"},
            {"id": "chatflow2", "name": "Second Chatflow"},
        ]
        filtered = filter_chatflows(chatflows)
        self.assertEqual(len(filtered), len(chatflows))
        self.assertListEqual(filtered, chatflows)

    @patch.dict(os.environ, {"FLOWISE_WHITELIST_ID": "chatflow1,chatflow3"})
    def test_whitelist_id_filter(self):
        """
        Test that only whitelisted chatflows by ID are returned.
        """
        chatflows = [
            {"id": "chatflow1", "name": "First Chatflow"},
            {"id": "chatflow2", "name": "Second Chatflow"},
            {"id": "chatflow3", "name": "Third Chatflow"},
        ]
        filtered = filter_chatflows(chatflows)
        self.assertEqual(len(filtered), 2)
        self.assertTrue(all(cf["id"] in {"chatflow1", "chatflow3"} for cf in filtered))

    @patch.dict(os.environ, {"FLOWISE_BLACKLIST_ID": "chatflow2"})
    def test_blacklist_id_filter(self):
        """
        Test that blacklisted chatflows by ID are excluded.
        """
        chatflows = [
            {"id": "chatflow1", "name": "First Chatflow"},
            {"id": "chatflow2", "name": "Second Chatflow"},
        ]
        filtered = filter_chatflows(chatflows)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["id"], "chatflow1")

    @patch.dict(os.environ, {"FLOWISE_WHITELIST_NAME_REGEX": ".*First.*"})
    def test_whitelist_name_regex_filter(self):
        """
        Test that only chatflows matching the whitelist name regex are returned.
        """
        chatflows = [
            {"id": "chatflow1", "name": "First Chatflow"},
            {"id": "chatflow2", "name": "Second Chatflow"},
        ]
        filtered = filter_chatflows(chatflows)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["name"], "First Chatflow")

    @patch.dict(os.environ, {"FLOWISE_BLACKLIST_NAME_REGEX": ".*Second.*"})
    def test_blacklist_name_regex_filter(self):
        """
        Test that chatflows matching the blacklist name regex are excluded.
        """
        chatflows = [
            {"id": "chatflow1", "name": "First Chatflow"},
            {"id": "chatflow2", "name": "Second Chatflow"},
        ]
        filtered = filter_chatflows(chatflows)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["name"], "First Chatflow")

    @patch.dict(
        os.environ,
        {
            "FLOWISE_WHITELIST_ID": "chatflow1",
            "FLOWISE_BLACKLIST_NAME_REGEX": ".*Second.*",
        },
    )
    def test_whitelist_and_blacklist_combined(self):
        """
        Test that whitelist takes precedence over blacklist.
        """
        chatflows = [
            {"id": "chatflow1", "name": "Second Chatflow"},
            {"id": "chatflow2", "name": "Another Chatflow"},
        ]
        filtered = filter_chatflows(chatflows)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["id"], "chatflow1")


if __name__ == "__main__":
    unittest.main()
