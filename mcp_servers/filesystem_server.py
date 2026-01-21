#!/usr/bin/env python3
"""
Filesystem MCP Server
Handles file operations for InsightOS
"""

import sys
import json
from pathlib import Path
from datetime import datetime


class FilesystemServer:
    """Simple MCP filesystem server"""
    
    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def handle_request(self, request):
        """Handle MCP request"""
        try:
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")
            
            if method == "tools/list":
                result = self.list_tools()
            elif method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                result = self.call_tool(tool_name, tool_args)
            else:
                result = {"error": f"Unknown method: {method}"}
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
        
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
    
    def list_tools(self):
        """List available tools"""
        return {
            "tools": [
                {
                    "name": "write_file",
                    "description": "Write content to a file in the generated directory",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "content": {"type": "string"}
                        },
                        "required": ["path", "content"]
                    }
                },
                {
                    "name": "read_file",
                    "description": "Read a file from the generated directory",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"}
                        },
                        "required": ["path"]
                    }
                },
                {
                    "name": "list_directory",
                    "description": "List files in a directory",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"}
                        },
                        "required": ["path"]
                    }
                }
            ]
        }
    
    def call_tool(self, tool_name, args):
        """Execute a tool"""
        if tool_name == "write_file":
            return self.write_file(args["path"], args["content"])
        elif tool_name == "read_file":
            return self.read_file(args["path"])
        elif tool_name == "list_directory":
            return self.list_directory(args.get("path", "."))
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    
    def write_file(self, path, content):
        """Write file"""
        try:
            full_path = self.output_dir / path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Add metadata
            metadata = f"""---
Generated: {datetime.now().isoformat()}
By: InsightOS MCP Filesystem Server
---

"""
            full_content = metadata + content
            
            full_path.write_text(full_content, encoding='utf-8')
            
            return {
                "success": True,
                "path": str(full_path),
                "message": f"File written: {full_path}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def read_file(self, path):
        """Read file"""
        try:
            full_path = self.output_dir / path
            content = full_path.read_text(encoding='utf-8')
            return {"success": True, "content": content}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def list_directory(self, path):
        """List directory"""
        try:
            full_path = self.output_dir / path
            files = [f.name for f in full_path.iterdir() if f.is_file()]
            dirs = [d.name for d in full_path.iterdir() if d.is_dir()]
            return {"success": True, "files": files, "directories": dirs}
        except Exception as e:
            return {"success": False, "error": str(e)}


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No output directory specified"}), file=sys.stderr)
        sys.exit(1)
    
    output_dir = sys.argv[1]
    server = FilesystemServer(output_dir)
    
    # JSON-RPC over stdio
    for line in sys.stdin:
        try:
            request = json.loads(line)
            response = server.handle_request(request)
            print(json.dumps(response), flush=True)
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "error": {"code": -32700, "message": f"Parse error: {str(e)}"}
            }
            print(json.dumps(error_response), flush=True)


if __name__ == "__main__":
    main()
