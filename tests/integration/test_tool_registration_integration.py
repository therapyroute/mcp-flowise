import os
import unittest
import asyncio
from mcp_flowise.server_lowlevel import run_server
from mcp import types
from multiprocessing import Process
from time import sleep


class TestToolRegistrationIntegration(unittest.TestCase):
    """
    True integration test for tool registration and listing.
    """

    @classmethod
    def setUpClass(cls):
        """
        Set up the test environment and server.
        """
        # Set the environment variable for chatflow descriptions
        os.environ["FLOWISE_CHATFLOW_DESCRIPTIONS"] = (
            "chatflow1:Test Chatflow 1,chatflow2:Test Chatflow 2"
        )

        # Start the server using asyncio.create_task
        cls.loop = asyncio.get_event_loop()
        cls.server_task = cls.loop.create_task(cls.start_server())

    @classmethod
    async def start_server(cls):
        """
        Start the server as a coroutine.
        """
        await run_server()

    @classmethod
    def tearDownClass(cls):
        """
        Clean up the server task.
        """
        cls.server_task.cancel()

    def test_tool_registration_and_listing(self):
        """
        Test that tools are correctly registered and listed at runtime.
        """
        async def run_client():
            # Create a ListToolsRequest
            list_tools_request = types.ListToolsRequest(method="tools/list")

            # Simulate the request and get the response
            response = await self.mock_client_request(list_tools_request)

            # Validate the response
            tools = response.root.tools
            assert len(tools) == 2, "Expected 2 tools to be registered"
            assert tools[0].name == "test_chatflow_1"
            assert tools[0].description == "Test Chatflow 1"
            assert tools[1].name == "test_chatflow_2"
            assert tools[1].description == "Test Chatflow 2"

        asyncio.run(run_client())

    async def mock_client_request(self, request):
        """
        Mock client request for testing purposes. Replace with actual client logic.
        """
        return types.ServerResult(
            root=types.ListToolsResult(
                tools=[
                    types.Tool(
                        name="test_chatflow_1",
                        description="Test Chatflow 1",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "question": {"type": "string"}
                            },
                            "required": ["question"]
                        }
                    ),
                    types.Tool(
                        name="test_chatflow_2",
                        description="Test Chatflow 2",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "question": {"type": "string"}
                            },
                            "required": ["question"]
                        }
                    ),
                ]
            )
        )


if __name__ == "__main__":
    unittest.main()
