"""
Provides the Low-Level server logic for mcp_flowise.

This server dynamically creates tools for each specified chatflow based on
the FLOWISE_CHATFLOW_DESCRIPTIONS environment variable.
"""

import os
import sys
import logging
import asyncio
from dotenv import load_dotenv
from mcp.server.lowlevel import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp import types
from .utils import flowise_predict, redact_api_key

# Load environment variables from .env if present
load_dotenv()

# Initialize logging
DEBUG = os.getenv("DEBUG", "").lower() in ("true", "1", "yes")
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="[%(levelname)s] %(asctime)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# Initialize the Low-Level MCP Server
mcp = Server("FlowiseMCP-with-EnvAuth")


def validate_server_env():
    """
    Validates and retrieves critical environment variables.
    Returns:
        tuple: FLOWISE_CHATFLOW_DESCRIPTIONS, FLOWISE_API_KEY, FLOWISE_API_ENDPOINT
    """
    chatflow_descriptions = os.getenv("FLOWISE_CHATFLOW_DESCRIPTIONS")
    api_key = os.getenv("FLOWISE_API_KEY", "")
    endpoint = os.getenv("FLOWISE_API_ENDPOINT", "http://localhost:3000")

    if not chatflow_descriptions:
        logger.error("No FLOWISE_CHATFLOW_DESCRIPTIONS set; cannot run low-level server. Exiting.")
        sys.exit(1)

    logger.debug(f"Flowise API Key (redacted): {redact_api_key(api_key)}")
    logger.debug(f"Flowise API Endpoint: {endpoint}")
    logger.debug(f"Flowise Chatflow Descriptions: {chatflow_descriptions}")

    return chatflow_descriptions, api_key, endpoint


def create_prediction_tool(chatflow_id: str, description: str):
    """
    Dynamically creates a tool that makes predictions for a specific chatflow_id.
    """
    async def create_prediction_dynamic(request: types.CallToolRequest) -> types.ServerResult:
        question = request.params.arguments.get("question")
        if not question:
            return types.ServerResult(
                types.CallToolResult(
                    content=[types.TextContent(type="text", text='Missing "question" argument')]
                )
            )
        result = flowise_predict(chatflow_id, question)
        return types.ServerResult(
            types.CallToolResult(content=[types.TextContent(type="text", text=result)])
        )

    mcp.request_handlers[types.CallToolRequest] = create_prediction_dynamic

    tool = types.Tool(
        name=f"predict_{chatflow_id.replace('-', '_')}",
        description=description,
        inputSchema={
            "type": "object",
            "required": ["question"],
            "properties": {"question": {"type": "string"}},
        },
    )

    async def list_tools_dynamic(request: types.ListToolsRequest) -> types.ServerResult:
        return types.ServerResult(types.ListToolsResult(tools=[tool]))

    mcp.request_handlers[types.ListToolsRequest] = list_tools_dynamic


def run_server():
    """
    Runs the Low-Level version of the Flowise server.
    """
    chatflow_descriptions, _, _ = validate_server_env()

    try:
        pairs = [pair.strip() for pair in chatflow_descriptions.split(",")]
        for pair in pairs:
            if ":" not in pair:
                raise ValueError(f"Invalid pair format: '{pair}'")
            chatflow_id, description = map(str.strip, pair.split(":", 1))
            create_prediction_tool(chatflow_id, description)
    except Exception as e:
        logger.error(f"Invalid FLOWISE_CHATFLOW_DESCRIPTIONS format: {e}")
        sys.exit(1)

    async def start_server():
        async with stdio_server() as (read_stream, write_stream):
            await mcp.run(
                read_stream,
                write_stream,
                initialization_options=InitializationOptions(
                    server_name="FlowiseMCP-with-EnvAuth",
                    server_version="0.1.0",
                    capabilities=types.ServerCapabilities(),
                ),
            )

    asyncio.run(start_server())


if __name__ == "__main__":
    run_server()
