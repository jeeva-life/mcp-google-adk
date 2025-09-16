"""
Advanced Output Formatting and Display Utilities.

This module provides comprehensive formatting capabilities for MCP server
responses, tool outputs, and system status information.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class OutputFormat(Enum):
    """Available output formats for displaying information."""
    JSON = "json"
    HUMAN_READABLE = "human_readable"
    TABLE = "table"
    LIST = "list"


@dataclass
class FormattedOutput:
    """Structured output format for consistent response handling."""
    success: bool
    data: Any
    message: Optional[str] = None
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AdvancedResponseFormatter:
    """
    Advanced formatter for MCP server responses and system outputs.
    
    This class provides multiple formatting options and utilities for
    displaying information in various formats suitable for different use cases.
    """
    
    def __init__(self):
        """Initialize the response formatter."""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def create_success_response(
        self,
        data: Any,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> FormattedOutput:
        """
        Create a formatted success response.
        
        Args:
            data: Response data
            message: Optional success message
            metadata: Optional metadata dictionary
            
        Returns:
            FormattedOutput: Formatted success response
        """
        return FormattedOutput(
            success=True,
            data=data,
            message=message or "Operation completed successfully",
            timestamp=datetime.utcnow().isoformat(),
            metadata=metadata or {}
        )
    
    def create_error_response(
        self,
        error: Union[str, Exception],
        error_code: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> FormattedOutput:
        """
        Create a formatted error response.
        
        Args:
            error: Error message or exception
            error_code: Optional error code
            metadata: Optional metadata dictionary
            
        Returns:
            FormattedOutput: Formatted error response
        """
        error_message = str(error) if isinstance(error, Exception) else error
        
        error_metadata = metadata or {}
        if error_code:
            error_metadata["error_code"] = error_code
        
        return FormattedOutput(
            success=False,
            data=None,
            message=f"Error: {error_message}",
            timestamp=datetime.utcnow().isoformat(),
            metadata=error_metadata
        )
    
    def create_tool_execution_result(
        self,
        tool_name: str,
        result: Any,
        execution_time: Optional[float] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> FormattedOutput:
        """
        Create a formatted tool execution result.
        
        Args:
            tool_name: Name of the executed tool
            result: Tool execution result
            execution_time: Time taken for execution
            parameters: Parameters used for execution
            
        Returns:
            FormattedOutput: Formatted tool result
        """
        metadata = {
            "tool_name": tool_name,
            "execution_time": execution_time
        }
        
        if parameters:
            metadata["parameters"] = parameters
        
        return self.create_success_response(
            data=result,
            message=f"Tool '{tool_name}' executed successfully",
            metadata=metadata
        )
    
    def format_to_json(self, output: FormattedOutput) -> str:
        """
        Convert a formatted output to JSON string.
        
        Args:
            output: Formatted output object
            
        Returns:
            str: JSON representation of the output
        """
        try:
            return json.dumps(asdict(output), indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Error converting output to JSON: {e}")
            return json.dumps({
                "success": False,
                "data": None,
                "message": f"JSON serialization error: {e}",
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": {}
            })
    
    def format_to_human_readable(self, output: FormattedOutput) -> str:
        """
        Convert a formatted output to human-readable format.
        
        Args:
            output: Formatted output object
            
        Returns:
            str: Human-readable representation of the output
        """
        lines = []
        
        # Status indicator
        status_icon = "✅ SUCCESS" if output.success else "❌ ERROR"
        lines.append(f"Status: {status_icon}")
        
        # Timestamp
        if output.timestamp:
            lines.append(f"Timestamp: {output.timestamp}")
        
        # Message
        if output.message:
            lines.append(f"Message: {output.message}")
        
        # Data section
        if output.data is not None:
            lines.append("Data:")
            if isinstance(output.data, (dict, list)):
                lines.append(json.dumps(output.data, indent=2))
            else:
                lines.append(str(output.data))
        
        # Metadata section
        if output.metadata:
            lines.append("Metadata:")
            lines.append(json.dumps(output.metadata, indent=2))
        
        return "\n".join(lines)
    
    def format_data_as_table(self, data: List[Dict[str, Any]], headers: Optional[List[str]] = None) -> str:
        """
        Format tabular data as a formatted table.
        
        Args:
            data: List of dictionaries to format as table
            headers: Optional list of column headers
            
        Returns:
            str: Formatted table string
        """
        if not data:
            return "No data available"
        
        # Determine headers
        if not headers:
            headers = list(data[0].keys()) if data else []
        
        # Calculate column widths
        column_widths = {}
        for header in headers:
            column_widths[header] = len(str(header))
        
        for row in data:
            for header in headers:
                value = str(row.get(header, ""))
                column_widths[header] = max(column_widths[header], len(value))
        
        # Build table
        table_lines = []
        
        # Header row
        header_row = " | ".join(header.ljust(column_widths[header]) for header in headers)
        table_lines.append(header_row)
        table_lines.append("-" * len(header_row))
        
        # Data rows
        for row in data:
            data_row = " | ".join(
                str(row.get(header, "")).ljust(column_widths[header])
                for header in headers
            )
            table_lines.append(data_row)
        
        return "\n".join(table_lines)
    
    def format_data_as_list(self, items: List[Any], title: Optional[str] = None) -> str:
        """
        Format a list of items in a structured list format.
        
        Args:
            items: List of items to format
            title: Optional title for the list
            
        Returns:
            str: Formatted list string
        """
        lines = []
        
        if title:
            lines.append(title)
            lines.append("=" * len(title))
        
        for i, item in enumerate(items, 1):
            lines.append(f"{i}. {item}")
        
        return "\n".join(lines)
    
    def print_welcome_banner(self) -> None:
        """Print a welcome banner for the application."""
        banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                    Advanced MCP Communication Interface                     ║
║                                                                              ║
║  Welcome to the Model Context Protocol (MCP) integration system!            ║
║  This interface provides comprehensive debugging and interaction            ║
║  capabilities with MCP servers and AI agents.                               ║
║                                                                              ║
║  Features:                                                                   ║
║  • Temperature conversion tools                                              ║
║  • Terminal command execution                                                ║
║  • Real-time MCP interaction debugging                                       ║
║  • Advanced session management                                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """
        print(banner)
    
    def print_tool_summary(self, server_name: str, tool_names: List[str]) -> None:
        """
        Print a summary of tools available from a server.
        
        Args:
            server_name: Name of the server
            tool_names: List of available tool names
        """
        summary = f"Server '{server_name}' provides {len(tool_names)} tools: {', '.join(tool_names)}"
        print(summary)
        self.logger.info(summary)
    
    def format_server_status(self, status_data: Dict[str, Any]) -> str:
        """
        Format server status information for display.
        
        Args:
            status_data: Dictionary containing server status information
            
        Returns:
            str: Formatted status string
        """
        lines = ["Server Status Summary:"]
        lines.append("-" * 30)
        
        for server_name, status_info in status_data.items():
            if isinstance(status_info, dict):
                status = status_info.get("status", "unknown")
                tool_count = status_info.get("tool_count", 0)
                lines.append(f"• {server_name}: {status} ({tool_count} tools)")
            else:
                lines.append(f"• {server_name}: {status_info}")
        
        return "\n".join(lines)


# Global formatter instance
formatter = AdvancedResponseFormatter()
