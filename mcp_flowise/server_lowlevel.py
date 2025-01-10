'''
Low-Level Server for the Flowise MCP.

This server dynamically registers tools based on the provided chatflows in 
the FLOWISE_CHATFLOW_DESCRIPTIONS environment variable.

Each chatflow is described in the format:
    "chatflow_id1:description1,chatflow_id2:description2,..."
'''

import os
import re
import sys
import logging
import asyncio
from typing import List, Dict
from dotenv import load_dotenv
from mcp import types
from mcp.server.lowlevel import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp_flowise.utils import flowise_predict, redact_api_key

# Global tool mapping
NAME_TO_ID_MAPPING = {}

# Load environment variables
load_dotenv()

# Configure logging
DEBUG = os.getenv("DEBUG", "").lower() in ("true", "1", "yes")
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="[%(levelname)s] %(asctime)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# Initialize the Low-Level MCP Server
mcp = Server("FlowiseMCP-with-EnvAuth")


def parse_chatflow_descriptions() -> List[Dict[str, str]]:
    '''
    Parse and validate the FLOWISE_CHATFLOW_DESCRIPTIONS environment variable.

    Returns:
        A list of dictionaries containing 'id' and 'description' for each chatflow.

    Raises:
        ValueError: If the environment variable is not set or has an invalid format.
    '''
    FLOWISE_CHATFLOW_DESCRIPTIONS = os.getenv("FLOWISE_CHATFLOW_DESCRIPTIONS")
    logger.debug("Retrieved FLOWISE_CHATFLOW_DESCRIPTIONS: %s", FLOWISE_CHATFLOW_DESCRIPTIONS)

    if not FLOWISE_CHATFLOW_DESCRIPTIONS:
        logger.error("FLOWISE_CHATFLOW_DESCRIPTIONS is not set.")
        raise ValueError("FLOWISE_CHATFLOW_DESCRIPTIONS environment variable must be set.")

    chatflows = []
    pairs = FLOWISE_CHATFLOW_DESCRIPTIONS.split(",")

    for pair in pairs:
        if ":" not in pair:
            logger.error("Invalid chatflow format detected: %s", pair)
            raise ValueError(f"Invalid chatflow format: {pair}. Expected 'chatflow_id:description'.")

        chatflow_id, description = pair.split(":", 1)
        chatflow_id = chatflow_id.strip()
        description = description.strip()

        if not chatflow_id or not description:
            logger.error("Empty chatflow_id or description found in pair: %s", pair)
            raise ValueError(f"Empty chatflow_id or description in: {pair}.")

        logger.debug("Parsed chatflow - ID: %s, Description: %s", chatflow_id, description)
        chatflows.append({"id": chatflow_id, "description": description})

    logger.info("Successfully parsed %d chatflows.", len(chatflows))
    return chatflows


def normalize_tool_name(name: str) -> str:
    '''
    Normalize tool names by converting to lowercase and replacing non-alphanumeric characters with underscores.

    Args:
        name (str): Original tool name.

    Returns:
        str: Normalized tool name.
    '''
    return re.sub(r"[^a-zA-Z0-9]", "_", name).lower()


def create_prediction_tool(chatflow_id: str, description: str) -> types.Tool:
    '''
    Create a tool dynamically for a given chatflow.

    Args:
        chatflow_id (str): The unique ID of the chatflow.
        description (str): The human-readable description of the chatflow.

    Returns:
        Tool: A dynamically created Tool object.

    Raises:
        ValueError: If the chatflow_id contains invalid characters.
    '''
    if not re.match(r"^[a-zA-Z0-9_-]+$", chatflow_id):
        raise ValueError(f"Invalid chatflow_id: {chatflow_id}. Only alphanumeric, dashes, and underscores are allowed.")

    normalized_name = normalize_tool_name(description)
    NAME_TO_ID_MAPPING[normalized_name] = chatflow_id

    async def handle_prediction(request: types.CallToolRequest) -> types.ServerResult:
        '''
        Handle prediction requests for this tool.
        '''
        if "question" not in request.params.arguments:
            return types.ServerResult(
                root=types.CallToolResult(
                    content=[types.TextContent(type="text", text='Missing "question" argument')]
                )
            )

        question = request.params.arguments["question"]
        logger.debug(f"Received question: {question} for tool: {normalized_name}")
        result = flowise_predict(chatflow_id, question)
        logger.debug(f"Prediction result for question '{question}': {result}")
        return types.ServerResult(
            root=types.CallToolResult(content=[types.TextContent(type="text", text=result)])
        )

    # Register the handler for this tool
    mcp.request_handlers[types.CallToolRequest] = handle_prediction

    logger.debug(f"Tool created: {normalized_name} for chatflow ID: {chatflow_id}")
    return types.Tool(
        name=normalized_name,
        description=description,
        inputSchema={
            "type": "object",
            "required": ["question"],
            "properties": {"question": {"type": "string"}},
        },
    )


def run_server():
    '''
    Run the Low-Level Flowise server by registering tools dynamically.
    '''
    try:
        chatflows = parse_chatflow_descriptions()
    except ValueError as e:
        logger.critical("Failed to start server: %s", e)
        sys.exit(1)

    tools = []
    for chatflow in chatflows:
        try:
            tool = create_prediction_tool(chatflow["id"], chatflow["description"])
            tools.append(tool)
        except Exception as e:
            logger.error(f"Error while creating tool for chatflow {chatflow['id']}: {e}")

    # Register the tool listing endpoint
    async def list_tools(request: types.ListToolsRequest) -> types.ServerResult:
        logger.debug("Handling list tools request.")
        return types.ServerResult(root=types.ListToolsResult(tools=tools))

    mcp.request_handlers[types.ListToolsRequest] = list_tools

    # Start the server
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
