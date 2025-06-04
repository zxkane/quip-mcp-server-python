[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/zxkane-quip-mcp-server-python-badge.png)](https://mseep.ai/app/zxkane-quip-mcp-server-python)

Check out the [Quip MCP Server (TypeScript)](https://github.com/zxkane/quip-mcp-server-typescript) repository for both stdio and http transport supports.

# Quip MCP Server

A Model Context Protocol (MCP) server for interacting with Quip spreadsheets. This server provides tools to read spreadsheet data from Quip documents and return the content in CSV format.

## Features

- Retrieve spreadsheet content from Quip documents
- Support for selecting specific sheets by name
- Returns data in CSV format with metadata
- Handles authentication via Quip API token
- Provides appropriate error messages for non-spreadsheet documents
- Automatically handles large spreadsheets by truncating content when necessary
- Stores spreadsheet content locally for efficient access
- Provides resource URIs for accessing complete spreadsheet content

## Installation

### Using uvx (recommended)

When using [`uv`](https://docs.astral.sh/uv/), no specific installation is needed. We will use [`uvx`](https://docs.astral.sh/uv/guides/tools/) to directly run the server:

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Run the server directly with uvx
uvx quip-mcp-server
```

### Using pip

Alternatively, you can install the package via pip:

```bash
pip install quip-mcp-server
```

After installation, you can run it as a script:

```bash
python -m src.server
```

### Set up environment variables

Set up the required environment variables:
```bash
export QUIP_TOKEN=your_quip_api_token
export QUIP_BASE_URL=https://platform.quip.com  # Optional, defaults to this value
export QUIP_STORAGE_PATH=/path/to/storage       # Optional, defaults to ~/.quip-mcp-server/storage
```
```

Alternatively, create a `.env` file in the root directory:
```
QUIP_TOKEN=your_quip_api_token
QUIP_BASE_URL=https://platform.quip.com
QUIP_STORAGE_PATH=/path/to/storage
```

## Usage

### Configure for Claude.app

Add to your Claude settings:

```json
"mcpServers": {
  "quip": {
    "command": "uvx",
    "args": ["quip-mcp-server", "--storage-path", "/path/to/storage"],
    "env": {
      "QUIP_TOKEN": "your_quip_api_token"
    }
  }
}
```

If you want to use the file protocol for resource URIs:

```json
"mcpServers": {
  "quip": {
    "command": "uvx",
    "args": ["quip-mcp-server", "--storage-path", "/path/to/storage", "--file-protocol"],
    "env": {
      "QUIP_TOKEN": "your_quip_api_token"
    }
  }
}
```

### Running the Server Manually

Run the server directly:

```bash
# Using uvx (recommended)
uvx quip-mcp-server --storage-path /path/to/storage

# Using python (if installed via pip)
python -m src.server --storage-path /path/to/storage

# With file protocol for resource URIs
uvx quip-mcp-server --storage-path /path/to/storage --file-protocol

# With debug logging enabled
uvx quip-mcp-server --storage-path /path/to/storage --debug
```

### Available Tools

#### quip_read_spreadsheet

Retrieves the content of a Quip spreadsheet as CSV.

**Parameters:**
- `threadId` (required): The Quip document thread ID
- `sheetName` (optional): Name of the sheet to extract. If not provided, the first sheet will be used.

**Example:**
```json
{
  "threadId": "AbCdEfGhIjKl",
  "sheetName": "Sheet1"
}
```

**Response:**
The tool returns a JSON object containing:
- `csv_content`: The spreadsheet content in CSV format (truncated if too large)
- `metadata`: Additional information about the spreadsheet:
  - `total_rows`: Total number of rows in the spreadsheet
  - `total_size`: Total size of the CSV content in bytes
  - `is_truncated`: Boolean indicating if the content was truncated
  - `resource_uri`: URI to access the complete spreadsheet content

**Example Response (default protocol):**
```json
{
  "csv_content": "header1,header2\nvalue1,value2\n...",
  "metadata": {
    "total_rows": 1000,
    "total_size": 52840,
    "is_truncated": true,
    "resource_uri": "quip://AbCdEfGhIjKl?sheet=Sheet1"
  }
}
```

**Example Response (with --file-protocol):**
```json
{
  "csv_content": "header1,header2\nvalue1,value2\n...",
  "metadata": {
    "total_rows": 1000,
    "total_size": 52840,
    "is_truncated": true,
    "resource_uri": "file:///path/to/storage/AbCdEfGhIjKl-Sheet1.csv"
  }
}
```

**Error Handling:**
- If the thread is not a spreadsheet, an error will be returned.
- If the specified sheet is not found, an error will be returned.

### Resource URIs

The server provides resource URIs for accessing complete spreadsheet content. These URIs can be used with the MCP resource access mechanism.

By default, the server uses the `quip://` protocol for resource URIs. However, you can use the `--file-protocol` option to use the `file://` protocol instead, which points directly to the local CSV files.

#### Default Protocol (quip://)

**URI Format:**
```
quip://{threadId}?sheet={sheetName}
```

**Example:**
```
quip://AbCdEfGhIjKl?sheet=Sheet1
```

#### File Protocol (with --file-protocol option)

**URI Format:**
```
file://{storage_path}/{threadId}-{sheetName}.csv
```

**Example:**
```
file:///home/user/.quip-mcp-server/storage/AbCdEfGhIjKl-Sheet1.csv
```

When accessed, the resource returns the complete CSV content of the spreadsheet, regardless of size.

## How It Works

The server uses two methods to extract spreadsheet data:

1. **Primary Method**: Exports the spreadsheet to XLSX format using the Quip API, then converts it to CSV.
2. **Fallback Method**: If the primary method fails, it parses the HTML content of the document to extract the table data.

For large spreadsheets, the server:
1. Saves the complete CSV content to local storage
2. Returns a truncated version (up to 10KB) with metadata
3. Provides a resource URI for accessing the complete content

### Command Line Arguments

The server supports the following command line arguments:

- `--storage-path`: Path to store CSV files (defaults to QUIP_STORAGE_PATH environment variable or ~/.quip-mcp-server/storage)
- `--file-protocol`: Use file protocol for resource URIs (instead of quip:// protocol)
- `--debug`: Enable debug logging

**Example:**
```bash
uvx quip-mcp-server --storage-path /path/to/storage
```

## Development

### Project Structure

```
quip-mcp-server/
├── src/
│   ├── __init__.py
│   ├── server.py       # Main MCP server implementation
│   ├── quip_client.py  # Quip API client
│   ├── tools.py        # Tool definitions and handlers
│   └── storage.py      # Storage abstraction and implementations
├── tests/
│   ├── __init__.py
│   ├── test_server.py  # Unit tests for the server
│   ├── test_storage.py # Unit tests for the storage module
│   └── e2e/            # End-to-end tests
│       ├── __init__.py
│       ├── conftest.py # Test fixtures for e2e tests
│       └── test_quip_integration.py # Integration tests with Quip API
├── .uv/
│   └── config.toml     # uv configuration settings
├── pyproject.toml      # Project metadata and dependencies (includes pytest config)
├── uvproject.yaml      # uv-specific project configuration
├── uv.lock             # Locked dependencies
├── .python-version     # Python version specification
├── .env.example        # Example environment variables
├── LICENSE             # MIT License
└── README.md           # Documentation
```

### Development with uv

This project uses [uv](https://github.com/astral-sh/uv) for dependency management. uv is a fast Python package installer and resolver that can replace pip and virtualenv.

#### Configuration Files

- `pyproject.toml`: Standard Python packaging configuration
- `uvproject.yaml`: uv-specific project configuration
- `.uv/config.toml`: uv configuration settings
- `.python-version`: Specifies Python 3.12 as the project's Python version (used by pyenv and other version managers)

#### Setting Up a Development Environment

To set up a development environment:

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create a virtual environment and install dependencies
uv venv
uv pip install -e .

# Install development dependencies
uv pip install pytest black isort mypy
```

Alternatively, you can use the uvproject.yaml file:

```bash
# Install dependencies from uvproject.yaml
uv pip sync
```

#### Running the Server with uv

```bash
# Using uvx (recommended for development)
uvx quip-mcp-server

# Or, if you're using a virtual environment:
# Activate the virtual environment (if not auto-activated)
source .venv/bin/activate

# Run the server
python -m src.server
```

#### Running Tests

The project uses pytest for testing. To run the tests:
```bash
# Install development dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=src

# Run only e2e tests
pytest tests/e2e

# Run a specific e2e test
pytest tests/e2e/test_quip_integration.py::test_connection
```

### End-to-End (e2e) Testing

The project includes end-to-end tests that verify integration with the actual Quip API. To run these tests:

1. Create a `.env.local` file in the project root with your test configuration:
   ```
   # Quip API token (required)
   QUIP_TOKEN=your_actual_quip_token_here
   
   # Test configuration
   TEST_THREAD_ID=your_test_spreadsheet_thread_id
   TEST_SHEET_NAME=Sheet1  # Optional: specific sheet name to test
   ```

2. Run the e2e tests:
   ```bash
   # Run all e2e tests
   pytest tests/e2e
   
   # Run with verbose output
   pytest -v tests/e2e
   ```

Note: The e2e tests will be skipped automatically if `.env.local` is missing or if required environment variables are not set.
```

#### Debugging

You can use the MCP inspector to debug the server:

```bash
# For uvx installations
npx @modelcontextprotocol/inspector uvx quip-mcp-server

# Or if you're developing locally
cd /path/to/quip-mcp-server
npx @modelcontextprotocol/inspector uv run src.server
```

### Adding New Tools

To add new tools:

1. Define the tool in `src/tools.py` by adding it to the `get_quip_tools()` function.
2. Implement the handler function for the tool.
3. Register the handler in `src/server.py` by adding it to the `call_tool()` function.

## License

[MIT License](LICENSE)
