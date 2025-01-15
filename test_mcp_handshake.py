import subprocess
import time
import json

# Define JSON-RPC requests
initialize_request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "1.0",
        "capabilities": {},
        "clientInfo": {"name": "manual-client", "version": "0.1"}
    }
}

initialized_notification = {
    "jsonrpc": "2.0",
    "method": "notifications/initialized"
}

list_tools_request = {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list"
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
    # Send "initialize" request
    process.stdin.write(json.dumps(initialize_request) + "\n")
    process.stdin.flush()
    time.sleep(2.0)

    # Send "initialized" notification
    process.stdin.write(json.dumps(initialized_notification) + "\n")
    process.stdin.flush()
    time.sleep(2.0)

    # Send "tools/list" request
    process.stdin.write(json.dumps(list_tools_request) + "\n")
    process.stdin.flush()
    time.sleep(4)

    # Capture output
    stdout, stderr = process.communicate(timeout=5)

    # Print server responses
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
