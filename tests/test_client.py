"""
Comprehensive Test Suite for MCP Client Manager.

This module contains unit tests for the MCPClientManager class
and its functionality, including connection management and message handling.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from src.client.mcp_client import MCPClientManager, MCPMessage, MessageType, ConnectionInfo


class TestMCPClientManager:
    """Test cases for MCPClientManager class."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        return {
            "timeout": 30,
            "retry_attempts": 3
        }
    
    @pytest.fixture
    def client_manager(self, mock_config):
        """Create an MCPClientManager instance for testing."""
        return MCPClientManager(mock_config)
    
    def test_client_initialization(self, client_manager):
        """Test client manager initialization."""
        assert client_manager.config == {"timeout": 30, "retry_attempts": 3}
        assert client_manager.active_connections == {}
        assert client_manager.message_handlers == {}
        assert client_manager.connection_info == {}
        assert client_manager._message_id_counter == 0
    
    @pytest.mark.asyncio
    async def test_establish_connection_stdio(self, client_manager):
        """Test stdio connection establishment."""
        connection_config = {"type": "stdio"}
        
        result = await client_manager.establish_connection("test_server", connection_config)
        
        assert result is True
        assert "test_server" in client_manager.active_connections
        assert client_manager.connection_info["test_server"].connection_type == "stdio"
        assert client_manager.connection_info["test_server"].status == "connected"
    
    @pytest.mark.asyncio
    async def test_establish_connection_http(self, client_manager):
        """Test HTTP connection establishment."""
        connection_config = {
            "type": "http",
            "host": "localhost",
            "port": 8000
        }
        
        result = await client_manager.establish_connection("http_server", connection_config)
        
        assert result is True
        assert "http_server" in client_manager.active_connections
        connection_info = client_manager.connection_info["http_server"]
        assert connection_info.connection_type == "http"
        assert connection_info.status == "connected"
    
    @pytest.mark.asyncio
    async def test_establish_connection_invalid_type(self, client_manager):
        """Test connection establishment with invalid type."""
        connection_config = {"type": "invalid"}
        
        result = await client_manager.establish_connection("invalid_server", connection_config)
        
        assert result is False
        assert "invalid_server" not in client_manager.active_connections
        assert client_manager.connection_info["invalid_server"].status == "failed"
    
    @pytest.mark.asyncio
    async def test_send_request_message_success(self, client_manager):
        """Test successful request message sending."""
        # Establish connection first
        await client_manager.establish_connection("test_server", {"type": "stdio"})
        
        result = await client_manager.send_request_message(
            "test_server",
            "test_method",
            {"param": "value"}
        )
        
        assert "id" in result
        assert result["result"] is not None
        assert result["error"] is None
    
    @pytest.mark.asyncio
    async def test_send_request_message_no_connection(self, client_manager):
        """Test request message sending without connection."""
        result = await client_manager.send_request_message(
            "non_existent_server",
            "test_method",
            {}
        )
        
        assert result["result"] is None
        assert result["error"] is not None
        assert "No active connection" in result["error"]["message"]
    
    @pytest.mark.asyncio
    async def test_send_notification_message(self, client_manager):
        """Test notification message sending."""
        await client_manager.establish_connection("test_server", {"type": "stdio"})
        
        # Should not raise any exceptions
        await client_manager.send_notification_message(
            "test_server",
            "test_notification",
            {"data": "test"}
        )
    
    def test_register_message_handler(self, client_manager):
        """Test message handler registration."""
        def test_handler(params):
            return {"result": "test"}
        
        client_manager.register_message_handler("test_method", test_handler)
        
        assert "test_method" in client_manager.message_handlers
        assert client_manager.message_handlers["test_method"] == test_handler
    
    @pytest.mark.asyncio
    async def test_process_incoming_message_with_handler(self, client_manager):
        """Test message processing with registered handler."""
        async def test_handler(params):
            return {"processed": params}
        
        client_manager.register_message_handler("test_method", test_handler)
        
        message = {
            "id": "123",
            "method": "test_method",
            "params": {"test": "value"}
        }
        
        result = await client_manager.process_incoming_message(message)
        
        assert result is not None
        assert result["id"] == "123"
        assert result["result"]["processed"]["test"] == "value"
        assert result["error"] is None
    
    @pytest.mark.asyncio
    async def test_process_incoming_message_no_handler(self, client_manager):
        """Test message processing without registered handler."""
        message = {
            "id": "123",
            "method": "unknown_method",
            "params": {}
        }
        
        result = await client_manager.process_incoming_message(message)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_process_incoming_notification(self, client_manager):
        """Test processing notification messages."""
        async def test_handler(params):
            return {"processed": params}
        
        client_manager.register_message_handler("test_notification", test_handler)
        
        message = {
            "method": "test_notification",
            "params": {"test": "value"}
        }
        
        result = await client_manager.process_incoming_message(message)
        
        # Notifications should not return responses
        assert result is None
    
    def test_generate_unique_message_id(self, client_manager):
        """Test unique message ID generation."""
        id1 = client_manager._generate_unique_message_id()
        id2 = client_manager._generate_unique_message_id()
        
        assert id1 != id2
        assert isinstance(id1, str)
        assert isinstance(id2, str)
        assert len(id1) > 0
        assert len(id2) > 0
    
    @pytest.mark.asyncio
    async def test_terminate_connection(self, client_manager):
        """Test server connection termination."""
        await client_manager.establish_connection("test_server", {"type": "stdio"})
        
        assert "test_server" in client_manager.active_connections
        
        await client_manager.terminate_connection("test_server")
        
        assert "test_server" not in client_manager.active_connections
        assert client_manager.connection_info["test_server"].status == "disconnected"
    
    @pytest.mark.asyncio
    async def test_terminate_connection_non_existent(self, client_manager):
        """Test terminating non-existent connection."""
        # Should not raise any exceptions
        await client_manager.terminate_connection("non_existent_server")
    
    @pytest.mark.asyncio
    async def test_shutdown_client(self, client_manager):
        """Test client shutdown."""
        await client_manager.establish_connection("server1", {"type": "stdio"})
        await client_manager.establish_connection("server2", {"type": "http", "host": "localhost", "port": 8000})
        
        assert len(client_manager.active_connections) == 2
        
        await client_manager.shutdown_client()
        
        assert len(client_manager.active_connections) == 0
    
    def test_get_connection_status(self, client_manager):
        """Test getting connection status."""
        status = ConnectionInfo(name="test_server", connection_type="stdio", status="connected")
        client_manager.connection_info["test_server"] = status
        
        result = client_manager.get_connection_status()
        
        assert "test_server" in result
        assert result["test_server"].status == "connected"
    
    def test_is_connected_true(self, client_manager):
        """Test is_connected when connected."""
        status = ConnectionInfo(name="test_server", connection_type="stdio", status="connected")
        client_manager.connection_info["test_server"] = status
        client_manager.active_connections["test_server"] = {}
        
        assert client_manager.is_connected("test_server") is True
    
    def test_is_connected_false(self, client_manager):
        """Test is_connected when not connected."""
        assert client_manager.is_connected("non_existent_server") is False


