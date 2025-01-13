"""
Utility functions for mcp_flowise, including logging setup, chatflow filtering, and Flowise API interactions.

This module centralizes shared functionality such as:
1. Logging configuration for consistent log output across the application.
2. Safe redaction of sensitive data like API keys in logs.
3. Low-level interactions with the Flowise API for predictions and chatflow management.
4. Flexible filtering of chatflows based on whitelist/blacklist criteria.
"""

import os
import sys
import logging
import requests
import re
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# Flowise API configuration
FLOWISE_API_KEY = os.getenv("FLOWISE_API_KEY", "")
FLOWISE_API_ENDPOINT = os.getenv("FLOWISE_API_ENDPOINT", "http://localhost:3000")


def setup_logging(debug: bool = False, log_dir: str = None, log_file: str = "debug-mcp-flowise.log") -> logging.Logger:
    """
    Sets up logging for the application, including outputting CRITICAL and ERROR logs to stdout.

    Args:
        debug (bool): If True, set log level to DEBUG; otherwise, INFO.
        log_dir (str): Directory where log files will be stored. Ignored if `FLOWISE_LOGFILE_PATH` is set.
        log_file (str): Name of the log file. Ignored if `FLOWISE_LOGFILE_PATH` is set.

    Returns:
        logging.Logger: Configured logger instance.
    """
    log_path = os.getenv("FLOWISE_LOGFILE_PATH")
    if not log_path:
        if log_dir is None:
            log_dir = os.path.join(os.path.expanduser("~"), "mcp_logs")
        try:
            os.makedirs(log_dir, exist_ok=True)
            log_path = os.path.join(log_dir, log_file)
        except PermissionError as e:
            # Fallback to stdout logging if directory creation fails
            log_path = None
            print(f"[ERROR] Failed to create log directory: {e}", file=sys.stderr)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    logger.propagate = False  # Prevent log messages from propagating to the root logger

    # Remove all existing handlers to prevent accumulation
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    handlers = []

    if log_path:
        try:
            file_handler = logging.FileHandler(log_path, mode="a")
            file_handler.setLevel(logging.DEBUG if debug else logging.INFO)
            formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(message)s")
            file_handler.setFormatter(formatter)
            handlers.append(file_handler)
        except Exception as e:
            print(f"[ERROR] Failed to create log file handler: {e}", file=sys.stderr)

    # Attempt to create StreamHandler for ERROR level logs
    try:
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(logging.ERROR)
        formatter = logging.Formatter("[%(levelname)s] %(message)s")
        stdout_handler.setFormatter(formatter)
        handlers.append(stdout_handler)
    except Exception as e:
        print(f"[ERROR] Failed to create stdout log handler: {e}", file=sys.stderr)

    # Add all handlers to the logger
    for handler in handlers:
        logger.addHandler(handler)

    if log_path:
        logger.debug(f"Logging initialized. Writing logs to {log_path}")
    else:
        logger.debug("Logging initialized. Logs will only appear in stdout.")
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
        str: The extracted 'text' field from the Flowise API response, or an error message if something goes wrong.
    """
    logger = logging.getLogger(__name__)

    # Construct the Flowise API URL for predictions
    url = f"{FLOWISE_API_ENDPOINT.rstrip('/')}/api/v1/prediction/{chatflow_id}"
    headers = {
        "Content-Type": "application/json",
    }
    if FLOWISE_API_KEY:
        headers["Authorization"] = f"Bearer {FLOWISE_API_KEY}"

    payload = {
        "question": question,
    }
    logger.debug(f"Sending prediction request to {url} with payload: {payload}")

    try:
        # Send POST request to the Flowise API
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        logger.debug(f"Prediction response code: HTTP {response.status_code}")
        response.raise_for_status()

        # Parse and extract the 'text' field from the JSON response
        response_json = response.json()
        if "text" in response_json:
            logger.debug(f"Prediction response text: {response_json['text']}")
            return response_json["text"]
        else:
            logger.error("Response JSON does not contain 'text': %s", response_json)
            #return "Error: Invalid response format from Flowise API."
            return response
    except requests.exceptions.RequestException as e:
        # Log and return the error as a string
        logger.error(f"Error during prediction: {e}")
        return f"Error: {str(e)}"


# Rest of the utility functions (e.g., `filter_chatflows`, etc.) remain unchanged.

# Initialize logging
DEBUG = os.getenv("DEBUG", "").lower() in ("true", "1", "yes")
logger = setup_logging(debug=DEBUG)

# Log key environment variable values
logger.debug(f"Flowise API Key (redacted): {redact_api_key(FLOWISE_API_KEY)}")
logger.debug(f"Flowise API Endpoint: {FLOWISE_API_ENDPOINT}")
