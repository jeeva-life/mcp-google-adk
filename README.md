"# MCP Google ADK

Model Context Protocol implementation with Google ADK integration.

## Overview

MCP Google ADK is a comprehensive implementation of the Model Context Protocol (MCP) that integrates with Google's AI Development Kit (ADK). This project provides a modular architecture for building and managing MCP servers and clients with support for both HTTP and stdio communication protocols.

## Features

- **Modular Architecture**: Clean separation of concerns with agent, client, and server components
- **Multiple Server Types**: Support for both HTTP/Streamable and stdio-based MCP servers
- **Command Line Interface**: Full-featured CLI for managing servers, executing tools, and client operations
- **Comprehensive Testing**: Unit tests for all major components
- **Configuration Management**: Flexible configuration system with JSON and environment variable support
- **Temperature Server**: Example HTTP server for temperature conversion operations
- **Terminal Server**: Example stdio server for terminal command execution
- **Response Formatting**: Built-in utilities for formatting responses in various formats

## Project Structure

```
├── .env                          # Environment variables
├── .gitignore                    # Git ignore patterns
├── README.md                     # Project documentation
├── requirements.txt              # Python dependencies
│
├── config/                      # Configuration files
│   ├── __init__.py
│   └── servers.json            # MCP server configurations
│
├── src/                        # Source code
│   ├── __init__.py
│   ├── agent/                  # Agent implementation
│   │   ├── __init__.py
│   │   └── agent_wrapper.py    # Agent logic and toolset management
│   ├── client/                 # Client implementation
│   │   ├── __init__.py
│   │   └── mcp_client.py       # Main client interface
│   └── utils/                  # Utilities and helpers
│       ├── __init__.py
│       ├── config_loader.py    # Configuration management
│       └── formatters.py       # Response formatting utilities
│
├── servers/                    # MCP server implementations
│   ├── __init__.py
│   ├── http/                   # HTTP/Streamable servers
│   │   ├── __init__.py
│   │   ├── temperature_server.py  # Temperature conversion server
│   │   └── server_launcher.py     # HTTP server launcher
│   └── stdio/                  # Stdio servers
│       ├── __init__.py
│       └── terminal_server.py  # Terminal command server
│
├── cli/                        # Command line interface
│   ├── __init__.py
│   └── main.py                 # CLI entry point
│
├── workspace/                  # Working directory for file operations
│   └── .gitkeep
│
└── tests/                      # Test files
    ├── __init__.py
    ├── test_agent.py
    ├── test_client.py
    └── test_servers.py
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd mcp-google-adk
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env .env.local
# Edit .env.local with your configuration
```

## Usage

### Command Line Interface

The project provides a comprehensive CLI for managing MCP operations:

```bash
# Server management
python cli/main.py server start temperature_server
python cli/main.py server stop all
python cli/main.py server status
python cli/main.py server list

# Tool execution
python cli/main.py tool convert_temperature --value 32 --from fahrenheit --to celsius
python cli/main.py tool list_directory
python cli/main.py tool read_file --path /path/to/file

# Client operations
python cli/main.py client connect temperature_server
python cli/main.py client disconnect temperature_server

# Agent management
python cli/main.py agent init
python cli/main.py agent status
```

### Server Implementations

#### Temperature Server (HTTP)
The temperature server provides temperature conversion capabilities:
- Convert between Celsius, Fahrenheit, and Kelvin
- Get available temperature formats and conversion formulas

#### Terminal Server (Stdio)
The terminal server provides command execution capabilities:
- Execute terminal commands (with security restrictions)
- List directory contents
- Read file contents

### Configuration

Server configurations are managed in `config/servers.json`:

```json
{
  "servers": {
    "temperature_server": {
      "name": "Temperature Conversion Server",
      "type": "http",
      "host": "localhost",
      "port": 8001,
      "description": "HTTP server for temperature conversion operations",
      "tools": ["convert_temperature", "get_temperature_formats"],
      "enabled": true
    }
  }
}
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_agent.py

# Run with coverage
pytest --cov=src --cov-report=html
```

### Code Quality

The project includes several code quality tools:

```bash
# Format code
black src/ servers/ cli/ tests/

# Sort imports
isort src/ servers/ cli/ tests/

# Lint code
flake8 src/ servers/ cli/ tests/

# Type checking
mypy src/ servers/ cli/
```

### Adding New Servers

1. Create a new server class in the appropriate directory (`servers/http/` or `servers/stdio/`)
2. Implement the required MCP methods (`tools/list`, `tools/call`)
3. Add server configuration to `config/servers.json`
4. Write tests for the new server
5. Update documentation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions and support, please open an issue in the repository or contact the development team." 
