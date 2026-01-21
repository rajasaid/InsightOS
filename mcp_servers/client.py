"""
mcp_servers/client.py
Real MCP Client - Communicates with MCP server subprocesses via stdio/JSON-RPC
"""

import subprocess
import json
import threading
import queue
from typing import Dict, Any, List, Optional
from pathlib import Path
import uuid

from mcp_servers import get_mcp_config
from utils.logger import get_logger

logger = get_logger(__name__)


class MCPClient:
    """
    Client for communicating with MCP servers via stdio
    
    This is REAL MCP - spawns server subprocesses and communicates
    via JSON-RPC over stdin/stdout
    """
    
    def __init__(self):
        """Initialize MCP client"""
        self.config = get_mcp_config()
        self.servers = {}  # server_name -> subprocess
        self.response_queues = {}  # request_id -> queue
        self.reader_threads = {}  # server_name -> thread
        
        logger.info("MCPClient initialized")
    
    def start_server(self, server_name: str) -> bool:
        """
        Start an MCP server subprocess via npx
        
        Args:
            server_name: Name of the server (filesystem, memory, brave-search)
            
        Returns:
            True if started successfully, False otherwise
        """
        if server_name in self.servers:
            logger.warning(f"Server {server_name} already running")
            return True
        
        enabled_servers = self.config.get_enabled_servers()
        
        if server_name not in enabled_servers:
            logger.error(f"Server {server_name} not enabled in config")
            return False
        
        try:
            # Start server based on type
            if server_name == "filesystem":
                process = self._start_filesystem_server()
            elif server_name == "memory":
                process = self._start_memory_server()
            elif server_name == "brave-search":
                process = self._start_brave_search_server()
            else:
                logger.error(f"Unknown server: {server_name}")
                return False
            
            # Process might be None for optional servers
            if process is None:
                logger.info(f"Server {server_name} not available (optional)")
                return False
            
            # Check if process started successfully
            try:
                # Give it a moment to fail if there's an immediate error
                import time
                time.sleep(0.5)
                
                if process.poll() is not None:
                    # Process already exited
                    stderr_output = process.stderr.read() if process.stderr else ""
                    logger.error(f"Server {server_name} failed to start: {stderr_output}")
                    return False
            except:
                pass
            
            self.servers[server_name] = process
            
            # Start reader thread for this server
            reader_thread = threading.Thread(
                target=self._read_server_output,
                args=(server_name, process),
                daemon=True
            )
            reader_thread.start()
            self.reader_threads[server_name] = reader_thread
            
            logger.info(f"✓ MCP server started: {server_name} (PID: {process.pid})")
            return True
        
        except FileNotFoundError as e:
            logger.error(f"npx not found. Please install Node.js: {e}")
            return False
        
        except Exception as e:
            logger.error(f"Failed to start MCP server {server_name}: {e}", exc_info=True)
            return False
    
    def _start_filesystem_server(self) -> subprocess.Popen:
        """
        Start filesystem MCP server using npx
        
        Returns:
            Subprocess instance
        """
        output_dir = self.config.get_output_dir()
        
        # Use official @modelcontextprotocol/server-filesystem
        # npx -y @modelcontextprotocol/server-filesystem <output_dir>
        process = subprocess.Popen(
            ["npx", "-y", "@modelcontextprotocol/server-filesystem", str(output_dir)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        logger.info(f"MCP filesystem server started via npx (output_dir: {output_dir})")
        
        return process
    
    def _start_memory_server(self) -> Optional[subprocess.Popen]:
        """
        Start memory MCP server using npx
        
        Returns:
            Subprocess instance or None if not available
        """
        try:
            # Use official @modelcontextprotocol/server-memory
            # npx -y @modelcontextprotocol/server-memory
            process = subprocess.Popen(
                ["npx", "-y", "@modelcontextprotocol/server-memory"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            logger.info("MCP memory server started via npx")
            return process
        
        except Exception as e:
            logger.warning(f"Memory server not available: {e}")
            return None
    
    def _start_brave_search_server(self) -> Optional[subprocess.Popen]:
        """
        Start Brave Search MCP server using npx
        
        Returns:
            Subprocess instance or None if not available
        """
        # Check if Brave Search API key is configured
        from security.config_manager import ConfigManager
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        brave_api_key = config.get('brave_search_api_key')
        
        if not brave_api_key:
            logger.warning("Brave Search API key not configured")
            return None
        
        try:
            # Use official @modelcontextprotocol/server-brave-search
            # Set API key via environment variable
            import os
            env = os.environ.copy()
            env['BRAVE_API_KEY'] = brave_api_key
            
            process = subprocess.Popen(
                ["npx", "-y", "@modelcontextprotocol/server-brave-search"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                env=env
            )
            
            logger.info("MCP Brave Search server started via npx")
            return process
        
        except Exception as e:
            logger.warning(f"Brave Search server not available: {e}")
            return None
    
    def _read_server_output(self, server_name: str, process: subprocess.Popen):
        """
        Read output from MCP server subprocess
        
        Args:
            server_name: Name of the server
            process: Subprocess instance
        """
        logger.info(f"Started reader thread for {server_name}")
        
        try:
            for line in process.stdout:
                if not line.strip():
                    continue
                
                try:
                    response = json.loads(line)
                    request_id = response.get("id")
                    
                    if request_id and request_id in self.response_queues:
                        self.response_queues[request_id].put(response)
                    else:
                        logger.warning(f"Received response with unknown ID: {request_id}")
                
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse server response: {line[:100]}")
        
        except Exception as e:
            logger.error(f"Error reading from {server_name}: {e}")
        
        logger.info(f"Reader thread for {server_name} stopped")
    
    def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an MCP tool
        
        Args:
            server_name: Name of the server
            tool_name: Name of the tool
            arguments: Tool arguments
            
        Returns:
            Tool result
        """
        if server_name not in self.servers:
            raise RuntimeError(f"Server {server_name} not running")
        
        process = self.servers[server_name]
        request_id = str(uuid.uuid4())
        
        # Create request
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        # Create response queue
        response_queue = queue.Queue()
        self.response_queues[request_id] = response_queue
        
        try:
            # Send request
            request_json = json.dumps(request) + "\n"
            process.stdin.write(request_json)
            process.stdin.flush()
            
            logger.debug(f"Sent MCP request: {tool_name}")
            
            # Wait for response (with timeout)
            try:
                response = response_queue.get(timeout=30)
                
                if "error" in response:
                    logger.error(f"MCP tool error: {response['error']}")
                    return {"success": False, "error": response["error"]}
                
                result = response.get("result", {})
                logger.debug(f"MCP tool response: {result}")
                
                return result
            
            except queue.Empty:
                logger.error(f"Timeout waiting for MCP response")
                return {"success": False, "error": "Timeout"}
        
        finally:
            # Clean up queue
            if request_id in self.response_queues:
                del self.response_queues[request_id]
    
    def list_tools(self, server_name: str) -> List[Dict[str, Any]]:
        """
        List tools available from an MCP server
        
        Args:
            server_name: Name of the server
            
        Returns:
            List of tool definitions
        """
        if server_name not in self.servers:
            return []
        
        process = self.servers[server_name]
        request_id = str(uuid.uuid4())
        
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/list"
        }
        
        response_queue = queue.Queue()
        self.response_queues[request_id] = response_queue
        
        try:
            request_json = json.dumps(request) + "\n"
            process.stdin.write(request_json)
            process.stdin.flush()
            
            response = response_queue.get(timeout=10)
            
            if "error" in response:
                logger.error(f"Error listing MCP tools: {response['error']}")
                return []
            
            tools = response.get("result", {}).get("tools", [])
            return tools
        
        except Exception as e:
            logger.error(f"Failed to list MCP tools: {e}")
            return []
        
        finally:
            if request_id in self.response_queues:
                del self.response_queues[request_id]
    
    def stop_server(self, server_name: str):
        """Stop an MCP server"""
        if server_name in self.servers:
            process = self.servers[server_name]
            process.terminate()
            process.wait(timeout=5)
            del self.servers[server_name]
            logger.info(f"Stopped MCP server: {server_name}")
    
    def stop_all_servers(self):
        """Stop all MCP servers"""
        for server_name in list(self.servers.keys()):
            self.stop_server(server_name)
    
    def __del__(self):
        """Cleanup on deletion"""
        self.stop_all_servers()


# Singleton instance
_mcp_client = None


def get_mcp_client() -> MCPClient:
    """
    Get singleton MCP client instance
    
    Returns:
        MCPClient instance
    """
    global _mcp_client
    
    if _mcp_client is None:
        _mcp_client = MCPClient()
    
    return _mcp_client