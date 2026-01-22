"""
main.py
InsightOS application entry point with MCP support
"""

import sys
from pathlib import Path
import logging 
from PyQt6.QtWidgets import QApplication, QMessageBox

from ui.main_window import MainWindow
from ui.dialogs.setup_wizard import SetupWizard
from security.config_manager import ConfigManager
from indexing.indexer import Indexer
from mcp_servers import get_mcp_config
from utils.logger import setup_logger, get_logger

logger = None


def initialize_mcp():
    """
    Initialize MCP configuration and validate security
    
    Returns:
        bool: True if initialization successful, False otherwise
    """
    try:
        mcp_config = get_mcp_config()
        
        # Validate filesystem security
        if not mcp_config.validate_filesystem_access():
            logger.warning("MCP filesystem access validation failed")
            # Show warning but don't block startup
            QMessageBox.warning(
                None,
                "MCP Security Warning",
                "MCP filesystem access validation failed!\n\n"
                "File generation may not work correctly.\n"
                "Please check MCP settings."
            )
        
        logger.info("MCP Configuration initialized")
        logger.info(f"  Output directory: {mcp_config.get_output_dir()}")
        logger.info(f"  Enabled servers: {list(mcp_config.get_enabled_servers().keys())}")
        
        # Ensure output directory exists
        output_dir = mcp_config.get_output_dir()
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created output directory: {output_dir}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize MCP configuration: {e}", exc_info=True)
        QMessageBox.critical(
            None,
            "MCP Initialization Error",
            f"Failed to initialize MCP configuration:\n{str(e)}\n\n"
            "The application will continue, but file generation may not work."
        )
        return False


def check_prerequisites():
    """
    Check system prerequisites before starting
    
    Returns:
        tuple: (success: bool, error_message: str or None)
    """
    # Check Python version
    if sys.version_info < (3, 10):
        return False, "Python 3.10 or higher is required"
    
    # Check if required packages are available
    try:
        import anthropic
    except ImportError:
        return False, "anthropic package not installed. Run: pip install anthropic"
    
    try:
        import chromadb
    except ImportError:
        return False, "chromadb package not installed. Run: pip install chromadb"
    
    try:
        from PyQt6 import QtWidgets
    except ImportError:
        return False, "PyQt6 not installed. Run: pip install PyQt6"
    
    return True, None


def main():
    global logger
    
    # Setup logging
    #logger = setup_logger(level=logging.DEBUG)
    logger = setup_logger()
    logger.info("=" * 60)
    logger.info("Starting InsightOS...")
    logger.info("=" * 60)
    
    # Check prerequisites
    prereq_ok, prereq_error = check_prerequisites()
    if not prereq_ok:
        print(f"ERROR: {prereq_error}")
        sys.exit(1)
    
    # Check for --reset flag (for development/testing)
    if '--reset' in sys.argv:
        logger.info("Reset flag detected, clearing configuration...")
        
        # Clear app config
        config_dir = Path.home() / ".insightos"
        config_file = config_dir / "config.json"
        api_key_file = config_dir / ".api_key.enc"
        
        if config_file.exists():
            config_file.unlink()
            logger.info("Deleted config.json")
        
        if api_key_file.exists():
            api_key_file.unlink()
            logger.info("Deleted API key")
        
        # Clear MCP config
        mcp_config_file = config_dir / "mcp" / "servers.json"
        if mcp_config_file.exists():
            mcp_config_file.unlink()
            logger.info("Deleted MCP servers.json")
        
        logger.info("Configuration reset complete")
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("InsightOS")
    app.setOrganizationName("InsightOS")
    app.setApplicationDisplayName("InsightOS")
    
    # Set application style (macOS-like on all platforms)
    app.setStyle("Fusion")
    
    logger.info("Qt application created")
    
    # Initialize MCP configuration
    mcp_initialized = initialize_mcp()
    if mcp_initialized:
        logger.info("✓ MCP initialization successful")
    else:
        logger.warning("⚠ MCP initialization had issues (continuing anyway)")
    
    
    # Check if first-time setup needed
    config_manager = ConfigManager()
    
    # Create indexer (shared between wizard and main window)
    indexer = Indexer(config_manager=config_manager)
    logger.info("Indexer created")

    if not config_manager.is_configured():
        logger.info("First-time setup required, showing wizard")
        
        # Show setup wizard with indexer
        wizard = SetupWizard(indexer=indexer)
        
        if wizard.exec() == SetupWizard.DialogCode.Accepted:
            logger.info("Setup completed successfully")
            
            # Get config from wizard and save
            config_data = wizard.get_config_data()
            
            # Save API key
            if config_data.get('api_key'):
                config_manager.save_api_key(config_data['api_key'])
                logger.info("✓ API key saved")
            
            # Save directories
            directories = config_data.get('directories', [])
            for directory in directories:
                config_manager.add_monitored_directory(directory)
            logger.info(f"✓ Saved {len(directories)} monitored directories")
        else:
            logger.info("Setup cancelled, exiting")
            sys.exit(0)
    else:
        logger.info("Configuration exists, skipping setup wizard")
    
    # Show main window (pass the same indexer instance)
    try:
        window = MainWindow(indexer=indexer)
        window.show()
        logger.info("=" * 60)
        logger.info("✓ InsightOS started successfully")
        logger.info("=" * 60)
    except Exception as e:
        logger.error(f"Failed to create main window: {e}", exc_info=True)
        QMessageBox.critical(
            None,
            "Startup Error",
            f"Failed to start InsightOS:\n{str(e)}\n\n"
            "Please check the logs for more details."
        )
        sys.exit(1)
    
    # Run application
    exit_code = app.exec()
    logger.info(f"Application exited with code: {exit_code}")
    sys.exit(exit_code)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        if logger:
            logger.error(f"Unhandled exception in main: {e}", exc_info=True)
        else:
            print(f"FATAL ERROR: {e}")
        sys.exit(1)