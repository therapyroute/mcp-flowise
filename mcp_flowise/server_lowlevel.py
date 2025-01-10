"""
Provides the Low-Level server logic for mcp_flowise.

This server dynamically creates tools for each specified chatflow based on
the FLOWISE_CHATFLOW_DESCRIPTIONS environment variable.
"""

import os
import sys
import logging
import json
from dotenv import load_dotenv
from mcp.server.lowlevel import Server
from mcp.server.models import InitializationOptions
from mcp import types
from .utils import flowise_predict

# Load environment variables from .env if present
load_dotenv()

FLOWISE_API_KEY = os.getenv("FLOWISE_API_KEY", "")
FLOWISE_API_ENDPOINT = os.getenv("FLOWISE_API_ENDPOINT", "http://localhost:3000")
FLOWISE_CHATFLOW_DESCRIPTIONS = os.getenv("FLOWISE_CHATFLOW_DESCRIPTIONS")

DEBUG = os.getenv("DEBUG", "").lower() in ("true", "1", "yes")

logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="[%(levelname)s] %(asctime)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

def redact_api_key(key: str) -> str:
    """
    Redacts the Flowise API key for safe logging output.
    """
    if len(key) > 4:
        return f"{key[:2]}{'*' * (len(key) - 4)}{key[-2:]}"
    return "<not set>"

logger.debug(f"Flowise API Key (redacted): {redact_api_key(FLOWISE_API_KEY)}")
logger.debug(f"Flowise API Endpoint: {FLOWISE_API_ENDPOINT}")
logger.debug(f"Flowise Chatflow Descriptions: {FLOWISE_CHATFLOW_DESCRIPTIONS}")

# Initialize the Low-Level MCP Server
mcp = Server("FlowiseMCP-with-EnvAuth")

def create_prediction_tool(chatflow_id: str, description: str) -> None:
    """
    Dynamically create a tool that can make predictions against a specific chatflow_id.
    """
    async def create_prediction_dynamic(request: types.CallToolRequest) -> types.ServerResult:
        logger.debug(
            f"create_prediction_dynamic called with chatflow_id={chatflow_id}, request={request}"
        )
        if 'question' not in request.params.arguments:
            return types.ServerResult(
                types.CallToolResult(
                    content=[types.TextContent(type="text", text='Missing "question" argument')]
                )
            )
        question = request.params.arguments['question']
        result = flowise_predict(chatflow_id, question)
        return types.ServerResult(
            types.CallToolResult(content=[types.TextContent(type="text", text=result)])
        )

    # Register the request handler to handle calls to this dynamic prediction tool.
    mcp.request_handlers[types.CallToolRequest] = create_prediction_dynamic

    # Build a tool definition with a schema for "question".
    tool = types.Tool(
        name=f"predict_{chatflow_id.replace('-', '_')}",
        description=description,
        inputSchema={
            "type": "object",
            "required": ["question"],
            "properties": {
                "question": {"type": "string"},
            },
        }
    )

    # Overwrite the default list_tools to only return our newly created tool(s).
    async def list_tools_dynamic(request: types.ListToolsRequest) -> types.ServerResult:
        return types.ServerResult(types.ListToolsResult(tools=[tool]))

    mcp.request_handlers[types.ListToolsRequest] = list_tools_dynamic

def run_server():
    """
    Run the Low-Level version of the Flowise server, creating dynamic tools
    based on FLOWISE_CHATFLOW_DESCRIPTIONS.
    """
    if not FLOWISE_CHATFLOW_DESCRIPTIONS:
        logger.error("No FLOWISE_CHATFLOW_DESCRIPTIONS set; cannot run low-level server. Exiting.")
        sys.exit(1)

    logger.debug("FLOWISE_CHATFLOW_DESCRIPTIONS is set, creating dynamic tools.")
    try:
        # Attempt to parse multiple chatflow_id:description pairs from CSV-like input
        pairs = [pair.strip() for pair in FLOWISE_CHATFLOW_DESCRIPTIONS.split(",")]
        # Note: Each pair can contain a chatflow_id and a description (split by first colon)
        for p in pairs:
            if ":" not in p:
                raise ValueError(f"Missing colon in pair '{p}'")
            chatflow_id, description = p.split(":", 1)
            create_prediction_tool(chatflow_id.strip(), description.strip().replace("\\\"", "\""))
    except Exception as e:
        logger.error(f"Invalid FLOWISE_CHATFLOW_DESCRIPTIONS format: {e}")
        sys.exit(1)

    try:
        logger.debug("Starting MCP server (Low-Level version)...")
        mcp.run(
            read_stream=None,  # Run on stdio by default
            write_stream=None,
            initialization_options=InitializationOptions(
                server_name="FlowiseMCP-with-EnvAuth",
                server_version="0.1.0",
                capabilities=types.ServerCapabilities(),
            )
        )
    except Exception as e:
        logger.error(f"Unhandled exception in Low-Level MCP server: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    run_server()
