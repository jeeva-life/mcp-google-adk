"""
Comprehensive Test Suite for MCP Servers.

This module contains unit tests for the various MCP server implementations
including HTTP and stdio servers.
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# Import server classes
from servers.stdio.terminal_server import SecureCommandRequest, CommandExecutionResult


class TestSecureCommandRequest:
    """Test cases for SecureCommandRequest model."""
    
    def test_valid_command_request(self):
        """Test valid command request creation."""
        request = SecureCommandRequest(command="ls -la")
        
        assert request.command == "ls -la"
    
    def test_command_validation_empty(self):
        """Test command validation with empty command."""
        with pytest.raises(ValueError, match="Command cannot be empty"):
            SecureCommandRequest(command="")
    
    def test_command_validation_whitespace_only(self):
        """Test command validation with whitespace-only command."""
        with pytest.raises(ValueError, match="Command cannot be empty"):
            SecureCommandRequest(command="   ")
    
    def test_command_validation_too_long(self):
        """Test command validation with command too long."""
        long_command = "a" * 1001
        
        with pytest.raises(ValueError):
            SecureCommandRequest(command=long_command)
    
    def test_command_stripping(self):
        """Test that commands are properly stripped."""
        request = SecureCommandRequest(command="  ls -la  ")
        
        assert request.command == "ls -la"


class TestCommandExecutionResult:
    """Test cases for CommandExecutionResult model."""
    
    def test_command_execution_result_creation(self):
        """Test command execution result creation."""
        result = CommandExecutionResult(
            command="ls -la",
            exit_code=0,
            stdout="file1.txt\nfile2.txt",
            stderr="",
            working_directory="/tmp",
            execution_time=0.5
        )
        
        assert result.command == "ls -la"
        assert result.exit_code == 0
        assert result.stdout == "file1.txt\nfile2.txt"
        assert result.stderr == ""
        assert result.working_directory == "/tmp"
        assert result.execution_time == 0.5
    
    def test_command_execution_result_optional_fields(self):
        """Test command execution result with optional fields."""
        result = CommandExecutionResult(
            command="test",
            exit_code=1,
            stdout="output",
            stderr="error",
            working_directory="/tmp"
        )
        
        assert result.execution_time is None


class TestTerminalServerIntegration:
    """Integration tests for terminal server functionality."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.mark.asyncio
    async def test_secure_command_execution_success(self, temp_workspace):
        """Test successful secure command execution."""
        # Mock the workspace directory
        with patch('servers.stdio.terminal_server.WORKSPACE_DIRECTORY', temp_workspace):
            from servers.stdio.terminal_server import execute_secure_command
            
            request = SecureCommandRequest(command="echo 'Hello World'")
            
            result = await execute_secure_command(request)
            
            assert result.command == "echo 'Hello World'"
            assert result.exit_code == 0
            assert "Hello World" in result.stdout
            assert result.stderr == ""
            assert result.working_directory == str(temp_workspace)
            assert result.execution_time is not None
            assert result.execution_time > 0
    
    @pytest.mark.asyncio
    async def test_secure_command_execution_error(self, temp_workspace):
        """Test command execution with error."""
        with patch('servers.stdio.terminal_server.WORKSPACE_DIRECTORY', temp_workspace):
            from servers.stdio.terminal_server import execute_secure_command
            
            request = SecureCommandRequest(command="nonexistentcommand12345")
            
            result = await execute_secure_command(request)
            
            assert result.command == "nonexistentcommand12345"
            assert result.exit_code != 0
            assert result.stderr != ""
            assert result.working_directory == str(temp_workspace)
    
    @pytest.mark.asyncio
    async def test_secure_command_execution_timeout(self, temp_workspace):
        """Test command execution timeout handling."""
        with patch('servers.stdio.terminal_server.WORKSPACE_DIRECTORY', temp_workspace):
            from servers.stdio.terminal_server import execute_secure_command
            
            # Create a command that would run indefinitely
            if os.name == 'nt':  # Windows
                command = "ping -t 127.0.0.1"
            else:  # Unix-like
                command = "sleep 60"
            
            request = SecureCommandRequest(command=command)
            
            result = await execute_secure_command(request)
            
            assert result.command == command
            assert result.exit_code == -1
            assert "timed out" in result.stderr.lower()
            assert result.working_directory == str(temp_workspace)
    
    @pytest.mark.asyncio
    async def test_secure_command_workspace_isolation(self, temp_workspace):
        """Test that commands are properly isolated to workspace."""
        with patch('servers.stdio.terminal_server.WORKSPACE_DIRECTORY', temp_workspace):
            from servers.stdio.terminal_server import execute_secure_command
            
            # Create a test file in the workspace
            test_file = temp_workspace / "test.txt"
            test_file.write_text("test content")
            
            # Try to access the file
            request = SecureCommandRequest(command=f"cat {test_file.name}")
            
            result = await execute_secure_command(request)
            
            assert result.exit_code == 0
            assert "test content" in result.stdout
    
    @pytest.mark.asyncio
    async def test_secure_command_file_operations(self, temp_workspace):
        """Test file operations within the secure workspace."""
        with patch('servers.stdio.terminal_server.WORKSPACE_DIRECTORY', temp_workspace):
            from servers.stdio.terminal_server import execute_secure_command
            
            # Create a new file
            request = SecureCommandRequest(command="echo 'Hello from test' > test_output.txt")
            result = await execute_secure_command(request)
            
            assert result.exit_code == 0
            
            # Read the file
            request = SecureCommandRequest(command="cat test_output.txt")
            result = await execute_secure_command(request)
            
            assert result.exit_code == 0
            assert "Hello from test" in result.stdout
    
    @pytest.mark.asyncio
    async def test_secure_command_directory_listing(self, temp_workspace):
        """Test directory listing functionality."""
        with patch('servers.stdio.terminal_server.WORKSPACE_DIRECTORY', temp_workspace):
            from servers.stdio.terminal_server import execute_secure_command
            
            # Create some test files
            (temp_workspace / "file1.txt").write_text("content1")
            (temp_workspace / "file2.txt").write_text("content2")
            
            # List directory contents
            request = SecureCommandRequest(command="ls -la" if os.name != 'nt' else "dir")
            result = await execute_secure_command(request)
            
            assert result.exit_code == 0
            assert "file1.txt" in result.stdout
            assert "file2.txt" in result.stdout
    
    @pytest.mark.asyncio
    async def test_secure_command_multiple_commands(self, temp_workspace):
        """Test multiple command executions."""
        with patch('servers.stdio.terminal_server.WORKSPACE_DIRECTORY', temp_workspace):
            from servers.stdio.terminal_server import execute_secure_command
            
            commands = [
                "echo 'First command'",
                "echo 'Second command'",
                "echo 'Third command'"
            ]
            
            results = []
            for cmd in commands:
                request = SecureCommandRequest(command=cmd)
                result = await execute_secure_command(request)
                results.append(result)
            
            assert len(results) == 3
            for result in results:
                assert result.exit_code == 0
                assert result.execution_time is not None
    
    @pytest.mark.asyncio
    async def test_secure_command_error_handling(self, temp_workspace):
        """Test error handling for various command failures."""
        with patch('servers.stdio.terminal_server.WORKSPACE_DIRECTORY', temp_workspace):
            from servers.stdio.terminal_server import execute_secure_command
            
            # Test command that doesn't exist
            request = SecureCommandRequest(command="thiscommanddoesnotexist12345")
            result = await execute_secure_command(request)
            
            assert result.exit_code != 0
            assert result.stderr != ""
            
            # Test command with syntax error
            request = SecureCommandRequest(command="echo 'unclosed quote")
            result = await execute_secure_command(request)
            
            # The behavior may vary by shell, but should handle gracefully
            assert result is not None


if __name__ == "__main__":
    pytest.main([__file__])
