import os
import subprocess
import time
import json

# Ensure the required environment variable is set
FLOWISE_CHATFLOW_ID = os.getenv("FLOWISE_CHATFLOW_ID")
if not FLOWISE_CHATFLOW_ID:
    print("Error: FLOWISE_CHATFLOW_ID environment variable is not set.")
    exit(1)

# Define requests
initialize_request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "1.0",
        "capabilities": {},
        "clientInfo": {"name": "valid-client", "version": "0.1"}
    }
}

list_tools_request = {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list"
}

call_tool_request = {
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
        "name": FLOWISE_CHATFLOW_ID,  # Use the valid chatflow ID
        "arguments": {"question": "What is AI?"}
    }
}

# Start MCP server
process = subprocess.Popen(
    ["uvx", "--from", ".", "mcp-flowise"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

try:
    # Initialize the server
    print("Sending initialize request...")
    process.stdin.write(json.dumps(initialize_request) + "\n")
    process.stdin.flush()

    # Wait until the server sends a response to the initialize request
    time.sleep(0.5)
    stdout_line = process.stdout.readline()
    while "id" not in stdout_line:  # Look for a response containing "id"
        print(f"Server Response: {stdout_line.strip()}")
        stdout_line = process.stdout.readline()

    print("Initialization complete.")

    # List tools
    print("Sending tools/list request...")
    process.stdin.write(json.dumps(list_tools_request) + "\n")
    process.stdin.flush()
    time.sleep(0.5)

    # Call the valid tool
    print(f"Sending tools/call request for chatflow '{FLOWISE_CHATFLOW_ID}'...")
    process.stdin.write(json.dumps(call_tool_request) + "\n")
    process.stdin.flush()
    time.sleep(1)

    # Capture output
    stdout, stderr = process.communicate(timeout=5)

    # Print responses
    print("STDOUT:")
    print(stdout)

    print("STDERR:")
    print(stderr)

except subprocess.TimeoutExpired:
    print("MCP server process timed out.")
    process.kill()
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    process.terminate()
