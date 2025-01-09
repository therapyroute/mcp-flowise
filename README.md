# mcp-flowise

`mcp-flowise` is a Python package that implements a Model Context Protocol (MCP) server integrating with the Flowise API. It provides a streamlined way to create predictions, list chatflows, and manage assistants in a standardized and flexible manner. It supports two operation modes:
- **FastMCP Mode**: Exposes `list_chatflows` and `create_prediction` tools with minimal configuration.
- **LowLevel Mode**: Dynamically creates tools for each chatflow or assistant, requiring descriptions for each.

## Features

- **Authentication**: Interact securely with the Flowise API using Bearer tokens.
- **Dynamic Tool Exposure**: Exposes tools based on configuration, either as generalized tools (FastMCP) or dynamically created tools (LowLevel).
- **Flexible Deployment**: Can be run directly or integrated into larger MCP workflows using `uvx`.
- **Environment Configuration**: Manage sensitive configurations through `.env` files or environment variables.

## Installation

### Prerequisites

- Python 3.12 or higher
- `pip` package manager

## Running the Server

### Using `uvx` from GitHub

The easiest way to run the server is via `uvx`, which installs and executes the package directly from the GitHub repository.

```bash
uvx --from git+https://github.com/matthewhand/mcp-flowise mcp-flowise
```

### Adding to MCP Ecosystem (`mcpServers` Configuration)

You can integrate `mcp-flowise` into your MCP ecosystem by adding it to the `mcpServers` configuration. Example configuration:

```json
{
    "mcpServers": {
        "mcp-flowise": {
            "command": "uvx",
            "args": [
                "--from", 
                "git+https://github.com/matthewhand/mcp-flowise", 
                "--with", "requests",
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

### Running Locally with `.env`

For local testing or deployment, follow these steps:

1. Clone the repository:

   ```bash
   git clone https://github.com/matthewhand/mcp-flowise.git
   cd mcp-flowise
   ```

2. Set up environment variables:

   - Copy `.env.example` to `.env`:

     ```bash
     cp .env.example .env
     ```

   - Edit the `.env` file and set the following variables:

     **Required Variables**:
     - `FLOWISE_API_KEY`: Your Flowise API Bearer token.
     - `FLOWISE_API_ENDPOINT`: The base URL of your Flowise API (default: `http://localhost:3000`).

     **Optional Variables**:
     - `FLOWISE_CHATFLOW_ID`: A specific Chatflow ID to use (FastMCP mode).
     - `FLOWISE_ASSISTANT_ID`: A specific Assistant ID to use (FastMCP mode).
     - `FLOWISE_CHATFLOW_DESCRIPTIONS`: Comma-separated list of chatflows and descriptions for LowLevel mode.

     **Important**: If both `FLOWISE_CHATFLOW_ID` and `FLOWISE_ASSISTANT_ID` are set, the server will refuse to start.

3. Install dependencies:

   ```bash
   pip install -e .
   ```

4. Run the server:

   ```bash
   mcp-flowise
   ```

## Configuration Scenarios

### 1. FastMCP Mode (Default)

**Tools Exposed**:
- `list_chatflows() -> list`: Lists all available chatflows and assistants.
- `create_prediction(chatflow_id: str, question: str) -> str`: Creates a prediction using the provided `chatflow_id`.

### 2. LowLevel Mode (Dynamic Tools)

- Tools are dynamically created based on the `FLOWISE_CHATFLOW_DESCRIPTIONS` variable.
- Each chatflow or assistant is exposed as a separate tool.
- **Example**:
  - `predict_mock_chatflow_id(question: str) -> str`

### 3. Both `FLOWISE_CHATFLOW_ID` and `FLOWISE_ASSISTANT_ID` Set

- **Behavior**: The server will refuse to start and output an error message.

## Example Usage

### Run via `uvx` with Environment Variables

```bash
FLOWISE_API_KEY="your_api_key" \
FLOWISE_API_ENDPOINT="http://localhost:3000" \
uvx --from git+https://github.com/matthewhand/mcp-flowise --with requests mcp-flowise
```

### Locally with Python

```bash
export FLOWISE_API_KEY="your_api_key"
export FLOWISE_API_ENDPOINT="http://localhost:3000"
python -m mcp_flowise
```

---

## Security

- **Protect Your `.env` File**: Ensure that your `.env` file is **never** committed to version control. Add `.env` to your `.gitignore` to prevent accidental exposure of sensitive information like API keys.

```gitignore
# .gitignore
.env
```

## Error Handling

- **Both IDs Set**: The server will not start and will output an error message.
- **Missing API Key**: If `FLOWISE_API_KEY` is not set, authenticated requests may fail.
- **Invalid Chatflow**: Providing an invalid `chatflow_id` will result in an error.
- **Missing Descriptions**: In LowLevel mode, all chatflows must have valid descriptions.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
