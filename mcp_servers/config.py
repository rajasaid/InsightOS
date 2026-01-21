"""
MCP Server Configuration for InsightOS
Manages connection to MCP servers with file writing capabilities
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class MCPServerConfig:
    """Configuration for a single MCP server"""
    name: str
    command: str
    args: List[str]
    env: Optional[Dict[str, str]] = None
    enabled: bool = True
    description: str = ""


class MCPConfig:
    """Manages MCP server configurations for InsightOS"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize MCP configuration
        
        Args:
            config_dir: Directory to store config files. Defaults to ~/.insightos/mcp/
        """
        if config_dir is None:
            config_dir = Path.home() / ".insightos" / "mcp"
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_file = self.config_dir / "servers.json"
        self.servers: Dict[str, MCPServerConfig] = {}
        
        # Create default output directory for generated files
        self.output_dir = Path.home() / "InsightOS" / "Generated"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self._load_config()
    
    def _get_default_servers(self) -> Dict[str, MCPServerConfig]:
        """Define default MCP servers for InsightOS"""
        return {
            "filesystem": MCPServerConfig(
                name="filesystem",
                command="npx",
                args=[
                    "-y",
                    "@modelcontextprotocol/server-filesystem",
                    str(self.output_dir)  # Restrict to Generated folder
                ],
                description="File system operations (read/write) restricted to InsightOS/Generated/"
            ),
            "memory": MCPServerConfig(
                name="memory",
                command="npx",
                args=[
                    "-y",
                    "@modelcontextprotocol/server-memory"
                ],
                description="Knowledge graph and entity memory system"
            ),
            "brave-search": MCPServerConfig(
                name="brave-search",
                command="npx",
                args=[
                    "-y",
                    "@modelcontextprotocol/server-brave-search"
                ],
                env={
                    "BRAVE_API_KEY": ""  # User needs to set this
                },
                enabled=False,  # Disabled by default until API key is set
                description="Web search via Brave Search API"
            )
        }
    
    def _load_config(self):
        """Load configuration from file or create default"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                
                for name, server_data in data.get("servers", {}).items():
                    self.servers[name] = MCPServerConfig(**server_data)
                
                print(f"Loaded {len(self.servers)} MCP server configurations")
            except Exception as e:
                print(f"Error loading config: {e}. Using defaults.")
                self.servers = self._get_default_servers()
                self._save_config()
        else:
            # First run - create default config
            self.servers = self._get_default_servers()
            self._save_config()
            print(f"Created default MCP configuration at {self.config_file}")
    
    def _save_config(self):
        """Save current configuration to file"""
        data = {
            "servers": {
                name: asdict(server)
                for name, server in self.servers.items()
            },
            "output_dir": str(self.output_dir),
            "last_updated": datetime.now().isoformat()
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_server(self, server: MCPServerConfig):
        """Add or update a server configuration"""
        self.servers[server.name] = server
        self._save_config()
    
    def remove_server(self, name: str):
        """Remove a server configuration"""
        if name in self.servers:
            del self.servers[name]
            self._save_config()
    
    def enable_server(self, name: str):
        """Enable a server"""
        if name in self.servers:
            self.servers[name].enabled = True
            self._save_config()
    
    def disable_server(self, name: str):
        """Disable a server"""
        if name in self.servers:
            self.servers[name].enabled = False
            self._save_config()
    
    def get_enabled_servers(self) -> Dict[str, MCPServerConfig]:
        """Get all enabled servers"""
        return {
            name: server
            for name, server in self.servers.items()
            if server.enabled
        }
    
    def get_server(self, name: str) -> Optional[MCPServerConfig]:
        """Get a specific server configuration"""
        return self.servers.get(name)
    
    def set_brave_api_key(self, api_key: str):
        """Set Brave Search API key and enable the server"""
        if "brave-search" in self.servers:
            if self.servers["brave-search"].env is None:
                self.servers["brave-search"].env = {}
            self.servers["brave-search"].env["BRAVE_API_KEY"] = api_key
            self.servers["brave-search"].enabled = True
            self._save_config()
    
    def get_output_dir(self) -> Path:
        """Get the directory where agent-generated files are saved"""
        return self.output_dir
    
    def set_output_dir(self, path: Path):
        """Set a custom output directory for generated files"""
        self.output_dir = Path(path)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Update filesystem server to use new path
        if "filesystem" in self.servers:
            self.servers["filesystem"].args = [
                "-y",
                "@modelcontextprotocol/server-filesystem",
                str(self.output_dir)
            ]
        
        self._save_config()
    
    def export_to_claude_config(self) -> Dict:
        """
        Export configuration in Claude Desktop format
        Returns dict that can be saved to Claude's config.json
        """
        mcpServers = {}
        
        for name, server in self.get_enabled_servers().items():
            mcpServers[name] = {
                "command": server.command,
                "args": server.args
            }
            
            if server.env:
                mcpServers[name]["env"] = server.env
        
        return {
            "mcpServers": mcpServers
        }
    
    def validate_filesystem_access(self) -> bool:
        """
        Validate that filesystem server is properly restricted to output directory
        Returns True if safe, False otherwise
        """
        if "filesystem" not in self.servers:
            return True  # No filesystem server = safe
        
        fs_server = self.servers["filesystem"]
        if not fs_server.enabled:
            return True  # Disabled = safe
        
        # Check that args contain the output directory path
        args_str = " ".join(fs_server.args)
        return str(self.output_dir) in args_str
    
    def get_security_summary(self) -> Dict:
        """Get summary of security settings"""
        return {
            "output_dir": str(self.output_dir),
            "filesystem_enabled": self.servers.get("filesystem", MCPServerConfig("", "", [])).enabled,
            "filesystem_restricted": self.validate_filesystem_access(),
            "enabled_servers": list(self.get_enabled_servers().keys()),
            "api_keys_configured": {
                name: bool(server.env and server.env.get("BRAVE_API_KEY"))
                for name, server in self.servers.items()
                if server.env and "BRAVE_API_KEY" in server.env
            }
        }


# Singleton instance for easy access
_config_instance: Optional[MCPConfig] = None


def get_mcp_config() -> MCPConfig:
    """Get or create the global MCP configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = MCPConfig()
    return _config_instance


if __name__ == "__main__":
    # Test the configuration
    config = MCPConfig()
    
    print("\n=== InsightOS MCP Configuration ===")
    print(f"Config file: {config.config_file}")
    print(f"Output directory: {config.output_dir}")
    print(f"\nEnabled servers: {list(config.get_enabled_servers().keys())}")
    
    print("\n=== Security Summary ===")
    for key, value in config.get_security_summary().items():
        print(f"{key}: {value}")
    
    print("\n=== Claude Desktop Config Export ===")
    print(json.dumps(config.export_to_claude_config(), indent=2))