class TestMCPMessage:
    """Test cases for MCPMessage class."""
    
    def test_message_creation(self):
        """Test MCP message creation."""
        message = MCPMessage(
            id="123",
            method="test_method",
            params={"param": "value"}
        )
        
        assert message.id == "123"
        assert message.method == "test_method"
        assert message.params == {"param": "value"}
        assert message.result is None
        assert message.error is None
    
    def test_message_to_dict(self):
        """Test message to dictionary conversion."""
        message = MCPMessage(
            id="123",
            method="test_method",
            params={"param": "value"},
            result={"success": True},
            error=None
        )
        
        message_dict = message.to_dict()
        
        assert message_dict["id"] == "123"
        assert message_dict["method"] == "test_method"
        assert message_dict["params"] == {"param": "value"}
        assert message_dict["result"] == {"success": True}
        assert message_dict["error"] is None


class TestConnectionInfo:
    """Test cases for ConnectionInfo dataclass."""
    
    def test_connection_info_creation(self):
        """Test connection info creation."""
        info = ConnectionInfo(
            name="test_server",
            connection_type="stdio",
            status="connected"
        )
        
        assert info.name == "test_server"
        assert info.connection_type == "stdio"
        assert info.status == "connected"
        assert info.connected_at is None
        assert info.last_activity is None


if __name__ == "__main__":
    pytest.main([__file__])
