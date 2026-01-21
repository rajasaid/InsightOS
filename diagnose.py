#!/usr/bin/env python3
"""
diagnose.py
Diagnostic script for InsightOS issues
"""

import sys
from pathlib import Path

def check_api_key():
    """Check if API key is properly configured"""
    print("=" * 60)
    print("CHECKING API KEY CONFIGURATION")
    print("=" * 60)
    
    try:
        from security.config_manager import ConfigManager
        
        config_manager = ConfigManager()
        
        print(f"✓ ConfigManager imported")
        print(f"  Has API key: {config_manager.has_api_key()}")
        
        if config_manager.has_api_key():
            try:
                api_key = config_manager.get_api_key()
                if api_key:
                    print(f"  API key length: {len(api_key)} characters")
                    print(f"  API key prefix: {api_key[:10]}...")
                    print(f"  ✓ API key retrieved successfully")
                else:
                    print(f"  ✗ API key is None or empty")
            except Exception as e:
                print(f"  ✗ Error retrieving API key: {e}")
        else:
            print(f"  ✗ No API key configured")
            print(f"  → Go to Settings → API Key and add your key")
        
        return config_manager.has_api_key()
        
    except Exception as e:
        print(f"✗ Error checking API key: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_claude_client():
    """Check if Claude client can initialize"""
    print("\n" + "=" * 60)
    print("CHECKING CLAUDE CLIENT")
    print("=" * 60)
    
    try:
        print("Attempting to import ClaudeClient...")
        from agent import ClaudeClient
        print("✓ ClaudeClient imported")
        
        print("\nAttempting to initialize ClaudeClient...")
        client = ClaudeClient()
        print("✓ ClaudeClient initialized successfully!")
        
        # Try to get status
        print("\nChecking MCP status...")
        status = client.get_mcp_status()
        print(f"✓ MCP status retrieved:")
        print(f"  Output dir: {status['output_dir']}")
        print(f"  Enabled servers: {status['enabled_servers']}")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("  → Check that agent/ directory has all required files")
        return False
    except Exception as e:
        print(f"✗ Initialization error: {e}")
        print("\nFull error details:")
        import traceback
        traceback.print_exc()
        return False


def check_mcp_config():
    """Check MCP configuration"""
    print("\n" + "=" * 60)
    print("CHECKING MCP CONFIGURATION")
    print("=" * 60)
    
    try:
        from mcp_servers import get_mcp_config
        
        mcp_config = get_mcp_config()
        print("✓ MCP config loaded")
        
        print(f"\nOutput directory: {mcp_config.get_output_dir()}")
        print(f"Filesystem restricted: {mcp_config.validate_filesystem_access()}")
        
        enabled = mcp_config.get_enabled_servers()
        print(f"\nEnabled servers ({len(enabled)}):")
        for name, server in enabled.items():
            print(f"  • {name}: {server.description}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error checking MCP: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_rag_retriever():
    """Check RAG retriever"""
    print("\n" + "=" * 60)
    print("CHECKING RAG RETRIEVER")
    print("=" * 60)
    
    try:
        from core.rag_retriever import RAGRetriever
        
        retriever = RAGRetriever(top_k=5)
        print("✓ RAG retriever initialized")
        
        # Try a test query (will return empty if no docs indexed)
        results = retriever.retrieve("test query")
        print(f"✓ Test query executed ({len(results)} results)")
        
        return True
        
    except Exception as e:
        print(f"✗ Error checking RAG: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_logs():
    """Check recent logs"""
    print("\n" + "=" * 60)
    print("CHECKING RECENT LOGS")
    print("=" * 60)
    
    log_file = Path.home() / ".insightos" / "logs" / "insightos.log"
    
    if not log_file.exists():
        print(f"✗ Log file not found: {log_file}")
        return False
    
    try:
        # Read last 50 lines
        with open(log_file, 'r') as f:
            lines = f.readlines()
            last_lines = lines[-50:]
        
        print(f"✓ Log file found: {log_file}")
        print(f"  Total lines: {len(lines)}")
        print("\nLast 20 lines:")
        print("-" * 60)
        for line in last_lines[-20:]:
            print(line.rstrip())
        
        # Look for errors
        errors = [l for l in last_lines if 'ERROR' in l or 'Error' in l]
        if errors:
            print("\n⚠️  Recent errors found:")
            print("-" * 60)
            for err in errors[-10:]:
                print(err.rstrip())
        
        return True
        
    except Exception as e:
        print(f"✗ Error reading logs: {e}")
        return False


def main():
    """Run all diagnostics"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "InsightOS Diagnostics" + " " * 22 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    results = {
        'api_key': check_api_key(),
        'mcp': check_mcp_config(),
        'rag': check_rag_retriever(),
        'claude': check_claude_client(),
    }
    
    # Always check logs
    check_logs()
    
    # Summary
    print("\n" + "=" * 60)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 60)
    
    for component, status in results.items():
        symbol = "✓" if status else "✗"
        print(f"{symbol} {component.upper()}: {'OK' if status else 'FAILED'}")
    
    if all(results.values()):
        print("\n🎉 All checks passed!")
        print("If you're still having issues, try:")
        print("  1. Restart the application")
        print("  2. Check Settings → Advanced → Agentic Mode is enabled")
        print("  3. Try re-entering your API key")
    else:
        print("\n⚠️  Some checks failed.")
        print("Please review the errors above and:")
        print("  1. Make sure your API key is configured in Settings")
        print("  2. Check that all dependencies are installed")
        print("  3. Review the log file for detailed errors")
    
    print("\nFor support, share the output above.")
    print()


if __name__ == "__main__":
    main()