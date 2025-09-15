"""
The ConfigLoader class handles loading this configuration with smart path resolution. It checks multiple locations to find your config file and validates each server configuration to catch any issues early.
"""

import json
import os
from pathlib import Path
import logging
from typing import Dict, Any
from dotenv import load_dotenv

# load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class ConfigLoader:
    """Loads and validates MCP server configurations from multiple sources"""

    def __init__(self, config_path: str = None):
        """Initialize the config loader with optional config path"""
        self.config_path = self._resolve_config_path(config_path)
        self.config_cache = None

    def _resolve_config_path(self, config_path: str = None) -> Path:
        """Resolve the config file path with fallbacks"""
        if config_path:
            return Path(config_path)
        
        # Try Environment variable
        env_path = os.getenv("MCP_CONFIG_PATH")
        if env_path:
            return Path(env_path)
        
        # Try project root for default config
        project_root = Path(__file__).parent.parent
        return project_root / "config" / "servers.json"
    
    def load_config(self) -> Dict[str, Any]:
        """Load and validate the configuration from the resolved path"""
        if self.config_cache is not None:
            return self.config_cache

        try:
            if not self.config_path.exists():
                raise FileNotFoundError(f"Config file not found at {self.config_path}")
            
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config_cache = json.load(f)

            logger.info(f"Loaded MCP server configurations from {self.config_path}")
            return self.config_cache

        except Exception as e:
            logger.error(f"Failed to load MCP server configurations: {str(e)}")
            raise

    def get_servers(self) -> Dict[str, Dict[str, Any]]:
        """Get all MCP servers from the configuration"""
        config = self.load_config()
        return config.get("mcpservers", {})

    def validate_server_config(self, server_name: str, server_config: Dict[str, Any]) -> bool:
        """Validate the configuration for a specific server"""
        required_fields = ["type", "url", "command", "description"]
        missing_fields = [field for field in required_fields if field not in server_config]
        if missing_fields:
            logger.warning(f"Server {server_name} is missing required fields: {missing_fields}")
            return False
        
        if server_config["type"] == "http":
            if "url" not in server_config:
                logger.warning(f"Server {server_name} is missing required field: url")
                return False
        elif server_config["type"] == "stdio":
            if "command" not in server_config:
                logger.warning(f"Server {server_name} is missing required field: command")
                return False
        else:
            logger.error(f"Stdio server '{server_name}' has an invalid type: {server_config['type']}")
            return False
        
        return True
    
# Global config loader instance
config_loader = ConfigLoader()