"""
Configuration Management System for MCP Servers.

This module provides a robust configuration loader that handles MCP server
configurations with intelligent path resolution and comprehensive validation.
"""

import json
import os
from pathlib import Path
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class ServerConfigValidation:
    """Validation result for server configuration."""
    is_valid: bool
    missing_fields: List[str]
    invalid_fields: List[str]
    error_message: Optional[str] = None


class MCPConfigurationManager:
    """Advanced configuration manager for MCP server settings."""

    def __init__(self, config_file_path: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_file_path: Optional custom path to configuration file
        """
        self.config_file_path = self._determine_config_location(config_file_path)
        self._configuration_cache: Optional[Dict[str, Any]] = None
        self.logger = logging.getLogger(self.__class__.__name__)

    def _determine_config_location(self, custom_path: Optional[str] = None) -> Path:
        """Determine the location of the configuration file with fallback options."""
        if custom_path:
            return Path(custom_path)
        
        # Check environment variable
        env_config_path = os.getenv("MCP_CONFIG_PATH")
        if env_config_path:
            return Path(env_config_path)
        
        # Default to project config directory
        project_root = Path(__file__).parent.parent.parent
        return project_root / "config" / "servers.json"
    
    def load_configuration(self) -> Dict[str, Any]:
        """Load and cache the configuration from the determined path."""
        if self._configuration_cache is not None:
            return self._configuration_cache

        try:
            if not self.config_file_path.exists():
                raise FileNotFoundError(f"Configuration file not found at {self.config_file_path}")
            
            with open(self.config_file_path, "r", encoding="utf-8") as config_file:
                self._configuration_cache = json.load(config_file)

            self.logger.info(f"Successfully loaded MCP server configurations from {self.config_file_path}")
            return self._configuration_cache

        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in configuration file: {str(e)}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"Failed to load MCP server configurations: {str(e)}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)

    def get_server_configurations(self) -> Dict[str, Dict[str, Any]]:
        """Retrieve all MCP server configurations from the loaded config."""
        configuration = self.load_configuration()
        return configuration.get("mcpservers", {})

    def validate_server_configuration(self, server_name: str, server_config: Dict[str, Any]) -> ServerConfigValidation:
        """
        Validate the configuration for a specific MCP server.
        
        Args:
            server_name: Name of the server being validated
            server_config: Server configuration dictionary
            
        Returns:
            ServerConfigValidation object with validation results
        """
        missing_fields = []
        invalid_fields = []
        
        # Check for required base fields
        base_required_fields = ["type", "description"]
        for field in base_required_fields:
            if field not in server_config:
                missing_fields.append(field)
        
        # Validate server type
        server_type = server_config.get("type")
        if server_type not in ["http", "stdio"]:
            invalid_fields.append(f"type: '{server_type}' is not supported")
        
        # Type-specific validation
        if server_type == "http":
            if "url" not in server_config:
                missing_fields.append("url")
        elif server_type == "stdio":
            if "command" not in server_config:
                missing_fields.append("command")
        
        # Determine overall validation result
        is_valid = len(missing_fields) == 0 and len(invalid_fields) == 0
        
        if not is_valid:
            error_message = f"Server '{server_name}' configuration invalid"
            if missing_fields:
                error_message += f" - Missing fields: {missing_fields}"
            if invalid_fields:
                error_message += f" - Invalid fields: {invalid_fields}"
            self.logger.warning(error_message)
        else:
            self.logger.debug(f"Server '{server_name}' configuration is valid")
        
        return ServerConfigValidation(
            is_valid=is_valid,
            missing_fields=missing_fields,
            invalid_fields=invalid_fields,
            error_message=error_message if not is_valid else None
        )

    def reload_configuration(self) -> Dict[str, Any]:
        """Force reload the configuration file, bypassing cache."""
        self._configuration_cache = None
        return self.load_configuration()

    def get_configuration_value(self, key_path: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path to the configuration value
            default: Default value if key is not found
            
        Returns:
            Configuration value or default
        """
        try:
            configuration = self.load_configuration()
            keys = key_path.split('.')
            value = configuration
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
            
            return value
            
        except Exception as e:
            self.logger.warning(f"Error accessing configuration key '{key_path}': {e}")
            return default


# Global configuration manager instance
config_loader = MCPConfigurationManager()