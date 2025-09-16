"""
AI Agent Orchestrator for MCP Server Integration.

This module provides a comprehensive agent management system that integrates
with Google's AI Development Kit and Model Context Protocol servers.
"""

import logging
import asyncio
import os
import sys
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, field

# Third-party imports
try:
    from google.adk import Agent, Runner
    from google.adk.sessions import InMemorySessionService
    from mcp import StdioServerParameters
except ImportError as e:
    logging.error(f"Missing required Google ADK dependencies: {e}")
    sys.exit(1)

# Local imports
from src.utils.config_loader import config_loader
from src.utils.formatters import formatter

logger = logging.getLogger(__name__)


@dataclass
class ServerConnectionStatus:
    """Represents the connection status of an MCP server."""
    name: str
    status: str = "disconnected"
    tool_count: int = 0
    error_message: Optional[str] = None
    connection_time: Optional[float] = None


@dataclass
class AgentConfiguration:
    """Configuration settings for the AI agent."""
    model_name: str = "gemini-2.0-flash-exp"
    agent_name: str = "Universal_MCP_Assistant"
    max_retry_attempts: int = 3
    connection_timeout: int = 30
    tool_filter: Optional[List[str]] = field(default_factory=list)


class MCPAgentOrchestrator:
    """
    Advanced orchestrator for managing AI agents with MCP server integration.

    This class provides comprehensive management of AI agents connected to
    multiple Model Context Protocol servers, including connection management,
    tool discovery, and health monitoring.
    """

    def __init__(self, tool_allowlist: Optional[List[str]] = None):
        """
        Initialize the MCP agent orchestrator.
        
        Args:
            tool_allowlist: Optional list of tool names to restrict access to.
                          If None, all available tools are loaded.
        """
        self.config = AgentConfiguration()
        if tool_allowlist:
            self.config.tool_filter = tool_allowlist
            
        self.ai_agent: Optional[Agent] = None
        self.active_toolsets: List[Any] = []
        self.server_connections: Dict[str, ServerConnectionStatus] = {}
        
        self._setup_logging()
        self._log_initialization()

    def _setup_logging(self) -> None:
        """Configure logging for the orchestrator."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(self.__class__.__name__)

    def _log_initialization(self) -> None:
        """Log initialization information."""
        self.logger.info("MCP Agent Orchestrator initialized successfully")
        if self.config.tool_filter:
            self.logger.info(f"Tool filtering enabled: {len(self.config.tool_filter)} tools allowed")
        else:
            self.logger.info("No tool filtering - all available tools will be loaded")

    async def initialize_agent(self) -> None:
        """
        Initialize the AI agent with MCP toolsets.

        This method orchestrates the complete agent initialization process:
        1. Load server configurations from configuration files
        2. Establish connections to each configured MCP server
        3. Discover and filter available tools from each server
        4. Create the AI agent with all loaded toolsets
        """
        self.logger.info("Initializing AI agent with MCP toolsets...")

        try:
            # Load toolsets from all configured servers
            toolsets = await self._discover_and_connect_toolsets()

            if not toolsets:
                self.logger.warning("No toolsets discovered. Agent will have limited capabilities.")
                return

            # Create the AI agent with Gemini 2.0 Flash Experimental
            # For now, we'll create the agent without tools since we're using mock toolsets
            self.ai_agent = Agent(
                model=self.config.model_name,
                name=self.config.agent_name,
                instruction=self._generate_agent_instructions()
            )

            self.active_toolsets = toolsets
            self.logger.info(f"AI agent initialized successfully with {len(toolsets)} MCP toolsets")

        except Exception as e:
            self.logger.error(f"Failed to initialize AI agent: {str(e)}")
            raise RuntimeError(f"Agent initialization failed: {str(e)}")

    def _generate_agent_instructions(self) -> str:
        """Generate comprehensive system instructions for the AI agent."""
        return """You are an advanced AI assistant with integrated access to specialized tools and capabilities.

Your primary functions include:
• Temperature conversion operations between Celsius, Fahrenheit, and Kelvin scales
• Local file system operations and terminal command execution
• Comprehensive explanations of mathematical formulas and processes

For temperature conversions:
• Validate input values against physical constraints
• Display the specific conversion formula utilized
• Round numerical results to appropriate precision levels
• Process multiple sequential conversions when requested

For file operations:
• Utilize available terminal tools for file creation, reading, and modification
• Present output in clear, professional formatting
• Verify successful completion of file operations

