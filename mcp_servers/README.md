# InsightOS MCP Configuration

## Overview

This module manages MCP (Model Context Protocol) server configurations for InsightOS, implementing **read-only + safe writing** architecture as recommended for v1.

## Key Design Decisions

### ✅ What the Agent CAN Do
- **Write NEW files** to `~/InsightOS/Generated/` directory
- Create summaries, reports, templates, and extracted data
- Synthesize knowledge from indexed documents into new artifacts
- Use memory system for knowledge graph and entity tracking
- (Optional) Web search via Brave Search API

### ❌ What the Agent CANNOT Do
- Modify original indexed documents
- Write files outside the `Generated/` directory
- Delete or rename user's original files
- Bulk operations without confirmation (handled at UI level)

## Architecture

```
~/InsightOS/
├── Generated/           # Safe write zone for agent-generated files
│   ├── summaries/
│   ├── reports/
│   ├── extracts/
│   └── templates/
└── Indexed/            # User documents (read-only via ChromaDB)
    └── ...

~/.insightos/
└── mcp/
    └── servers.json    # MCP server configurations
```

## Default MCP Servers

### 1. Filesystem Server (Restricted)
- **Purpose**: File reading and writing
- **Restriction**: Only has access to `~/InsightOS/Generated/`
- **Status**: Enabled by default
- **Safety**: Cannot access or modify user's original documents

### 2. Memory Server
- **Purpose**: Knowledge graph and entity memory
- **Features**: 
  - Create relations between entities
  - Store conversation context
  - Build semantic connections
- **Status**: Enabled by default

### 3. Brave Search Server
- **Purpose**: Web search capability
- **Status**: Disabled by default (requires API key)
- **Setup**: Call `config.set_brave_api_key("your-key")`

## Usage Examples

### Basic Usage

```python
from mcp_servers.config import get_mcp_config

# Get configuration instance
config = get_mcp_config()

# Check what's enabled
enabled = config.get_enabled_servers()
print(f"Active servers: {list(enabled.keys())}")

# Get output directory
output_dir = config.get_output_dir()
print(f"Generated files go to: {output_dir}")
```

### Security Validation

```python
from mcp_servers.config import get_mcp_config

config = get_mcp_config()

# Get security summary
security = config.get_security_summary()
print(f"Filesystem restricted: {security['filesystem_restricted']}")
print(f"Output directory: {security['output_dir']}")

# Validate filesystem access is safe
is_safe = config.validate_filesystem_access()
assert is_safe, "Filesystem access is not properly restricted!"
```

### Custom Output Directory

```python
from pathlib import Path
from mcp_servers.config import get_mcp_config

config = get_mcp_config()

# Change output directory (e.g., for testing)
custom_dir = Path("/tmp/insightos_test")
config.set_output_dir(custom_dir)

# Filesystem server automatically updates to use new path
```

### Configure Brave Search

```python
from mcp_servers.config import get_mcp_config

config = get_mcp_config()

# Set API key and enable
config.set_brave_api_key("your-brave-api-key")

# Verify it's enabled
brave_server = config.get_server("brave-search")
print(f"Brave Search enabled: {brave_server.enabled}")
```

### Export for Claude Desktop

```python
import json
from mcp_servers.config import get_mcp_config

config = get_mcp_config()

# Export configuration for Claude Desktop
claude_config = config.export_to_claude_config()

# Save to Claude's config file (example path)
with open("/path/to/claude_desktop_config.json", "w") as f:
    json.dump(claude_config, f, indent=2)
```

### Add Custom MCP Server

```python
from mcp_servers.config import get_mcp_config, MCPServerConfig

config = get_mcp_config()

# Add custom server
custom_server = MCPServerConfig(
    name="my-custom-tool",
    command="node",
    args=["/path/to/my-server.js"],
    env={"API_KEY": "secret"},
    enabled=True,
    description="My custom MCP server"
)

config.add_server(custom_server)
```

## File Organization for Generated Content

Recommended structure within `~/InsightOS/Generated/`:

