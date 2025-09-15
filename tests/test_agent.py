"""
Comprehensive Test Suite for MCP Agent Orchestrator.

This module contains unit tests for the MCPAgentOrchestrator class
and its functionality, including connection management and tool discovery.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from src.agent.agent_wrapper import MCPAgentOrchestrator, AgentConfiguration, ServerConnectionStatus


class TestMCPAgentOrchestrator:
    """Test cases for MCPAgentOrchestrator class."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        return {
            "mcpservers": {
                "test_server": {
                    "type": "stdio",
                    "command": "python -m test_server",
                    "description": "Test server"
                }
            },
            "timeout": 30
        }
    
    @pytest.fixture
    def agent_orchestrator(self, mock_config):
        """Create an MCPAgentOrchestrator instance for testing."""
        with patch('src.utils.config_loader.config_loader') as mock_loader:
            mock_loader.get_servers.return_value = mock_config["mcpservers"]
            mock_loader.validate_server_configuration.return_value = Mock(is_valid=True)
            return MCPAgentOrchestrator()
    
    def test_orchestrator_initialization(self, agent_orchestrator):
        """Test orchestrator initialization."""
        assert agent_orchestrator.ai_agent is None
        assert agent_orchestrator.active_toolsets == []
        assert agent_orchestrator.server_connections == {}
        assert agent_orchestrator.config.model_name == "gemini-2.0-flash-exp"
    
    def test_orchestrator_initialization_with_tool_filter(self):
        """Test orchestrator initialization with tool filter."""
        tool_filter = ["tool1", "tool2"]
        orchestrator = MCPAgentOrchestrator(tool_filter)
        assert orchestrator.config.tool_filter == tool_filter
    
    @pytest.mark.asyncio
    async def test_agent_initialization_success(self, agent_orchestrator):
        """Test successful agent initialization."""
        with patch.object(agent_orchestrator, '_discover_and_connect_toolsets') as mock_discover:
            mock_discover.return_value = []
            
            await agent_orchestrator.initialize_agent()
            
            assert agent_orchestrator.ai_agent is not None
            assert agent_orchestrator.ai_agent.name == "Universal MCP Assistant"
    
    @pytest.mark.asyncio
    async def test_agent_initialization_failure(self, agent_orchestrator):
        """Test agent initialization failure handling."""
        with patch.object(agent_orchestrator, '_discover_and_connect_toolsets') as mock_discover:
            mock_discover.side_effect = Exception("Connection failed")
            
            with pytest.raises(RuntimeError, match="Agent initialization failed"):
                await agent_orchestrator.initialize_agent()
    
    def test_generate_agent_instructions(self, agent_orchestrator):
        """Test agent instruction generation."""
        instructions = agent_orchestrator._generate_agent_instructions()
        
        assert isinstance(instructions, str)
        assert "temperature conversion" in instructions.lower()
        assert "file operations" in instructions.lower()
        assert len(instructions) > 100  # Should be comprehensive
    
    @pytest.mark.asyncio
    async def test_discover_and_connect_toolsets_success(self, agent_orchestrator):
        """Test successful toolset discovery and connection."""
        mock_toolset = Mock()
        mock_toolset.get_tools = AsyncMock(return_value=[Mock(name="test_tool")])
        
        with patch('src.agent.agent_wrapper.MCPToolset') as mock_toolset_class:
            mock_toolset_class.return_value = mock_toolset
            
            toolsets = await agent_orchestrator._discover_and_connect_toolsets()
            
            assert len(toolsets) == 1
            assert "test_server" in agent_orchestrator.server_connections
            assert agent_orchestrator.server_connections["test_server"].status == "connected"
    
    @pytest.mark.asyncio
    async def test_discover_and_connect_toolsets_validation_failure(self, agent_orchestrator):
        """Test toolset discovery with validation failure."""
        with patch('src.utils.config_loader.config_loader') as mock_loader:
            mock_loader.validate_server_configuration.return_value = Mock(is_valid=False)
            
            toolsets = await agent_orchestrator._discover_and_connect_toolsets()
            
            assert len(toolsets) == 0
            assert agent_orchestrator.server_connections["test_server"].status == "invalid_configuration"
    
    @pytest.mark.asyncio
    async def test_build_connection_parameters_http(self, agent_orchestrator):
        """Test HTTP connection parameter building."""
        server_config = {
            "type": "http",
            "url": "http://localhost:8000"
        }
        
        with patch('src.agent.agent_wrapper.StreamableHTTPServerParams') as mock_params:
            result = await agent_orchestrator._build_connection_parameters("test_server", server_config)
            
            assert result is not None
            mock_params.assert_called_once_with(url="http://localhost:8000")
    
    @pytest.mark.asyncio
    async def test_build_connection_parameters_stdio(self, agent_orchestrator):
        """Test stdio connection parameter building."""
        server_config = {
            "type": "stdio",
            "command": "python -m test_server",
            "args": ["arg1", "arg2"]
        }
        
        with patch('src.agent.agent_wrapper.StdioConnectionParams') as mock_params:
            result = await agent_orchestrator._build_connection_parameters("test_server", server_config)
            
            assert result is not None
            mock_params.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_build_connection_parameters_invalid_type(self, agent_orchestrator):
        """Test connection parameter building with invalid type."""
        server_config = {
            "type": "invalid_type"
        }
        
        result = await agent_orchestrator._build_connection_parameters("test_server", server_config)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_build_connection_parameters_missing_url(self, agent_orchestrator):
        """Test HTTP connection parameter building with missing URL."""
        server_config = {
            "type": "http"
        }
        
        result = await agent_orchestrator._build_connection_parameters("test_server", server_config)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_build_connection_parameters_missing_command(self, agent_orchestrator):
        """Test stdio connection parameter building with missing command."""
        server_config = {
            "type": "stdio"
        }
        
        result = await agent_orchestrator._build_connection_parameters("test_server", server_config)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_shutdown(self, agent_orchestrator):
        """Test orchestrator shutdown."""
        mock_toolset = Mock()
        mock_toolset.close = AsyncMock()
        agent_orchestrator.active_toolsets = [mock_toolset]
        agent_orchestrator.ai_agent = Mock()
        
        await agent_orchestrator.shutdown()
        
        assert agent_orchestrator.active_toolsets == []
        assert agent_orchestrator.ai_agent is None
        mock_toolset.close.assert_called_once()
    
    def test_get_connection_status(self, agent_orchestrator):
        """Test getting connection status."""
        status = ServerConnectionStatus(name="test_server", status="connected")
        agent_orchestrator.server_connections["test_server"] = status
        
        result = agent_orchestrator.get_connection_status()
        
        assert "test_server" in result
        assert result["test_server"].status == "connected"
    
    def test_is_initialized_false(self, agent_orchestrator):
        """Test is_initialized when not initialized."""
        assert not agent_orchestrator.is_initialized()
    
    def test_is_initialized_true(self, agent_orchestrator):
        """Test is_initialized when initialized."""
        agent_orchestrator.ai_agent = Mock()
        assert agent_orchestrator.is_initialized()


class TestAgentConfiguration:
    """Test cases for AgentConfiguration dataclass."""
    
    def test_default_configuration(self):
        """Test default configuration values."""
        config = AgentConfiguration()
        
        assert config.model_name == "gemini-2.0-flash-exp"
        assert config.agent_name == "Universal MCP Assistant"
        assert config.max_retry_attempts == 3
        assert config.connection_timeout == 30
        assert config.tool_filter == []


class TestServerConnectionStatus:
    """Test cases for ServerConnectionStatus dataclass."""
    
    def test_default_status(self):
        """Test default connection status values."""
        status = ServerConnectionStatus(name="test_server")
        
        assert status.name == "test_server"
        assert status.status == "disconnected"
        assert status.tool_count == 0
        assert status.error_message is None
        assert status.connection_time is None


if __name__ == "__main__":
    pytest.main([__file__])
