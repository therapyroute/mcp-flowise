"""
Entry point for the mcp_flowise package.

Depending on the presence of FLOWISE_CHATFLOW_DESCRIPTIONS, this module
decides whether to run the Low-Level server (dynamic tool creation) or
the FastMCP server (no dynamic tools).
"""

import os
import sys
import logging

def main():
    """
    Main entrypoint for the mcp_flowise package. Depending on the
    FLOWISE_CHATFLOW_DESCRIPTIONS environment variable, launches
    the appropriate server.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(asctime)s - %(message)s",
        stream=sys.stdout,
    )
    logger = logging.getLogger(__name__)

    FLOWISE_CHATFLOW_DESCRIPTIONS = os.getenv("FLOWISE_CHATFLOW_DESCRIPTIONS")
    if FLOWISE_CHATFLOW_DESCRIPTIONS:
        logger.info("FLOWISE_CHATFLOW_DESCRIPTIONS is set, running Low-Level server.")
        from .server_lowlevel import run_server
        run_server()
    else:
        logger.info("FLOWISE_CHATFLOW_DESCRIPTIONS is NOT set, running FastMCP server.")
        from .server_fastmcp import run_server
        run_server()

if __name__ == "__main__":
    main()
