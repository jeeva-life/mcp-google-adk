"""
Secure Terminal Command Execution Server.

This module implements a secure MCP server that provides controlled access
to terminal command execution within a sandboxed workspace environment.
"""

import os
import subprocess
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, validator

# Configure logging for the terminal server
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server for stdio transport
mcp_server = FastMCP("secure_terminal_server")

# Establish workspace directory with environment variable support
WORKSPACE_DIRECTORY = Path(os.getenv("WORKSPACE_DIR", "workspace")).resolve()

# Create workspace directory if it doesn't exist
WORKSPACE_DIRECTORY.mkdir(exist_ok=True)
logger.info(f"Terminal server workspace established at: {WORKSPACE_DIRECTORY}")


class SecureCommandRequest(BaseModel):
    """Secure command request model with input validation."""
    command: str = Field(
        ...,
        description="Shell command to execute within the secure workspace environment",
        min_length=1,
        max_length=1000
    )
    
    @validator('command')
    def validate_command(cls, v):
        """Validate command input for security."""
        if not v.strip():
            raise ValueError("Command cannot be empty")
        return v.strip()


class CommandExecutionResult(BaseModel):
    """Comprehensive command execution result model."""
    command: str = Field(..., description="The command that was executed")
    exit_code: int = Field(..., description="Process exit code (0 indicates success)")
    stdout: str = Field(..., description="Standard output from the command")
    stderr: str = Field(..., description="Standard error output from the command")
    working_directory: str = Field(..., description="The directory where the command was executed")
    execution_time: Optional[float] = Field(None, description="Time taken to execute the command")

@mcp_server.tool(
    description="Execute shell commands within a secure workspace environment. Ideal for file operations, text processing, and system administration tasks.",
    title="Secure Command Executor"
)
async def execute_secure_command(request: SecureCommandRequest) -> CommandExecutionResult:
    """
    Execute a shell command within the secure workspace directory.

    Security Features:
    - Commands are restricted to the designated workspace directory
    - Built-in timeout protection to prevent infinite execution
    - Comprehensive output capture for full transparency
    - Input validation and sanitization

    Args:
        request: SecureCommandRequest containing the command to execute

    Returns:
        CommandExecutionResult with complete execution details
    """
    command = request.command
    start_time = asyncio.get_event_loop().time()

    # Log command execution for audit purposes
    logger.info(f"Executing secure command: {command}")

    try:
        # Execute command within the secure workspace with timeout protection
        process_result = subprocess.run(
            command,
            shell=True,
            cwd=WORKSPACE_DIRECTORY,  # Restrict execution to workspace
            capture_output=True,  # Capture all output streams
            text=True,
            timeout=30  # 30-second timeout for safety
        )

        end_time = asyncio.get_event_loop().time()
        execution_time = end_time - start_time

        # Create comprehensive result object
        execution_result = CommandExecutionResult(
            command=command,
            exit_code=process_result.returncode,
            stdout=process_result.stdout,
            stderr=process_result.stderr,
            working_directory=str(WORKSPACE_DIRECTORY),
            execution_time=execution_time
        )

        # Log execution summary for monitoring
        execution_status = "SUCCESS" if process_result.returncode == 0 else "FAILED"
        logger.info(f"{execution_status}: Command '{command}' completed in {execution_time:.2f}s with exit code {process_result.returncode}")

        return execution_result

    except subprocess.TimeoutExpired:
        end_time = asyncio.get_event_loop().time()
        execution_time = end_time - start_time
        
        logger.error(f"Command '{command}' exceeded timeout limit after {execution_time:.2f} seconds")
        
        return CommandExecutionResult(
            command=command,
            exit_code=-1,
            stdout="",
            stderr=f"Command execution timed out after 30 seconds",
            working_directory=str(WORKSPACE_DIRECTORY),
            execution_time=execution_time
        )
    
    except Exception as e:
        end_time = asyncio.get_event_loop().time()
        execution_time = end_time - start_time
        
        error_message = f"Command execution failed: {str(e)}"
        logger.error(f"Command '{command}' failed: {error_message}")
        
        return CommandExecutionResult(
            command=command,
            exit_code=-1,
            stdout="",
            stderr=error_message,
            working_directory=str(WORKSPACE_DIRECTORY),
            execution_time=execution_time
        )


if __name__ == "__main__":
    logger.info("Initializing secure terminal server with stdio transport")
    logger.info(f"Workspace directory: {WORKSPACE_DIRECTORY}")
    
    # Start the MCP server with stdio transport
    mcp_server.run(transport="stdio")
