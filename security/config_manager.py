"""
security/config_manager.py
Configuration management with encrypted API key storage
"""

from copy import copy
import json
from pathlib import Path
from typing import Optional, Dict, Any

from security.key_manager import KeyManager
from utils.logger import get_logger
from utils.file_utils import ensure_directory_exists, read_text_file, write_text_file
from copy import deepcopy as _deepcopy

logger = get_logger(__name__)


# Default configuration
DEFAULT_CONFIG = {
    'top_k': 5,
    'chunk_size': 1000,
    'chunk_overlap': 200,
    'monitored_directories': [],
    'file_types_enabled': [
        '.txt', '.md', '.pdf', '.docx', '.py', '.java', '.js',
        '.html', '.css', '.csv', '.log', '.rtf', '.ini', '.cfg',
        '.doc', '.odt', '.pages', '.asc', '.htm'
    ],
}

# Configuration file location
CONFIG_DIR = Path.home() / ".insightos"
CONFIG_FILE = CONFIG_DIR / "config.json"


class ConfigManager:
    """
    Manages application configuration with encrypted API key storage
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize ConfigManager
        
        Args:
            config_path: Path to config file (default: ~/.insightos/config.json)
        """
        self.config_path = config_path or CONFIG_FILE
        self.key_manager = KeyManager()
        
        # Ensure config directory exists
        ensure_directory_exists(self.config_path.parent)
        
        # Load or create config
        self._config = self._load_or_create_config()
        
        logger.info(f"ConfigManager initialized with config at: {self.config_path}")
    
    def _load_or_create_config(self) -> Dict[str, Any]:
        """
        Load existing config or create default
        
        Returns:
            Configuration dictionary
        """
        if self.config_path.exists():
            try:
                config_text = read_text_file(self.config_path)
                if config_text:
                    config = json.loads(config_text)
                    logger.info("Configuration loaded successfully")
                    return config
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse config file: {e}")
                logger.warning("Creating backup and using default config")
                self._backup_corrupted_config()
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
        
        # Create default config
        logger.info("Creating default configuration")
        config = DEFAULT_CONFIG.copy()
        self._save_config_to_disk(config)
        return config
    
    def _backup_corrupted_config(self):
        """Create backup of corrupted config file"""
        try:
            from datetime import datetime
            backup_name = f"config.json.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_path = self.config_path.parent / backup_name
            
            import shutil
            shutil.copy2(self.config_path, backup_path)
            logger.info(f"Corrupted config backed up to: {backup_path}")
        except Exception as e:
            logger.error(f"Failed to backup corrupted config: {e}")
    
    def _save_config_to_disk(self, config: Dict[str, Any]) -> bool:
        """
        Save configuration to disk
        
        Args:
            config: Configuration dictionary
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Remove api_key_encrypted from config before saving
            # (it's handled separately by KeyManager)
            config_to_save = config.copy()
            
            # Convert to JSON with nice formatting
            config_json = json.dumps(config_to_save, indent=2, sort_keys=True)
            
            # Write to file
            success = write_text_file(self.config_path, config_json)
            
            if success:
                # Set secure permissions (read/write for owner only)
                from utils.file_utils import set_file_permissions
                set_file_permissions(self.config_path, 0o600)
                logger.debug("Configuration saved to disk")
            
            return success
        
        except Exception as e:
            logger.error(f"Failed to save config to disk: {e}")
            return False
    
    # ========================================================================
    # Public API - Config Access
    # ========================================================================
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get current configuration
        
        Returns:
            Configuration dictionary (copy)
        """
        return _deepcopy(self._config)
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """
        Save configuration
        
        Args:
            config: Configuration dictionary to save
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate config
            from utils.validators import validate_config
            is_valid, error = validate_config(config)
            
            if not is_valid:
                logger.error(f"Invalid configuration: {error}")
                return False
            
            # Handle API key separately (encrypted storage)
            if 'api_key' in config:
                api_key = config.pop('api_key')
                if api_key:
                    success = self.key_manager.save_encrypted_key(api_key)
                    if not success:
                        logger.error("Failed to save encrypted API key")
                        return False
            
            # Update internal config
            self._config.update(config)
            
            # Save to disk
            return self._save_config_to_disk(self._config)
        
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Get specific setting
        
        Args:
            key: Setting key
            default: Default value if key not found
        
        Returns:
            Setting value or default
        """
        return self._config.get(key, default)
    
    def set_setting(self, key: str, value: Any) -> bool:
        """
        Set specific setting
        
        Args:
            key: Setting key
            value: Setting value
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self._config[key] = value
            return self._save_config_to_disk(self._config)
        except Exception as e:
            logger.error(f"Failed to set setting {key}: {e}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """
        Reset configuration to defaults (preserves API key and directories)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Preserve certain settings
            preserved_keys = ['monitored_directories']
            preserved_settings = {
                key: self._config.get(key)
                for key in preserved_keys
                if key in self._config
            }
            
            # Reset to defaults
            self._config = DEFAULT_CONFIG.copy()
            
            # Restore preserved settings
            self._config.update(preserved_settings)
            
            logger.info("Configuration reset to defaults")
            return self._save_config_to_disk(self._config)
        
        except Exception as e:
            logger.error(f"Failed to reset configuration: {e}")
            return False
    
    # ========================================================================
    # Public API - API Key Management
    # ========================================================================
    
    def has_api_key(self) -> bool:
        """
        Check if API key is configured
        
        Returns:
            True if API key exists, False otherwise
        """
        return self.key_manager.key_exists()
    
    def get_api_key(self) -> Optional[str]:
        """
        Get decrypted API key
        
        Returns:
            API key string or None if not configured
        
        Note: Key is cleared from memory after use by caller
        """
        return self.key_manager.get_decrypted_key()
    
    def save_api_key(self, api_key: str) -> bool:
        """
        Save API key (encrypted)
        
        Args:
            api_key: API key to save
        
        Returns:
            True if successful, False otherwise
        """
        # Validate format
        from utils.validators import validate_api_key_format
        is_valid, error = validate_api_key_format(api_key)
        
        if not is_valid:
            logger.error(f"Invalid API key format: {error}")
            return False
        
        # Save encrypted
        success = self.key_manager.save_encrypted_key(api_key)
        
        if success:
            logger.info("API key saved successfully")
        else:
            logger.error("Failed to save API key")
        
        return success
    
    def remove_api_key(self) -> bool:
        """
        Remove API key
        
        Returns:
            True if successful, False otherwise
        """
        success = self.key_manager.delete_key()
        
        if success:
            logger.info("API key removed")
        else:
            logger.error("Failed to remove API key")
        
        return success
    
    def validate_api_key(self, api_key: Optional[str] = None) -> bool:
        """
        Validate API key with test call
        
        Args:
            api_key: API key to validate (if None, use stored key)
        
        Returns:
            True if valid, False otherwise
        """
        if api_key is None:
            api_key = self.get_api_key()
        
        if not api_key:
            logger.error("No API key to validate")
            return False
        
        # Validate with KeyManager
        is_valid = self.key_manager.validate_api_key(api_key)
        
        # Clear from memory
        del api_key
        
        return is_valid
    
    # ========================================================================
    # Public API - Directory Management
    # ========================================================================
    
    def get_monitored_directories(self) -> list:
        """
        Get list of monitored directories
        
        Returns:
            List of directory paths
        """
        return self._config.get('monitored_directories', []).copy()
    
    def add_monitored_directory(self, directory: str) -> bool:
        """
        Add directory to monitored list
        
        Args:
            directory: Directory path to add
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate directory
            from utils.validators import validate_directory_path
            is_valid, error = validate_directory_path(directory, must_exist=True)
            
            if not is_valid:
                logger.error(f"Invalid directory: {error}")
                return False
            
            # Get current directories
            directories = self.get_monitored_directories()
            
            # Check if already exists
            if directory in directories:
                logger.warning(f"Directory already monitored: {directory}")
                return True
            
            # Add directory
            directories.append(directory)
            
            # Save
            return self.set_setting('monitored_directories', directories)
        
        except Exception as e:
            logger.error(f"Failed to add monitored directory: {e}")
            return False
    
    def remove_monitored_directory(self, directory: str) -> bool:
        """
        Remove directory from monitored list
        
        Args:
            directory: Directory path to remove
        
        Returns:
            True if successful, False otherwise
        """
        try:
            directories = self.get_monitored_directories()
            
            if directory not in directories:
                logger.warning(f"Directory not in monitored list: {directory}")
                return True
            
            directories.remove(directory)
            
            return self.set_setting('monitored_directories', directories)
        
        except Exception as e:
            logger.error(f"Failed to remove monitored directory: {e}")
            return False
    
    # ========================================================================
    # Public API - Convenience Methods
    # ========================================================================
    
    def is_configured(self) -> bool:
        """
        Check if application is configured (has API key)
        
        Returns:
            True if configured, False otherwise
        """
        return self.has_api_key()
    
    def get_config_path(self) -> Path:
        """
        Get path to config file
        
        Returns:
            Path to config file
        """
        return self.config_path
    
    def export_config(self, export_path: Path, include_api_key: bool = False) -> bool:
        """
        Export configuration to file
        
        Args:
            export_path: Path to export to
            include_api_key: If True, include encrypted API key (NOT RECOMMENDED)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            config_to_export = self._config.copy()
            
            if include_api_key and self.has_api_key():
                logger.warning("Exporting config with encrypted API key")
                # This is not recommended for security reasons
                # API key is machine-specific and won't decrypt on another machine
            
            config_json = json.dumps(config_to_export, indent=2, sort_keys=True)
            success = write_text_file(export_path, config_json)
            
            if success:
                logger.info(f"Configuration exported to: {export_path}")
            
            return success
        
        except Exception as e:
            logger.error(f"Failed to export configuration: {e}")
            return False
    
    
    def reload(self) -> Dict[str, Any]:
        self._config = self._load_or_create_config()
        return _deepcopy(self._config)

    def import_config(self, import_path: Path, merge: bool = True) -> bool:
        """
        Import configuration from file
        
        Args:
            import_path: Path to import from
            merge: If True, merge with existing config; if False, replace
        
        Returns:
            True if successful, False otherwise
        """
        try:
            config_text = read_text_file(import_path)
            if not config_text:
                logger.error(f"Failed to read config from: {import_path}")
                return False
            
            imported_config = json.loads(config_text)
            
            # Validate
            from utils.validators import validate_config
            is_valid, error = validate_config(imported_config)
            
            if not is_valid:
                logger.error(f"Invalid imported configuration: {error}")
                return False
            
            if merge:
                # Merge with existing
                self._config.update(imported_config)
            else:
                # Replace entirely
                self._config = imported_config
            
            logger.info(f"Configuration imported from: {import_path}")
            return self._save_config_to_disk(self._config)
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse imported config: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to import configuration: {e}")
            return False


# Convenience singleton instance
_config_manager_instance = None

def get_config_manager() -> ConfigManager:
    """
    Get singleton ConfigManager instance
    
    Returns:
        ConfigManager instance
    """
    global _config_manager_instance
    if _config_manager_instance is None:
        _config_manager_instance = ConfigManager()
    return _config_manager_instance