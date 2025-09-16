"""
Advanced Command Line Interface for MCP Communication.

This module provides a sophisticated command-line interface for interacting with
Model Context Protocol servers with comprehensive debugging and session management.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.client.mcp_client import AdvancedMCPCommunicationInterface
from src.utils.formatters import formatter
from servers.http.server_launcher import launcher

# Tool configuration
PERMITTED_TOOLS = [
    'celsius_to_fahrenheit',
    'fahrenheit_to_celsius', 
    'celsius_to_kelvin',
    'kelvin_to_celsius',
    'fahrenheit_to_kelvin',
    'kelvin_to_fahrenheit',
    'run_command'
]

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("mcp_interface.log")
    ]
)

# Reduce external library verbosity
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("google").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


@dataclass
class InterfaceConfiguration:
    """Configuration settings for the CLI interface."""
    application_name: str = "universal_mcp_interface"
    user_identifier: str = "cli_user_001"
    session_identifier: str = "cli_session_001"
    verbose_debugging: bool = True
    permitted_tools: List[str] = None
    
    def __post_init__(self):
        if self.permitted_tools is None:
            self.permitted_tools = PERMITTED_TOOLS

class AdvancedMCPCommandLineInterface:
    """Sophisticated CLI for MCP communication with comprehensive debugging and server management."""
    
    def __init__(self):
        self.communication_interface: Optional[AdvancedMCPCommunicationInterface] = None
        self.http_servers_active = False
        self.interface_config = InterfaceConfiguration()
    
    async def activate_http_servers(self) -> bool:
        """Activate required HTTP servers with comprehensive health monitoring."""
        try:
            logger.info("Activating HTTP server infrastructure...")
            
            # Activate temperature conversion server
            if launcher.start_temperature_server(port=8001):
                self.http_servers_active = True
                logger.info("Temperature conversion server activated successfully")
                return True
            else:
                logger.error("Failed to activate temperature conversion server")
                return False
                
        except Exception as e:
            logger.error(f"Error activating server infrastructure: {e}")
            return False
    
    async def establish_communication_interface(self) -> bool:
        """Establish the MCP communication interface with comprehensive debugging."""
        try:
            logger.info("Establishing MCP communication interface...")
            
            self.communication_interface = AdvancedMCPCommunicationInterface(
                application_name=self.interface_config.application_name,
                user_identifier=self.interface_config.user_identifier,
                session_identifier=self.interface_config.session_identifier,
                allowed_tools=self.interface_config.permitted_tools,
                verbose_debugging=self.interface_config.verbose_debugging
            )
            
            await self.communication_interface.establish_communication_session()
            logger.info("MCP communication interface established")
            return True
            
        except Exception as e:
            logger.error(f"Failed to establish communication interface: {e}")
            formatter.create_error_response("Interface establishment failed", str(e))
            return False
    
    async def interactive_communication_session(self) -> None:
        """Main interactive communication session with comprehensive debugging."""
        self._display_welcome_message()
        
        print("\nCommunication session initiated. Available commands:")
        print("  - Enter your requests in natural language")
        print("  - 'status' - Display system status information")
        print("  - 'debug on/off' - Toggle verbose debugging mode") 
        print("  - 'help' - Display example requests and usage tips")
        print("  - 'quit', 'exit', ':q' - Terminate the application\n")
        
        try:
            while True:
                try:
                    # Capture user input
                    user_input = input("You: ").strip()
                    
                    if not user_input:
                        continue
                    
                    # Process special commands
                    if user_input.lower() in ['quit', 'exit', ':q']:
                        print("Session terminated. Goodbye!")
                        break
                    elif user_input.lower() == 'status':
                        self._display_system_status()
                        continue
                    elif user_input.lower().startswith('debug'):
                        self._process_debug_command(user_input)
                        continue
                    elif user_input.lower() == 'help':
                        self._display_usage_help()
                        continue
                    
                    # Process user input through communication interface
                    await self._process_user_input(user_input)
                    
                except KeyboardInterrupt:
                    print("\n\nSession interrupted by user. Goodbye!")
                    break
                except EOFError:
                    print("\n\nInput stream ended. Goodbye!")
                    break
                except Exception as e:
                    logger.error(f"Error in communication session: {e}")
                    formatter.create_error_response("An error occurred", str(e))
                    
        except Exception as e:
            logger.error(f"Critical error in communication session: {e}")
            formatter.create_error_response("Critical error occurred", str(e))
    
    async def _process_user_input(self, user_input: str) -> None:
        """Process user input with comprehensive MCP interaction debugging."""
        event_sequence = 0
        final_agent_response = None
        
        try:
            print(f"\nAssistant: Processing your request...")
            if self.interface_config.verbose_debugging:
                print("[VERBOSE DEBUGGING] Displaying detailed MCP interactions:\n")
            
            async for response_event in self.communication_interface.process_user_input(user_input):
                event_sequence += 1
                
                # In verbose debugging mode, detailed interactions are displayed by the interface
                # Here we track event sequence and identify the final response
                if hasattr(response_event, 'is_final_response') and response_event.is_final_response():
                    final_agent_response = response_event
                    break
            
            # Display the final agent response
            if final_agent_response and hasattr(final_agent_response, 'content'):
                if hasattr(final_agent_response.content, 'parts') and final_agent_response.content.parts:
                    response_content = final_agent_response.content.parts[0].text
                    print(f"\nFinal Agent Response:\n{response_content}\n")
                else:
                    print("Task completed successfully (no text response)\n")
            else:
                print("No final response received from agent\n")
                
            if self.interface_config.verbose_debugging:
                print(f"Total events processed: {event_sequence}")
                
        except Exception as e:
            logger.error(f"Error processing user input: {e}")
            formatter.create_error_response("Failed to process user input", str(e))
    
    def _process_debug_command(self, command: str) -> None:
        """Process debug mode toggle commands."""
        command_parts = command.split()
        if len(command_parts) > 1:
            debug_mode = command_parts[1].lower()
            if debug_mode == 'on':
                self.interface_config.verbose_debugging = True
                if self.communication_interface:
                    self.communication_interface.toggle_verbose_debugging()
                print("Verbose debugging enabled - comprehensive MCP interactions will be displayed")
            elif debug_mode == 'off':
                self.interface_config.verbose_debugging = False
                if self.communication_interface:
                    self.communication_interface.toggle_verbose_debugging()
                print("Verbose debugging disabled - only final responses will be displayed")
            else:
                print("Usage: debug on/off")
        else:
            current_state = "enabled" if self.interface_config.verbose_debugging else "disabled"
            print(f"Verbose debugging is currently {current_state}")
    
    def _display_system_status(self) -> None:
        """Display current system status with comprehensive information."""
        if not self.communication_interface:
            print("Communication interface not established")
            return
        
        interface_status = self.communication_interface.get_interface_status()
        
        print("\nSystem Status:")
        print(f"  - Interface established: {'[OK]' if interface_status['initialization_complete'] else '[FAIL]'}")
        print(f"  - Agent ready: {'[OK]' if interface_status['agent_ready'] else '[FAIL]'}")
        print(f"  - Verbose debugging: {'ON' if interface_status['verbose_debugging'] else 'OFF'}")
        print(f"  - User: {interface_status['user_identifier']}")
        print(f"  - Session: {interface_status['session_identifier']}")
        
        print("\nServer Connection Status:")
        for server_name, server_status in interface_status['server_connection_status'].items():
            status_icon = "[OK]" if server_status.status == "connected" else "[FAIL]"
            print(f"  - {server_name}: {status_icon} {server_status.status}")
        print()
    
    def _display_usage_help(self) -> None:
        """Display example requests and debugging guidance."""
        example_requests = [
            "Convert 25 degrees Celsius to Fahrenheit",
            "What is 100°F in Celsius and Kelvin?", 
            "Convert 300 Kelvin to Celsius and Fahrenheit",
            "Convert 0°C to all other temperature scales",
            "Convert room temperature (20°C) to Fahrenheit and save to file",
            "Create a temperature conversion table for 0, 25, 50, 75, 100°C"
        ]
        
        debugging_guidance = [
            "Use 'debug on' to see comprehensive MCP server interactions",
            "Monitor tool invocations, parameters, and server responses",
            "Each event displays the communication between interface and servers",
            "Use 'debug off' to display only final responses"
        ]
        
        print("\nExample Requests:")
        for i, example in enumerate(example_requests, 1):
            print(f"  {i}. {example}")
        
        print("\nDebugging Guidance:")
        for i, tip in enumerate(debugging_guidance, 1):
            print(f"  {i}. {tip}")
        print()
    
    def _display_welcome_message(self) -> None:
        """Display welcome message for the communication session."""
        formatter.print_welcome_banner()

    async def terminate_session_and_cleanup(self) -> None:
        """Terminate session and cleanup all resources."""
        try:
            if self.communication_interface:
                await self.communication_interface.terminate_session()
            
            if self.http_servers_active:
                launcher.stop_all_servers()
                
        except Exception as e:
            logger.error(f"Error during session termination and cleanup: {e}")

async def main():
    """Main entry point for the advanced CLI application with comprehensive debugging."""
    cli_interface = AdvancedMCPCommandLineInterface()
    
    try:
        # Activate server infrastructure
        print("Initializing Advanced MCP Communication Interface with Verbose Debugging...")
        
        if not await cli_interface.activate_http_servers():
            print("Failed to activate required server infrastructure")
            return 1
        
        # Establish communication interface
        if not await cli_interface.establish_communication_interface():
            print("Failed to establish communication interface")
            return 1
        
        # Start interactive communication session with debugging
        await cli_interface.interactive_communication_session()
        
        return 0
        
    except KeyboardInterrupt:
        print("\nSession interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        formatter.create_error_response("Unexpected error occurred", str(e))
        return 1
    finally:
        await cli_interface.terminate_session_and_cleanup()

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except asyncio.CancelledError:
        # Suppress cancelled error messages during shutdown
        logger.debug("Main coroutine cancelled during shutdown")
        sys.exit(0)