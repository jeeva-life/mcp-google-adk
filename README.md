# Advanced MCP Communication Interface

A sophisticated Model Context Protocol (MCP) implementation with Google AI Development Kit (ADK) integration, featuring comprehensive debugging capabilities and advanced session management.

## 🚀 Overview

The Advanced MCP Communication Interface is a fully functional implementation of the Model Context Protocol that integrates seamlessly with Google's AI Development Kit. This project provides a modular, production-ready architecture for building and managing MCP servers and clients with support for both HTTP and stdio communication protocols.

## ✨ Features

- **🔧 Advanced Agent Orchestration**: Sophisticated AI agent management with Google ADK integration
- **🌐 Multiple Server Types**: Support for HTTP/Streamable and stdio-based MCP servers
- **💬 Interactive CLI**: Full-featured command-line interface with comprehensive debugging
- **🌡️ Temperature Conversion**: Complete temperature conversion server (Celsius, Fahrenheit, Kelvin)
- **💻 Terminal Operations**: Secure terminal command execution with workspace isolation
- **🔍 Verbose Debugging**: Real-time MCP interaction monitoring and detailed logging
- **⚙️ Configuration Management**: Flexible configuration system with JSON and environment support
- **🧪 Comprehensive Testing**: Unit tests for all major components
- **📊 Response Formatting**: Advanced utilities for formatting responses in multiple formats
- **🔒 Security Features**: Input validation, workspace sandboxing, and command restrictions

## 📁 Project Structure

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
│   │   └── agent_wrapper.py    # MCPAgentOrchestrator - Advanced agent management
│   ├── client/                 # Client implementation
│   │   ├── __init__.py
│   │   └── mcp_client.py       # AdvancedMCPCommunicationInterface
│   └── utils/                  # Utilities and helpers
│       ├── __init__.py
│       ├── config_loader.py    # MCPConfigurationManager
│       └── formatters.py       # AdvancedResponseFormatter
│
├── servers/                    # MCP server implementations
│   ├── __init__.py
│   ├── http/                   # HTTP/Streamable servers
│   │   ├── __init__.py
│   │   ├── temperature_server.py  # Temperature conversion server
│   │   └── server_launcher.py     # HTTP server launcher
│   └── stdio/                  # Stdio servers
│       ├── __init__.py
│       └── terminal_server.py  # Secure terminal command server
│
├── cli/                        # Command line interface
│   ├── __init__.py
│   └── main.py                 # AdvancedMCPCommandLineInterface
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

## 🛠️ Installation

### Prerequisites
- Python 3.12+
- Google API Key (for Gemini model access)

### Setup Instructions

1. **Clone the repository:**
```bash
git clone <repository-url>
cd mcp-google-adk
```

2. **Create and activate virtual environment:**
```bash
# Using uv (recommended)
uv venv
uv pip install -r requirements.txt

# Or using pip
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Configure environment variables:**
```bash
# Set your Google API key
export GOOGLE_API_KEY="your-api-key-here"
# Or
export GEMINI_API_KEY="your-api-key-here"
```

## 🚀 Usage

### Quick Start

Launch the interactive communication interface:

```bash
uv run python cli/main.py
```

### Interactive Commands

Once the application starts, you can use these commands:

- **Natural Language Requests**: Ask questions like "Convert 25°C to Fahrenheit"
- **`status`**: Display system status and server connections
- **`debug on/off`**: Toggle verbose debugging mode
- **`help`**: Show example requests and usage tips
- **`quit`, `exit`, `:q`**: Exit the application

### Example Interactions

```
You: Convert 52 degrees Celsius to Kelvin scale
Assistant: Processing your request...
[VERBOSE DEBUGGING] Displaying detailed MCP interactions:

Final Agent Response:
```tool_code
print(52 + 273.15)
```
```

### Available Tools

#### Temperature Conversion Server
- `celsius_to_fahrenheit` - Convert Celsius to Fahrenheit
- `fahrenheit_to_celsius` - Convert Fahrenheit to Celsius
- `celsius_to_kelvin` - Convert Celsius to Kelvin
- `kelvin_to_celsius` - Convert Kelvin to Celsius
- `fahrenheit_to_kelvin` - Convert Fahrenheit to Kelvin
- `kelvin_to_fahrenheit` - Convert Kelvin to Fahrenheit

#### Terminal Server
- `run_command` - Execute terminal commands (with security restrictions)
- `list_directory` - List directory contents
- `read_file` - Read file contents
- `write_file` - Write content to file

## ⚙️ Configuration

### Server Configuration (`config/servers.json`)

```json
{
    "mcpservers": {
        "temperature_server": {
            "type": "http",
            "url": "http://localhost:8001",
            "description": "Temperature conversion server"
        },
        "terminal_server": {
            "type": "stdio",
            "command": "python -m servers.stdio.terminal_server",
            "description": "Terminal command execution server for file operations and system tasks"
        }
    }
}
```

### Environment Variables

```bash
# Google API Configuration
GOOGLE_API_KEY=your-google-api-key
GEMINI_API_KEY=your-gemini-api-key  # Alternative to GOOGLE_API_KEY

# Application Configuration
MCP_CONFIG_PATH=config/servers.json
LOG_LEVEL=INFO
DEBUG_MODE=false
```

## 🔧 Development

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_agent.py

# Run with coverage
pytest --cov=src --cov-report=html
```

### Code Quality Tools

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

1. **Create server implementation** in `servers/http/` or `servers/stdio/`
2. **Implement MCP methods** using FastMCP framework
3. **Add configuration** to `config/servers.json`
4. **Write tests** for the new server
5. **Update documentation**

### Server Development Example

```python
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

# Create FastMCP server
mcp = FastMCP("my_server", host="localhost", port=8002, stateless_http=True)

# Define input/output models
class MyInput(BaseModel):
    value: str = Field(..., description="Input value")

class MyOutput(BaseModel):
    result: str = Field(..., description="Processing result")

# Register tool
@mcp.tool(description="My custom tool")
async def my_tool(params: MyInput) -> MyOutput:
    return MyOutput(result=f"Processed: {params.value}")

# Start server
if __name__ == "__main__":
    import asyncio
    asyncio.run(mcp.run_streamable_http_async())
```

## 🐛 Troubleshooting

### Common Issues

1. **Server not starting**: Check if port 8001 is available
2. **API key errors**: Ensure GOOGLE_API_KEY is set correctly
3. **Import errors**: Verify all dependencies are installed
4. **Permission errors**: Check workspace directory permissions

### Debug Mode

Enable verbose debugging to see detailed MCP interactions:

```bash
# In the CLI
debug on

# Or set environment variable
export DEBUG_MODE=true
```

### Logs

Application logs are written to:
- Console output (INFO level and above)
- `mcp_interface.log` file (all levels)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest`)
6. Run code quality checks (`black`, `flake8`, `mypy`)
7. Commit your changes (`git commit -m 'Add amazing feature'`)
8. Push to the branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: Open an issue in the repository
- **Documentation**: Check the inline code documentation
- **Examples**: See the `tests/` directory for usage examples

## 🎯 Roadmap

- [ ] Web-based interface
- [ ] Additional MCP server implementations
- [ ] Enhanced security features
- [ ] Performance optimizations
- [ ] Docker containerization
- [ ] Kubernetes deployment support

---

**Built with ❤️ using Google ADK and FastMCP**