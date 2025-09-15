"""
Launcher for HTTP MCP servers
Provide utilities to start and manage HTTP MCP servers with health monitoring.
"""

import subprocess
import sys
import time
import requests
import logging
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class ServerLauncher:
    """Manages HTTP MCP server lifecycle with health monitoring"""

    def __init__(self):
        self.processes: List[subprocess.Popen] = [] # Keeps a list of server processes it has started.

    def start_temperature_server(self, host: str = "localhost", port: int = 8000) -> bool:
        """Start the temperature conversion server with health monitoring"""

        try:
            server_path = Path(__file__).parent/"temperature_server.py"

            cmd = [
                sys.executable,
                str(server_path),
                "--host", host,
                "--port", str(port),
                "--log-level", "INFO"
            ]

            logger.info(f"Starting temperature server on {host}:{port}")
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            self.processes.append(process)

            # wait for server to be ready and verify health
            return self._wait_for_server(host, port)

        except Exception as e:
            logger.error(f"Failed to start temperature server: {str(e)}")
            return False

    def _wait_for_server(self, host: str, port: int, timeout: int = 10) -> bool:
        """
        wait for server to become available with health checking"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # try to connect to the MCP endpoint
                # we expect a 406 "not acceptable" response for stateless HTTP
                # but needs proper MCP headers (this confirms the MCP server is active)
                response = requests.get(url, timeout=5)
                if response.status_code == 406: # MCP server expects proper headers
                    logger.info(f"Temperature server at {host}:{port} is ready")
                    return True
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Failed to connect to temperature server: {str(e)}")
                    pass
            time.sleep(1)
        logger.warning(f"server at {host}:{port} did not respond in time")
        return False

    def stop_all_servers(self) -> None:
        """Stop all running servers"""
        for process in self.processes:
            try:
                process.terminate() # send termination signal
                process.wait(timeout=5) # wait for process to terminate gracefully
                logger.info(f"Stopped temperature server process")
            except Exception as e:
                logger.error(f"Failed to stop temperature server: {str(e)}")
                try:
                    process.kill() # force kill if needed or shutdown failed
                except:
                    pass
        self.processes.clear()

# Global launcher instance
launcher = ServerLauncher()