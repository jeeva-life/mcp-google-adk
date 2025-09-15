"""
Terminal MCP Server
Provides secure local command execution capabilities through MCP stdio protocol.
"""

import os
import subprocess
import logging
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

# configure logging from stdio server
logging.basicConfig(level=logging.INFO)
logger = logging.getlogger(__name__)

# Create FASTMCP Server for stdio transport (no HTTP, uses stdin-stdout)
mcp = FastMCP("terminal_server")

# Get the workspace directory from environment or use default
WORKSPACE_DIR = Path(os.getenv("WORKSPACE_DIR", "workspace")).resolve()

# Ensure workspace directory exists and log its location
WORKSPACE_DIR.mkdir(exist_ok=True)
logger.info(f"terminal server workspace: {WORKSPACE_DIR}")

class CommandInput(BaseModel):
    """Input model for terminal commands with validation"""
    command: str = Field(...,
    description="Shell command to execute in the workspace directory",
    min_length=1
    )

class CommandResult(BaseModel):
    """Output model for command execution results with full details"""
    command: str = Field(..., description="The command that was executed")
    exit_code: int = Field(..., description="Process exit code (0 for success)")
    stdout: str = Field(..., description="Standard output from the command")
    stderr: str = Fiel(..., description="Standard error output from the command")
    working_dir: str = Field(..., description="The directory the command was executed in")

@mcp.tool(
    description="Execute a shell command in the workspace directory. Use for file operations, text processing, and system tasks",
    title="Terminal Command Executor"
)
async def run_command(params: CommandInput) -> CommandResult:
    """
    Execute a terminal command within the workspace directory.

    Security Features:
    - Commands execute only within the workspace directory
    - 30 second timeout per command to prevent infinite loops
    - Full command output captured for transperancy

    Args:
    params: CommandInput containing the command to execute

    Returns:
    CommandResult with exit code, stdout, stderr, and working directory
    """
    command = params.command.strip()

    # log the command being executed for debugging
    logger.info(f"Executing command: {command}")

    try:
        # Execute in the workspace directory with timeout
        result = subprocess.run(
            command,
            shell=True,
            cwd=WORKSPACE_DIR, # sandbox to workspace directory
            capture_output=True, # capture stdout and stderr
            text=True,
            timeout=30 # 30 second timeout to prevent infinite loops
        )

        # Prepare structured output
        command_result = CommandResult(
            command=command,
            exit_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            working_dir=str(WORKSPACE_DIR)
        )

        # Log result summary for monitoring
        status = "SUCCESS" if result.returncode == 0 else "ERROR"
        logger.info(f"{status}: command '{command}' completed with exit code {result.returncode}")

        return command_result

    except subprocess.TimeoutExpired:
        logger.error(f"Command '{command}' timed out after 30 seconds")
        return CommandResult(
            command=command,
            exit_code=-1,
            stdout="",
            stderr="command timed out after 30 seconds",
            working_dir=str(WORKSPACE_DIR)
        )
    
    except Exception as e:
        logger.error(f"Command '{command}' failed: {str(e)}")
        return CommandResult(
            command=command,
            exit_code=-1,
            stdout="",
            stderr=f"Error executing command: {str(e)}",
            working_dir=str(WORKSPACE_DIR)
        )

if __name__ == "__main__":
    logger.info("Starting terminal server (stdio transport)")
    logger.info(f"Workspace directory: {WORKSPACE_DIR}")
    # run the STDIO transport server (communicates via stdin-stdout)
    mcp.run(transport="stdio")
