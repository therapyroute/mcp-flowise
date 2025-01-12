'''
Low-Level Server for the Flowise MCP.

This server dynamically registers tools based on the provided chatflows
retrieved from the Flowise API. Tool names are normalized for safety 
and consistency, and potential conflicts are logged.

Descriptions for tools are prioritized from FLOWISE_CHATFLOW_DESCRIPTIONS,
falling back to the chatflow names when not provided.

Conflicts in tool names after normalization are handled gracefully by
skipping those chatflows.
'''

import os
import re
import sys
import asyncio
from typing import List, Dict
from dotenv import load_dotenv
from mcp import types
from mcp.server.lowlevel import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp_flowise.utils import (
    flowise_predict,
    fetch_chatflows,
    normalize_tool_name,
    setup_logging,
)

# Load environment variables from .env if present
load_dotenv()

# Configure logging
DEBUG = os.getenv("DEBUG", "").lower() in ("true", "1", "yes")
logger = setup_logging(debug=DEBUG)

# Global tool mapping: tool name to chatflow ID
NAME_TO_ID_MAPPING = {}

# Initialize the Low-Level MCP Server
mcp = Server("FlowiseMCP-with-EnvAuth")


def get_chatflow_descriptions() -> Dict[str, str]:
    """
    Parse the FLOWISE_CHATFLOW_DESCRIPTIONS environment variable for descriptions.

    Returns:
        dict: A dictionary mapping chatflow IDs to descriptions.
    """
    descriptions_env = os.getenv("FLOWISE_CHATFLOW_DESCRIPTIONS", "")
    logger.debug("Retrieved FLOWISE_CHATFLOW_DESCRIPTIONS: %s", descriptions_env)

    descriptions = {}
    for pair in descriptions_env.split(","):
        if ":" not in pair:
            logger.warning("Invalid format in FLOWISE_CHATFLOW_DESCRIPTIONS: %s", pair)
            continue
        chatflow_id, description = map(str.strip, pair.split(":", 1))
        if chatflow_id and description:
            descriptions[chatflow_id] = description
    logger.debug("Parsed FLOWISE_CHATFLOW_DESCRIPTIONS: %s", descriptions)
    return descriptions


async def dispatcher_handler(request: types.CallToolRequest) -> types.ServerResult:
    '''
    Dispatcher handler that routes CallToolRequest to the appropriate tool handler based on the tool name.

    Args:
        request (types.CallToolRequest): The incoming tool call request.

    Returns:
        types.ServerResult: The result of the tool execution.
    '''
    try:
        # Extract tool name from request.params.name
        tool_name = request.params.name
        logger.debug("Dispatcher received CallToolRequest for tool: %s", tool_name)

        # Check if the tool name exists in the registered tools
        if tool_name not in NAME_TO_ID_MAPPING:
            logger.error("Unknown tool requested: %s", tool_name)
            return types.ServerResult(
                root=types.CallToolResult(
                    content=[types.TextContent(type="text", text="Unknown tool requested")]
                )
            )

        # Map the tool name to its associated chatflow ID
        chatflow_id = NAME_TO_ID_MAPPING[tool_name]
        question = request.params.arguments.get("question")

        # Validate the question argument
        if not question:
            logger.error("Missing 'question' argument in request for tool: %s", tool_name)
            return types.ServerResult(
                root=types.CallToolResult(
                    content=[types.TextContent(type="text", text='Missing "question" argument')]
                )
            )

        logger.debug("Dispatching prediction for chatflow_id: %s with question: %s", chatflow_id, question)

        # Call the prediction function
        result = flowise_predict(chatflow_id, question)
        logger.debug("Received prediction result: %s", result)

        return types.ServerResult(
            root=types.CallToolResult(
                content=[types.TextContent(type="text", text=result)]
            )
        )
    except Exception as e:
        # Log the error and dump the raw request for debugging
        logger.error("Unhandled exception in dispatcher_handler: %s", e, exc_info=True)

        try:
            # Attempt to log the raw request
            import json
            raw_request = json.dumps(request.model_dump(), indent=2) if hasattr(request, 'model_dump') else str(request)
            logger.error("Raw request causing the error: %s", raw_request)
        except Exception as log_error:
            logger.error("Failed to serialize the raw request: %s", log_error)

        # Return a generic error response
        return types.ServerResult(
            root=types.CallToolResult(
                content=[types.TextContent(type="text", text="An internal server error occurred. Please check logs.")]
            )
        )


def run_server():
    '''
    Run the Low-Level Flowise server by registering tools dynamically.
    '''
    try:
        # Fetch chatflows dynamically from the Flowise API
        chatflows = fetch_chatflows()
        if not chatflows:
            raise ValueError("No chatflows retrieved from the Flowise API.")
    except Exception as e:
        logger.critical("Failed to start server: %s", e)
        sys.exit(1)

    # Get descriptions from environment variable
    chatflow_descriptions = get_chatflow_descriptions()

    tools = []
    for chatflow in chatflows:
        try:
            # Normalize the tool name to ensure it's safe for use
            normalized_name = normalize_tool_name(chatflow["name"])

            if normalized_name in NAME_TO_ID_MAPPING:
                logger.warning(
                    "Tool name conflict: '%s' already exists. Skipping chatflow '%s' (ID: '%s').",
                    normalized_name,
                    chatflow["name"],
                    chatflow["id"],
                )
                continue

            # Register the normalized name and chatflow ID
            NAME_TO_ID_MAPPING[normalized_name] = chatflow["id"]

            # Use the description from the environment variable, fallback to the chatflow name
            description = chatflow_descriptions.get(chatflow["id"], chatflow["name"])

            # Create the tool using the normalized name and description
            tool = types.Tool(
                name=normalized_name,
                description=description,
                inputSchema={
                    "type": "object",
                    "required": ["question"],
                    "properties": {"question": {"type": "string"}},
                },
            )
            tools.append(tool)
            logger.info("Registered tool: %s (ID: %s)", tool.name, chatflow["id"])

        except Exception as e:
            logger.error("Error registering chatflow '%s' (ID: '%s'): %s", chatflow["name"], chatflow["id"], e)

    if not tools:
        logger.critical("No valid tools registered. Shutting down the server.")
        sys.exit(1)

    # Register the dispatcher handler for handling tool requests
    mcp.request_handlers[types.CallToolRequest] = dispatcher_handler
    logger.debug("Registered dispatcher_handler for CallToolRequest.")

    # Register the tool listing endpoint
    async def list_tools(request: types.ListToolsRequest) -> types.ServerResult:
        logger.debug("Handling list_tools request.")
        return types.ServerResult(root=types.ListToolsResult(tools=tools))

    mcp.request_handlers[types.ListToolsRequest] = list_tools
    logger.debug("Registered list_tools handler.")

    # Start the server
    async def start_server():
        logger.info("Starting Low-Level MCP server...")
        try:
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
        except Exception as e:
            logger.critical("Unhandled exception in MCP server: %s", e)
            sys.exit(1)

    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        logger.info("MCP server shutdown initiated by user.")
    except Exception as e:
        logger.critical("Failed to start MCP server: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    run_server()
