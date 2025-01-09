# flowise_mcp/server.py
import os
import sys
import logging
import requests
import json
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Load environment variables
load_dotenv()

FLOWISE_API_KEY = os.getenv("FLOWISE_API_KEY", "")
FLOWISE_API_ENDPOINT = os.getenv("FLOWISE_API_ENDPOINT", "http://localhost:3002")
FLOWISE_CHATFLOW_ID = os.getenv("FLOWISE_CHATFLOW_ID")
FLOWISE_ASSISTANT_ID = os.getenv("FLOWISE_ASSISTANT_ID")

DEBUG = os.getenv("DEBUG", "").lower() in ("true", "1", "yes")
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="[%(levelname)s] %(asctime)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# Redact API key for logs
def redact_api_key(key: str) -> str:
    return f"{key[:2]}{'*' * (len(key) - 4)}{key[-2:]}" if key else "<not set>"

logger.debug(f"Flowise API Key (redacted): {redact_api_key(FLOWISE_API_KEY)}")
logger.debug(f"Flowise API Endpoint: {FLOWISE_API_ENDPOINT}")
logger.debug(f"Flowise Chatflow ID: {FLOWISE_CHATFLOW_ID}")
logger.debug(f"Flowise Assistant ID: {FLOWISE_ASSISTANT_ID}")

# Initialize MCP Server
mcp = FastMCP("FlowiseMCP-with-EnvAuth", dependencies=["requests"])

# Tool: List Chatflows
@mcp.tool()
def list_chatflows() -> str:
    logger.debug("Handling list_chatflows tool.")
    url = f"{FLOWISE_API_ENDPOINT.rstrip('/')}/api/v1/chatflows"
    headers = {"Authorization": f"Bearer {FLOWISE_API_KEY}"} if FLOWISE_API_KEY else {}
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        chatflows_data = response.json()
        
        # Extract only id and name
        simplified_chatflows = [{"id": cf["id"], "name": cf["name"]} for cf in chatflows_data]
        
        logger.debug(f"Simplified Chatflows: {simplified_chatflows}")
        return json.dumps(simplified_chatflows)
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching chatflows: {e}")
        return f"Error: {str(e)}"

# Tool: Create Prediction
@mcp.tool()
def create_prediction(*, chatflow_id: str = None, question: str) -> str:
    logger.debug(f"create_prediction called with chatflow_id={chatflow_id}, question={question}")
    chatflow_id = chatflow_id or FLOWISE_CHATFLOW_ID
    if not chatflow_id:
        logger.error("No chatflow_id provided or pre-configured.")
        return "Error: chatflow_id is required."
    return flowise_predict(chatflow_id, question)

def flowise_predict(chatflow_id: str, question: str) -> str:
    url = f"{FLOWISE_API_ENDPOINT.rstrip('/')}/api/v1/prediction/{chatflow_id}"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {FLOWISE_API_KEY}"} if FLOWISE_API_KEY else {"Content-Type": "application/json"}
    payload = {"chatflowId": chatflow_id, "question": question, "streaming": False}
    logger.debug(f"Sending prediction request: {url} Payload: {payload}")
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        logger.debug(f"Prediction response: {response.text}")
        return response.text
    except requests.exceptions.RequestException as e:
        logger.error(f"Error during prediction: {e}")
        return f"Error: {str(e)}"

def run_server():
    if FLOWISE_CHATFLOW_ID and FLOWISE_ASSISTANT_ID:
        logger.error("Both FLOWISE_CHATFLOW_ID and FLOWISE_ASSISTANT_ID are set. Set only one.")
        sys.exit(1)

    try:
        logger.info("Starting MCP server...")
        mcp.run(transport="stdio")
    except Exception as e:
        logger.error(f"Unhandled exception in MCP server: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    run_server()
