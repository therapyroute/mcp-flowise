"""
Utility functions for mcp_flowise, including the low-level calls to the Flowise API.
"""

import logging
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

FLOWISE_API_KEY = os.getenv("FLOWISE_API_KEY", "")
FLOWISE_API_ENDPOINT = os.getenv("FLOWISE_API_ENDPOINT", "http://localhost:3000")

logger = logging.getLogger(__name__)

def redact_api_key(key: str) -> str:
    """
    Redacts the Flowise API key for safe logging output.

    Args:
        key (str): The API key to redact.

    Returns:
        str: The redacted API key.
    """
    if len(key) > 4:
        return f"{key[:2]}{'*' * (len(key) - 4)}{key[-2:]}"
    return "<not set>"

logger.debug(f"Flowise API Key (redacted): {redact_api_key(FLOWISE_API_KEY)}")
logger.debug(f"Flowise API Endpoint: {FLOWISE_API_ENDPOINT}")

def flowise_predict(chatflow_id: str, question: str) -> str:
    """
    Sends a question to a specific chatflow ID via the Flowise API and returns the response text.

    Args:
        chatflow_id (str): The ID of the Flowise chatflow to be used.
        question (str): The question or prompt to send to the chatflow.

    Returns:
        str: The response text from the Flowise API or an error string if something went wrong.
    """
    url = f"{FLOWISE_API_ENDPOINT.rstrip('/')}/api/v1/prediction/{chatflow_id}"
    headers = {
        "Content-Type": "application/json",
    }
    if FLOWISE_API_KEY:
        headers["Authorization"] = f"Bearer {FLOWISE_API_KEY}"

    payload = {
        "chatflowId": chatflow_id,
        "question": question,
        "streaming": False
    }
    logger.debug(f"Sending prediction request to {url} with payload: {payload}")

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        logger.debug(f"Prediction response (HTTP {response.status_code}): {response.text}")
        return response.text
    except requests.exceptions.RequestException as e:
        logger.error(f"Error during prediction: {e}")
        return f"Error: {str(e)}"

def fetch_chatflows() -> list[dict]:
    """
    Fetch a list of all chatflows from the Flowise API.

    Returns:
        list of dict: Each dict contains the 'id' and 'name' of a chatflow.
                      Returns an empty list if there's an error.
    """
    url = f"{FLOWISE_API_ENDPOINT.rstrip('/')}/api/v1/chatflows"
    headers = {}
    if FLOWISE_API_KEY:
        headers["Authorization"] = f"Bearer {FLOWISE_API_KEY}"

    logger.debug(f"Fetching chatflows from {url}")

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        chatflows_data = response.json()
        # Extract only id and name to keep it simple and safe
        simplified_chatflows = [{"id": cf["id"], "name": cf["name"]} for cf in chatflows_data]

        logger.debug(f"Simplified Chatflows: {simplified_chatflows}")
        return simplified_chatflows
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching chatflows: {e}")
        return []
