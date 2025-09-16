"""
Advanced MCP Communication Interface.

This module provides a sophisticated client interface for managing Model Context Protocol
interactions with comprehensive debugging capabilities and session management.
"""

import logging
import asyncio
from typing import Optional, List, AsyncGenerator, Any, Dict
from dataclasses import dataclass
from google.genai.types import Content, Part
from google.adk import Runner
from google.adk.sessions import InMemorySessionService

from src.agent.agent_wrapper import MCPAgentOrchestrator
from src.utils.formatters import formatter

logger = logging.getLogger(__name__)


@dataclass
class ClientSessionInfo:
    """Information about the client session."""
    app_identifier: str
    user_identifier: str
    session_identifier: str
    debug_enabled: bool = False


class AdvancedMCPCommunicationInterface:
    """
    Sophisticated MCP communication interface with advanced session management.
    
    This interface provides comprehensive interaction capabilities with Model Context Protocol
    servers, featuring real-time streaming, detailed debugging, and robust session handling.
    """
    
    def __init__(
        self,
        application_name: str = "universal_mcp_interface",
        user_identifier: str = "default_user",
        session_identifier: str = "default_session",
        allowed_tools: Optional[List[str]] = None,
        verbose_debugging: bool = False
    ):
        """
        Initialize the advanced MCP communication interface.
        
        Args:
            application_name: Application identifier for ADK framework
            user_identifier: Unique user identifier for session context
            session_identifier: Session identifier for conversation tracking
            allowed_tools: Optional list of permitted tool names
            verbose_debugging: Enable comprehensive debugging of MCP interactions
        """
        self.session_info = ClientSessionInfo(
            app_identifier=application_name,
            user_identifier=user_identifier,
            session_identifier=session_identifier,
            debug_enabled=verbose_debugging
        )
        
        # Initialize core communication components
        self.session_manager = InMemorySessionService()
        self.agent_orchestrator = MCPAgentOrchestrator(tool_allowlist=allowed_tools)
        self.execution_runner: Optional[Runner] = None
        
        # State management
        self.initialization_complete = False
        
        logger.info(f"Advanced MCP Interface initialized for user '{user_identifier}', session '{session_identifier}'")
        if verbose_debugging:
            logger.info("Verbose debugging enabled - comprehensive MCP interaction details will be displayed")
    
    async def establish_communication_session(self) -> None:
        """
        Establish the communication session and initialize the agent system.
        
        This method must be called before using process_user_input().
        It configures the session, initializes the agent, and prepares the execution runner.
        """
        if self.initialization_complete:
            logger.warning("Communication interface already initialized")
            return
        
        try:
            logger.info("Establishing MCP communication session...")
            
            # Create ADK framework session
            await self.session_manager.create_session(
                app_name=self.session_info.app_identifier,
                user_id=self.session_info.user_identifier,
                session_id=self.session_info.session_identifier
            )
            logger.debug("ADK framework session established")
            
            # Initialize agent orchestrator with all MCP toolsets
            await self.agent_orchestrator.initialize_agent()
            
            if not self.agent_orchestrator.is_initialized():
                raise RuntimeError("Agent orchestrator failed to initialize properly")
            
            # Create execution runner for agent processing
            self.execution_runner = Runner(
                agent=self.agent_orchestrator.ai_agent,
                app_name=self.session_info.app_identifier,
                session_service=self.session_manager
            )
            
            self.initialization_complete = True
            logger.info("MCP communication interface initialized successfully")
            
            # Display server connection status summary
            connection_status = self.agent_orchestrator.get_connection_status()
            active_connections = sum(1 for s in connection_status.values() if s.status == "connected")
            logger.info(f"Server connection status: {active_connections}/{len(connection_status)} servers active")
            
        except Exception as e:
            logger.error(f"Failed to establish MCP communication session: {e}")
            await self.terminate_session()
            raise

    async def process_user_input(self, user_input: str) -> AsyncGenerator[Any, None]:
        """
        Process user input and stream the agent's response with comprehensive debugging.
        
        Args:
            user_input: User input message to process
            
        Yields:
            Streaming response events from the agent with detailed MCP interaction information
            
        Raises:
            RuntimeError: If communication interface is not initialized
        """
        if not self.initialization_complete:
            raise RuntimeError("Communication interface not initialized. Call establish_communication_session() first.")
        
        if not user_input.strip():
            raise ValueError("User input cannot be empty")
        
        logger.info(f"Processing user input: {user_input[:100]}{'...' if len(user_input) > 100 else ''}")
        
        try:
            # Create content structure for ADK framework
            content_structure = Content(
                role="user",
                parts=[Part(text=user_input)]
            )
            
            event_sequence = 0
            # Process through agent and yield streaming responses with debugging
            async for response_event in self.execution_runner.run_async(
                user_id=self.session_info.user_identifier,
                session_id=self.session_info.session_identifier,
                new_message=content_structure
            ):
                event_sequence += 1
                
                # Display comprehensive debugging information
                if self.session_info.debug_enabled:
                    # Create a formatted output object for the response event
                    formatted_output = formatter.create_success_response(
                        data=response_event,
                        message=f"Event #{event_sequence}"
                    )
                    print(formatter.format_to_json(formatted_output))
                    self._examine_response_event(response_event, event_sequence)
                
                yield response_event
                
        except Exception as e:
            logger.error(f"Error processing user input: {e}")
            raise

    def _examine_response_event(self, response_event: Any, event_sequence: int) -> None:
        """
        Examine and display comprehensive information about MCP response events.
        
        Args:
            response_event: The response event object from the agent
            event_sequence: Sequential event number for tracking
        """
        try:
            # Examine tool-related events
            if hasattr(response_event, 'tool_calls') and response_event.tool_calls:
                for tool_invocation in response_event.tool_calls:
                    tool_name = tool_invocation.name if hasattr(tool_invocation, 'name') else "Unknown"
                    formatter.print_tool_summary(
                        "tool_invocation",
                        [tool_name]
                    )
                    logger.debug(f"Tool invocation: {tool_name}")
            
            # Examine tool response events
            if hasattr(response_event, 'tool_responses') and response_event.tool_responses:
                for tool_result in response_event.tool_responses:
                    tool_name = getattr(tool_result, 'name', 'Unknown')
                    execution_status = "success" if not hasattr(tool_result, 'error') else "error"
                    logger.debug(f"Tool execution result: {tool_name} - {execution_status}")
            
            # Examine agent processing events
            if hasattr(response_event, 'content') and hasattr(response_event.content, 'parts'):
                if response_event.content.parts and not getattr(response_event, 'is_final_response', lambda: False)():
                    processing_content = response_event.content.parts[0].text if response_event.content.parts else "Processing..."
                    logger.debug(f"Agent processing: {processing_content[:100]}...")
            
            # Examine final response events
            if hasattr(response_event, 'is_final_response') and response_event.is_final_response():
                final_content = ""
                if hasattr(response_event, 'content') and hasattr(response_event.content, 'parts') and response_event.content.parts:
                    final_content = response_event.content.parts[0].text
                
                logger.info(f"Final agent response: {final_content[:200]}{'...' if len(final_content) > 200 else ''}")
                
        except Exception as e:
            logger.debug(f"Error examining response event {event_sequence}: {e}")

    def toggle_verbose_debugging(self) -> bool:
        """Toggle verbose debugging mode on/off and return new state."""
        self.session_info.debug_enabled = not self.session_info.debug_enabled
        logger.info(f"Verbose debugging {'enabled' if self.session_info.debug_enabled else 'disabled'}")
        return self.session_info.debug_enabled

    async def terminate_session(self) -> None:
        """
        Gracefully terminate the communication session and cleanup all resources.
        """
        logger.info("Terminating MCP communication session...")
        
        try:
            if self.agent_orchestrator:
                await self.agent_orchestrator.shutdown()
            
            # Reset state
            self.execution_runner = None
            self.initialization_complete = False
            
            logger.info("MCP communication session terminated successfully")
            
        except Exception as e:
            logger.error(f"Error during session termination: {e}")

    def get_interface_status(self) -> Dict[str, Any]:
        """
        Get comprehensive interface status information.
        
        Returns:
            Dictionary with detailed interface status information
        """
        status = {
            "initialization_complete": self.initialization_complete,
            "verbose_debugging": self.session_info.debug_enabled,
            "application_name": self.session_info.app_identifier,
            "user_identifier": self.session_info.user_identifier,
            "session_identifier": self.session_info.session_identifier,
            "agent_ready": self.agent_orchestrator.is_initialized() if self.agent_orchestrator else False,
            "server_connection_status": self.agent_orchestrator.get_connection_status() if self.agent_orchestrator else {}
        }
        
        return status
