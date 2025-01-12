"""
Entry point for the mcp_flowise package.

This script determines which server to run based on the presence of 
the FLOWISE_CHATFLOW_DESCRIPTIONS environment variable:
- Low-Level Server: For dynamic tool creation based on chatflows.
- FastMCP Server: For static tool configurations.
"""

import os
import sys
from mcp_flowise.utils import setup_logging

def main():
    """
    Main entry point for the mcp_flowise package.

    Depending on the FLOWISE_CHATFLOW_DESCRIPTIONS environment variable, 
    this function launches either:
    - Low-Level Server (dynamic tools)
    - FastMCP Server (static tools)
    """
    # Configure logging
    DEBUG = os.getenv("DEBUG", "").lower() in ("true", "1", "yes")
    logger = setup_logging(debug=DEBUG)

    logger.info("Starting mcp_flowise package entry point.")

    # Check the FLOWISE_CHATFLOW_DESCRIPTIONS environment variable
    FLOWISE_CHATFLOW_DESCRIPTIONS = os.getenv("FLOWISE_CHATFLOW_DESCRIPTIONS")
    if FLOWISE_CHATFLOW_DESCRIPTIONS:
        logger.info("FLOWISE_CHATFLOW_DESCRIPTIONS is set. Launching Low-Level Server.")
        from .server_lowlevel import run_server
    else:
        logger.info("FLOWISE_CHATFLOW_DESCRIPTIONS is not set. Launching FastMCP Server.")
        from .server_fastmcp import run_server

    # Run the selected server
    try:
        run_server()
    except Exception as e:
        logger.critical("Unhandled exception occurred while running the server.", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
