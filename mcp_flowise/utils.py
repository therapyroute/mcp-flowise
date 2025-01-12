"""
Utility functions for mcp_flowise, including logging setup and low-level calls to the Flowise API.

This module centralizes shared functionality such as:
1. Logging configuration for consistent log output across the application.
2. Safe redaction of sensitive data like API keys in logs.
3. Low-level interactions with the Flowise API for predictions and chatflow management.
"""

import os
import sys
import logging
import requests
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# Flowise API configuration
FLOWISE_API_KEY = os.getenv("FLOWISE_API_KEY", "")
FLOWISE_API_ENDPOINT = os.getenv("FLOWISE_API_ENDPOINT", "http://localhost:3000")

# Global logger instance
logger = logging.getLogger(__name__)


def setup_logging(debug: bool = False, log_dir: str = "logs", log_file: str = "debug-mcp-flowise.log") -> logging.Logger:
    """
    Sets up logging for the application.

    Args:
        debug (bool): Whether to enable debug-level logging.
        log_dir (str): Directory where the log files will be stored.
        log_file (str): Name of the log file.

    Returns:
        logging.Logger: Configured logger instance.
    """
    # Ensure the logs directory exists
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, log_file)

    # Configure logging to file and console
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="[%(levelname)s] %(asctime)s - %(name)s - %(message)s",
        handlers=[
            logging.FileHandler(log_path, mode="a"),  # Append logs to the file
            logging.StreamHandler(sys.stdout),       # Also output logs to the console
        ],
    )

    logger = logging.getLogger(__name__)
    logger.info("Logging initialized. Writing logs to %s", log_path)
    return logger


def redact_api_key(key: str) -> str:
    """
    Redacts the Flowise API key for safe logging output.

    Args:
        key (str): The API key to redact.

    Returns:
        str: The redacted API key or '<not set>' if the key is invalid.
    """
    if not key or len(key) <= 4:
        return "<not set>"
    return f"{key[:2]}{'*' * (len(key) - 4)}{key[-2:]}"


def flowise_predict(chatflow_id: str, question: str) -> str:
    """
    Sends a question to a specific chatflow ID via the Flowise API and returns the response text.

    Args:
        chatflow_id (str): The ID of the Flowise chatflow to be used.
        question (str): The question or prompt to send to the chatflow.

    Returns:
        str: The response text from the Flowise API or an error string if something went wrong.
    """
    # Construct the Flowise API URL for predictions
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
        # Send POST request to the Flowise API
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        logger.debug(f"Prediction response (HTTP {response.status_code}): {response.text}")
        return response.text
    except requests.exceptions.RequestException as e:
        # Log and return the error as a string
        logger.error(f"Error during prediction: {e}")
        return f"Error: {str(e)}"


def fetch_chatflows() -> list[dict]:
    """
    Fetch a list of all chatflows from the Flowise API.

    Returns:
        list of dict: Each dict contains the 'id' and 'name' of a chatflow.
                      Returns an empty list if there's an error.
    """
    # Construct the Flowise API URL for fetching chatflows
    url = f"{FLOWISE_API_ENDPOINT.rstrip('/')}/api/v1/chatflows"
    headers = {}
    if FLOWISE_API_KEY:
        headers["Authorization"] = f"Bearer {FLOWISE_API_KEY}"

    logger.debug(f"Fetching chatflows from {url}")

    try:
        # Send GET request to the Flowise API
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        # Parse and simplify the response data
        chatflows_data = response.json()
        simplified_chatflows = [{"id": cf["id"], "name": cf["name"]} for cf in chatflows_data]

        logger.debug(f"Simplified Chatflows: {simplified_chatflows}")
        return simplified_chatflows
    except requests.exceptions.RequestException as e:
        # Log and return an empty list on error
        logger.error(f"Error fetching chatflows: {e}")
        return []


# Set up logging during module import to ensure consistent logging throughout the application
DEBUG = os.getenv("DEBUG", "").lower() in ("true", "1", "yes")
setup_logging(debug=DEBUG)

logger.info(f"Flowise API Key (redacted): {redact_api_key(FLOWISE_API_KEY)}")
logger.info(f"Flowise API Endpoint: {FLOWISE_API_ENDPOINT}")
