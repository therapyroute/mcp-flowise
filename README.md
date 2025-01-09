# flowise_mcp

Flowise MCP is a Python package that implements a Model Context Protocol (MCP) server integrating with the Flowise API. It allows users to create predictions, list chatflows, and manage assistants in a standardized and secure manner.

## Features

- **Authentication**: Securely interact with the Flowise API using Bearer tokens.
- **Dynamic Tool Exposure**: Tools are exposed based on environment configurations.
- **Flexible Deployment**: Easily run directly or via `uvx` for seamless integration into other MCP workflows.
- **Environment Configuration**: Manage sensitive configurations using `.env` files or pass them directly into MCP server configurations.

## Installation

### Prerequisites

- Python 3.12 or higher
- `pip` package manager

## Running the Server

### Using `uvx` from GitHub

The easiest way to run the server is via `uvx`, which installs and executes it directly from the GitHub repository.

```bash
uvx --from git+https://github.com/matthewhand/flowise-mcp flowise-mcp
```

### Adding to `mcpServers` Configuration

You can integrate `flowise-mcp` into your MCP ecosystem by adding it to the `mcpServers` configuration. Here’s an example configuration:

```json
{
    "mcpServers": {
        "flowise-mcp": {
            "command": "uvx",
            "args": [
                "--from", 
                "git+https://github.com/matthewhand/flowise-mcp", 
                "flowise-mcp"
            ],
            "env": {
                "FLOWISE_API_KEY": "${FLOWISE_API_KEY}",
                "FLOWISE_API_ENDPOINT": "${FLOWISE_API_ENDPOINT}",
            }
        }
    }
}
```

### Running Locally with `.env`

If you prefer to run the server locally, follow these steps:

1. Clone the repository:

   ```bash
   git clone https://github.com/matthewhand/flowise-mcp.git
   cd flowise-mcp
   ```

2. Set up environment variables:

   - Copy `.env.example` to `.env`:

     ```bash
     cp .env.example .env
     ```

   - Edit the `.env` file and set the required variables:

     ```bash
     nano .env
     ```

     **Required Variables:**
     - `FLOWISE_API_KEY`: Your Flowise API Bearer token.
     - `FLOWISE_API_ENDPOINT`: The base URL of your Flowise API (default: `http://localhost:3000`).

     **Optional Variables:**
     - `FLOWISE_CHATFLOW_ID`: A specific Chatflow ID to use.
     - `FLOWISE_ASSISTANT_ID`: A specific Assistant ID to use.

     **Important**: If both `FLOWISE_CHATFLOW_ID` and `FLOWISE_ASSISTANT_ID` are set, the server will refuse to start.

3. Install dependencies:

   ```bash
   pip install -e .
   ```

4. Run the server:

   ```bash
   flowise-mcp
   ```

### Configuration Scenarios

#### 1. No IDs Set

- **Tools Exposed**:
  - `list_chatflows() -> str`: Lists all available chatflows.
  - `create_prediction(chatflow_id: str, question: str) -> str`: Creates a prediction using the provided `chatflow_id`.

#### 2. Single ID Set

- **Tools Exposed**:
  - `create_prediction(question: str) -> str`: Uses the pre-configured `FLOWISE_CHATFLOW_ID` or `FLOWISE_ASSISTANT_ID`.

#### 3. Both IDs Set

- **Behavior**:
  - The server will refuse to start and display an error message.

---

## Example Usage

### Run via `uvx` with Environment Variables

```bash
FLOWISE_API_KEY="your_api_key" \
FLOWISE_API_ENDPOINT="http://localhost:3000" \
uvx --from git+https://github.com/matthewhand/flowise-mcp flowise-mcp
```

If using a single ID (alternative use FLOWISE_ASSISTANT_ID instead of FLOWISE_CHATFLOW_ID):

```bash
FLOWISE_API_KEY="your_api_key" \
FLOWISE_API_ENDPOINT="http://localhost:3000" \
FLOWISE_CHATFLOW_ID="your_chatflow_id" \
uvx --from git+https://github.com/matthewhand/flowise-mcp flowise-mcp
```

### Locally with `python`

```bash
export FLOWISE_API_KEY="your_api_key"
export FLOWISE_API_ENDPOINT="http://localhost:3000"
python -m flowise_mcp
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
- **Invalid `model_type`**: When creating a prediction, specifying an invalid `model_type` will return an error.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

