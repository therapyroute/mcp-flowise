# mcp-flowise

`mcp-flowise` is a Python package that implements a Model Context Protocol (MCP) server integrating with the Flowise API. It provides a streamlined way to create predictions, list chatflows, and manage assistants in a standardized and flexible manner. It supports two operation modes:

- **FastMCP Mode**: Exposes `list_chatflows` and `create_prediction` tools with minimal configuration.
- **LowLevel Mode**: Dynamically creates tools for each chatflow or assistant, requiring descriptions for each.

## Features

- **Authentication**: Interact securely with the Flowise API using Bearer tokens.
- **Dynamic Tool Exposure**: Exposes tools based on configuration, either as generalized tools (FastMCP) or dynamically created tools (LowLevel).
- **Flexible Deployment**: Can be run directly or integrated into larger MCP workflows using `uvx`.
- **Environment Configuration**: Manage sensitive configurations through environment variables (e.g., `.env` files).

## Installation

### Prerequisites

- Python 3.12 or higher
- `pip` package manager

## Running the Server

### Using `uvx` from GitHub

The easiest way to run the server is via `uvx`, which installs and executes the package directly from the GitHub repository:

```bash
uvx --from git+https://github.com/matthewhand/mcp-flowise mcp-flowise
```

### Adding to MCP Ecosystem (`mcpServers` Configuration)

You can integrate `mcp-flowise` into your MCP ecosystem by adding it to the `mcpServers` configuration. Example:

```json
{
    "mcpServers": {
        "mcp-flowise": {
            "command": "uvx",
            "args": [
                "--from",
                "git+https://github.com/matthewhand/mcp-flowise",
                "mcp-flowise"
            ],
            "env": {
                "FLOWISE_API_KEY": "${FLOWISE_API_KEY}",
                "FLOWISE_API_ENDPOINT": "${FLOWISE_API_ENDPOINT}"
            }
        }
    }
}
```

## Running on Windows with `uvx`

If you're using `uvx` on Windows and encounter issues with `--from git+https`, the recommended solution is to clone the repository locally and configure the `mcpServers` with the full path to `uvx.exe` and the cloned repository. Additionally, include `APPDATA`, `LOGLEVEL`, and other environment variables as required.

### Example Configuration for MCP Ecosystem (`mcpServers` on Windows)

```json
{
  "mcpServers": {
    "flowise": {
      "command": "C:\\Users\\matth\\.local\\bin\\uvx.exe",
      "args": [
        "--from",
        "C:\\Users\\matth\\downloads\\mcp-flowise",
        "mcp-flowise"
      ],
      "env": {
        "LOGLEVEL": "ERROR",
        "APPDATA": "C:\\Users\\matth\\AppData\\Roaming",
        "FLOWISE_API_KEY": "your-api-key-goes-here",
        "FLOWISE_API_ENDPOINT": "http://localhost:3000/"
      }
    }
  }
}
```

### Notes

- **Full Paths**: Use full paths for both `uvx.exe` and the cloned repository.
- **Environment Variables**: Point `APPDATA` to your Windows user profile (e.g., `C:\\Users\\<username>\\AppData\\Roaming`) if needed.
- **Log Level**: Adjust `LOGLEVEL` as needed (`ERROR`, `INFO`, `DEBUG`, etc.).

## Environment Variables

`mcp-flowise` relies on a few key environment variables:

- `FLOWISE_API_KEY`: Your Flowise API Bearer token. (**Required**)
- `FLOWISE_API_ENDPOINT`: Base URL for Flowise (default: `http://localhost:3000`). (**Required**)

Depending on which mode you use:

- **FastMCP Mode** (Default):
  - `FLOWISE_CHATFLOW_ID`: Single Chatflow ID (optional).
  - `FLOWISE_ASSISTANT_ID`: Single Assistant ID (optional).
  - `FLOWISE_CHATFLOW_WHITELIST`: Comma-separated list of allowed chatflow IDs (optional).
  - `FLOWISE_CHATFLOW_BLACKLIST`: Comma-separated list of denied chatflow IDs (optional).

- **LowLevel Mode**:
  - `FLOWISE_CHATFLOW_DESCRIPTIONS`: A comma-separated list of `chatflow_id:Description` pairs. Example:
    ```
    FLOWISE_CHATFLOW_DESCRIPTIONS="abc123:My Chatflow,hijk456:Another Chatflow"
    ```

> **Important**: If both `FLOWISE_CHATFLOW_ID` and `FLOWISE_ASSISTANT_ID` are set, the server will refuse to start.

## Configuration Scenarios

### 1. FastMCP Mode (Default)

**Tools Exposed**:
- `list_chatflows() -> list`: Lists all available chatflows and assistants.
- `create_prediction(chatflow_id: str, question: str) -> str`: Creates a prediction using the provided `chatflow_id`.

![image](https://github.com/user-attachments/assets/0901ef9c-5d56-4f1e-a799-1e5d8e8343bd)

### 2. LowLevel Mode (Dynamic Tools)

- Tools are dynamically created based on the `FLOWISE_CHATFLOW_DESCRIPTIONS` variable.
- Each chatflow or assistant is exposed as a separate tool.
- **Example**:  
  `predict_mock_chatflow_id(question: str) -> str`

### 3. Both `FLOWISE_CHATFLOW_ID` and `FLOWISE_ASSISTANT_ID` Set

- **Behavior**: The server will refuse to start and output an error message.

## Example Usage

### Run via `uvx` with Environment Variables

```bash
FLOWISE_API_KEY="your_api_key" \
FLOWISE_API_ENDPOINT="http://localhost:3000" \
uvx --from git+https://github.com/matthewhand/mcp-flowise mcp-flowise
```

### Locally with Python

```bash
export FLOWISE_API_KEY="your_api_key"
export FLOWISE_API_ENDPOINT="http://localhost:3000"
python -m mcp_flowise
```

## Security

- **Protect Your Credentials**: Ensure that environment variables or `.env` files containing API keys are **never** committed to version control. Add `.env` to your `.gitignore` if necessary.

```gitignore
# .gitignore
.env
```

## Error Handling

- **Both IDs Set**: The server will not start and will output an error message.
- **Missing API Key**: If `FLOWISE_API_KEY` is not set, authenticated requests may fail.
- **Invalid Chatflow**: Providing an invalid `chatflow_id` will result in an error.
- **Missing Descriptions**: In LowLevel mode, all chatflows must have valid descriptions.

## TODO

- [x] Claude desktop integration
- [x] Fastmcp mode
- [ ] Lowlevel mode

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