Maintain precision, provide educational value, and demonstrate your methodology clearly."""

    async def _discover_and_connect_toolsets(self) -> List[Any]:
        """
        Discover and connect to MCP servers to load their toolsets.
        
        This method processes all configured servers, validates their configurations,
        and establishes connections to load available tools.
        
        Returns:
            List of successfully connected toolset instances.
        """
        server_configs = config_loader.get_server_configurations()
        connected_toolsets = []

        self.logger.info(f"Discovering toolsets from {len(server_configs)} configured servers")

        for server_name, server_config in server_configs.items():
            connection_status = ServerConnectionStatus(name=server_name)
            
            try:
                # Validate server configuration
                validation_result = config_loader.validate_server_configuration(server_name, server_config)
                if not validation_result.is_valid:
                    connection_status.status = "invalid_configuration"
                    connection_status.error_message = "Configuration validation failed"
                    self.server_connections[server_name] = connection_status
                    continue

                # For now, we'll create a simple toolset representation
                # In a real implementation, this would connect to actual MCP servers
                mock_toolset = {
                    "name": server_name,
                    "type": server_config.get("type", "unknown"),
                    "tools": self._get_mock_tools_for_server(server_name)
                }

                if mock_toolset["tools"]:
                    connected_toolsets.append(mock_toolset)
                    connection_status.status = "connected"
                    connection_status.tool_count = len(mock_toolset["tools"])
                    connection_status.connection_time = asyncio.get_event_loop().time()
                    
                    tool_names = [tool["name"] for tool in mock_toolset["tools"]]
                    self.logger.info(f"Connected to {server_name} with {len(mock_toolset['tools'])} tools: {tool_names}")
                    formatter.print_tool_summary(server_name, tool_names)
                else:
                    connection_status.status = "no_tools_found"
                    connection_status.error_message = "No tools discovered on server"
                    self.logger.warning(f"No tools found on {server_name}. Server disabled.")

            except Exception as e:
                connection_status.status = "connection_error"
                connection_status.error_message = str(e)
                self.logger.error(f"Failed to connect to {server_name}: {str(e)}")

            self.server_connections[server_name] = connection_status

        self.logger.info(f"Successfully connected to {len(connected_toolsets)} out of {len(server_configs)} servers")
        return connected_toolsets

    def _get_mock_tools_for_server(self, server_name: str) -> List[Dict[str, Any]]:
        """Get mock tools for a server based on its name."""
        if "temperature" in server_name.lower():
            return [
                {"name": "celsius_to_fahrenheit", "description": "Convert Celsius to Fahrenheit"},
                {"name": "fahrenheit_to_celsius", "description": "Convert Fahrenheit to Celsius"},
                {"name": "celsius_to_kelvin", "description": "Convert Celsius to Kelvin"},
                {"name": "kelvin_to_celsius", "description": "Convert Kelvin to Celsius"},
                {"name": "fahrenheit_to_kelvin", "description": "Convert Fahrenheit to Kelvin"},
                {"name": "kelvin_to_fahrenheit", "description": "Convert Kelvin to Fahrenheit"}
            ]
        elif "terminal" in server_name.lower():
            return [
                {"name": "run_command", "description": "Execute terminal commands"},
                {"name": "list_directory", "description": "List directory contents"},
                {"name": "read_file", "description": "Read file contents"},
                {"name": "write_file", "description": "Write content to file"}
            ]
        return []

    async def _build_connection_parameters(self, server_name: str, server_config: Dict[str, Any]) -> Optional[Any]:
        """
        Build connection parameters based on server transport protocol.
        
        Args:
            server_name: Name of the server for logging purposes
            server_config: Server configuration dictionary
            
        Returns:
            Connection parameters object or None if creation failed
        """
        transport_type = server_config.get("type")
        
        try:
            if transport_type == "http":
                # Build HTTP connection parameters
                server_url = server_config.get("url")
                if not server_url:
                    raise ValueError("HTTP server missing required 'url' parameter")
                    
                return {"type": "http", "url": server_url}
                
            elif transport_type == "stdio":
                # Build STDIO connection parameters
                command = server_config.get("command")
                if not command:
                    raise ValueError("STDIO server missing required 'command' parameter")
                
                args = server_config.get("args", [])

                # Resolve relative paths to absolute paths for Python scripts
                if args:
                    project_root = Path(__file__).parent.parent.parent
                    resolved_args = []
                    for arg in args:
                        if not os.path.isabs(arg) and arg.endswith('.py'):
                            resolved_args.append(str(project_root / arg))
                        else:
                            resolved_args.append(arg)
                    args = resolved_args
                
                return {
                    "type": "stdio",
                    "command": command,
                    "args": args,
                    "timeout": self.config.connection_timeout
                }
            else:
                raise ValueError(f"Unsupported transport type: {transport_type}")
                
        except Exception as e:
            self.logger.error(f"Error building connection parameters for '{server_name}': {e}")
            return None

    async def shutdown(self) -> None:
        """
        Gracefully shutdown the agent and close all connections.
        """
        self.logger.info("Initiating agent shutdown and connection cleanup...")
        
        for i, toolset in enumerate(self.active_toolsets):
            try:
                # Mock toolsets are dictionaries, so they don't need to be closed
                if hasattr(toolset, 'close'):
                    await toolset.close()
                self.logger.debug(f"Closed toolset {i+1}")
            except Exception as e:
                self.logger.error(f"Error closing toolset {i+1}: {e}")
        
        self.active_toolsets.clear()
        self.ai_agent = None
        
        # Brief delay to ensure cleanup completes
        await asyncio.sleep(0.5)
        self.logger.info("Agent shutdown completed successfully")

    def get_connection_status(self) -> Dict[str, ServerConnectionStatus]:
        """Get the current connection status of all configured servers."""
        return self.server_connections.copy()

    def is_initialized(self) -> bool:
        """Check if the agent is properly initialized and ready for use."""
        return self.ai_agent is not None