```
Generated/
├── summaries/
│   ├── 2025-01-21_AI_Ethics_Summary.md
│   └── Weekly_Research_Digest_2025-W03.md
├── reports/
│   ├── Project_Analysis_Report.pdf
│   └── Meeting_Notes_Synthesis.docx
├── extracts/
│   ├── Action_Items_2025-01.csv
│   └── Bibliography_AI_Papers.bib
├── templates/
│   ├── Meeting_Notes_Template.md
│   └── Project_Proposal_Template.md
└── _metadata/
    └── generation_log.json  # Track what was generated when
```

## Integration with InsightOS

### From UI Layer

```python
from mcp_servers.config import get_mcp_config

# In your PyQt6 application
config = get_mcp_config()

# Show user the output directory in settings
output_path = config.get_output_dir()
settings_widget.set_output_path(output_path)

# Validate before enabling agent features
if not config.validate_filesystem_access():
    show_security_warning()
```

### From Agent Layer

```python
from mcp_servers.config import get_mcp_config
import anthropic

config = get_mcp_config()

# When initializing Claude with MCP
client = anthropic.Anthropic(api_key="...")

# Get enabled MCP servers for the session
enabled_servers = config.get_enabled_servers()

# Pass to agent prompt
system_prompt = f"""
You have access to these MCP servers: {list(enabled_servers.keys())}

IMPORTANT: You can only write files to: {config.get_output_dir()}
All generated files must include metadata indicating they were created by InsightOS.
"""
```

## Provenance & Metadata

Every generated file should include metadata about its creation:

```python
from datetime import datetime
from mcp_servers.config import get_mcp_config

def add_provenance_to_file(filepath: Path, sources: list[str]):
    """Add metadata header to generated file"""
    
    config = get_mcp_config()
    
    header = f"""
---
Generated by: InsightOS
Date: {datetime.now().isoformat()}
Source documents: {len(sources)}
Output directory: {config.get_output_dir()}
---

"""
    
    # Prepend to file content
    with open(filepath, 'r') as f:
        content = f.read()
    
    with open(filepath, 'w') as f:
        f.write(header + content)
```

## Testing

```bash
cd mcp_servers
python config.py
```

Expected output:
- Creates `~/.insightos/mcp/servers.json`
- Creates `~/InsightOS/Generated/` directory
- Shows security summary confirming filesystem restriction

## Security Considerations

1. **Filesystem Isolation**: The filesystem MCP server only has access to the `Generated/` folder
2. **No Original File Modification**: Indexed documents are never exposed to write operations
3. **Clear Provenance**: All generated files are marked with metadata
4. **User Control**: Users can disable any MCP server through the config
5. **Validation**: `validate_filesystem_access()` ensures safety

## Future Extensions (v2+)

Potential additions for future versions:
- **Git MCP Server**: For code repository documentation
- **SQLite MCP Server**: For structured data queries
- **Puppeteer MCP Server**: For web scraping research
- **Sequential Thinking MCP**: For complex reasoning chains

Each new server should follow the principle: **transform existing knowledge into new artifacts, don't modify originals**.

## Configuration File Location

- **Config**: `~/.insightos/mcp/servers.json`
- **Output**: `~/InsightOS/Generated/`
- **Format**: JSON with timestamp tracking

## API Reference

### MCPConfig Class

- `__init__(config_dir)`: Initialize configuration
- `add_server(server)`: Add/update server config
- `remove_server(name)`: Remove server
- `enable_server(name)`: Enable server
- `disable_server(name)`: Disable server
- `get_enabled_servers()`: Get active servers
- `get_server(name)`: Get specific server
- `set_brave_api_key(key)`: Configure Brave Search
- `get_output_dir()`: Get generation directory
- `set_output_dir(path)`: Change output directory
- `export_to_claude_config()`: Export for Claude Desktop
- `validate_filesystem_access()`: Verify safety
- `get_security_summary()`: Get security info

### MCPServerConfig Dataclass

```python
@dataclass
class MCPServerConfig:
    name: str
    command: str
    args: List[str]
    env: Optional[Dict[str, str]] = None
    enabled: bool = True
    description: str = ""
```

## Support

For issues or questions:
1. Check security summary: `config.get_security_summary()`
2. Validate filesystem: `config.validate_filesystem_access()`
3. Review logs in `~/.insightos/mcp/`