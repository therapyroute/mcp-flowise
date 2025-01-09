"""
Provides the FastMCP server logic for mcp_flowise.

This server exposes a limited set of tools (list_chatflows, create_prediction)
and uses environment variables to determine the chatflow or assistant configuration.
"""

import os
import sys
import logging
import json
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from .utils import flowise_predict, fetch_chatflows

# Load environment variables from .env if present
load_dotenv()

FLOWISE_API_KEY = os.getenv("FLOWISE_API_KEY", "")
FLOWISE_API_ENDPOINT = os.getenv("FLOWISE_API_ENDPOINT", "http://localhost:3000")
FLOWISE_CHATFLOW_ID = os.getenv("FLOWISE_CHATFLOW_ID")
FLOWISE_ASSISTANT_ID = os.getenv("FLOWISE_ASSISTANT_ID")
FLOWISE_CHATFLOW_DESCRIPTION = os.getenv("FLOWISE_CHATFLOW_DESCRIPTION")
FLOWISE_CHATFLOW_WHITELIST = os.getenv("FLOWISE_CHATFLOW_WHITELIST")
FLOWISE_CHATFLOW_BLACKLIST = os.getenv("FLOWISE_CHATFLOW_BLACKLIST")

DEBUG = os.getenv("DEBUG", "").lower() in ("true", "1", "yes")

logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="[%(levelname)s] %(asctime)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

def redact_api_key(key: str) -> str:
    """
    Redacts the Flowise API key so it can be safely displayed in debug logs.
    """
    if len(key) > 4:
        return f"{key[:2]}{'*' * (len(key) - 4)}{key[-2:]}"
    return "<not set>"

logger.debug(f"Flowise API Key (redacted): {redact_api_key(FLOWISE_API_KEY)}")
logger.debug(f"Flowise API Endpoint: {FLOWISE_API_ENDPOINT}")
logger.debug(f"Flowise Chatflow ID: {FLOWISE_CHATFLOW_ID}")
logger.debug(f"Flowise Assistant ID: {FLOWISE_ASSISTANT_ID}")
logger.debug(f"Flowise Chatflow Description: {FLOWISE_CHATFLOW_DESCRIPTION}")

# Initialize MCP Server
mcp = FastMCP("FlowiseMCP-with-EnvAuth", dependencies=["requests"])

@mcp.tool()
def list_chatflows() -> str:
    """
    List all available chatflows from the Flowise API.

    Respects optional whitelisting or blacklisting if configured.
    """
    logger.debug("Handling list_chatflows tool.")
    chatflows = fetch_chatflows()
    # Apply whitelisting
    if FLOWISE_CHATFLOW_WHITELIST:
        whitelist = set(FLOWISE_CHATFLOW_WHITELIST.split(","))
        chatflows = [cf for cf in chatflows if cf["id"] in whitelist]
    # Apply blacklisting
    if FLOWISE_CHATFLOW_BLACKLIST:
        blacklist = set(FLOWISE_CHATFLOW_BLACKLIST.split(","))
        chatflows = [cf for cf in chatflows if cf["id"] not in blacklist]

    return json.dumps(chatflows)

@mcp.tool()
def create_prediction(*, chatflow_id: str = None, question: str) -> str:
    """
    Create a prediction by sending a question to either a specific chatflow_id
    or the default from the environment variables (FLOWISE_CHATFLOW_ID or FLOWISE_ASSISTANT_ID).
    """
    logger.debug(f"create_prediction called with chatflow_id={chatflow_id}, question={question}")
    chatflow_id = chatflow_id or FLOWISE_CHATFLOW_ID
    if not chatflow_id and not FLOWISE_ASSISTANT_ID:
        logger.error("No chatflow_id or assistant_id provided or pre-configured.")
        return "Error: chatflow_id or assistant_id is required."

    if chatflow_id:
        # If a chatflow ID is provided, optionally attach a special description to the tool.
        if FLOWISE_CHATFLOW_DESCRIPTION:
            logger.debug(f"Using description for chatflow {chatflow_id}: {FLOWISE_CHATFLOW_DESCRIPTION}")

            # Nested tool to apply a custom description if needed
            @mcp.tool(description=FLOWISE_CHATFLOW_DESCRIPTION)
            def create_prediction_with_description(*, question: str) -> str:
                logger.debug(f"create_prediction_with_description called with chatflow_id={chatflow_id}, question={question}")
                return flowise_predict(chatflow_id, question)

            return create_prediction_with_description(question=question)
        else:
            logger.debug(f"No custom description set for chatflow {chatflow_id}.")
            return flowise_predict(chatflow_id, question)
    else:
        # If there's an assistant ID
        return flowise_predict(FLOWISE_ASSISTANT_ID, question)

def run_server():
    """
    Run the FastMCP version of the Flowise server. 
    Exits with an error if both FLOWISE_CHATFLOW_ID and FLOWISE_ASSISTANT_ID are set.
    """
    if FLOWISE_CHATFLOW_ID and FLOWISE_ASSISTANT_ID:
        logger.error("Both FLOWISE_CHATFLOW_ID and FLOWISE_ASSISTANT_ID are set. Set only one.")
        sys.exit(1)

    try:
        logger.info("Starting MCP server (FastMCP version)...")
        mcp.run(transport="stdio")
    except Exception as e:
        logger.error(f"Unhandled exception in MCP server: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    run_server()
