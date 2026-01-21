"""
security/key_manager.py
Secure API key management with machine-specific encryption
"""

import os
import uuid
import base64
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from utils.logger import get_logger
from utils.file_utils import ensure_directory_exists, read_text_file, write_text_file

logger = get_logger(__name__)


# Key storage location
KEY_DIR = Path.home() / ".insightos"
KEY_FILE = KEY_DIR / ".api_key.enc"


class KeyManager:
    """
    Manages API key encryption/decryption with machine-specific encryption
    """
    
    def __init__(self, key_file: Optional[Path] = None):
        """
        Initialize KeyManager
        
        Args:
            key_file: Path to encrypted key file (default: ~/.insightos/.api_key.enc)
        """
        self.key_file = key_file or KEY_FILE
        
        # Ensure directory exists
        ensure_directory_exists(self.key_file.parent)
        
        # Get machine-specific encryption key
        self._encryption_key = self._get_encryption_key()
        
        logger.debug("KeyManager initialized")
    
    def _get_machine_id(self) -> str:
        """
        Get machine-specific identifier
        
        Returns:
            Machine ID string
        
        Note: This uses the machine's hardware UUID. The encrypted key
        will only work on this specific machine.
        """
        try:
            # Try to get hardware UUID (most reliable)
            if os.name == 'posix':  # macOS, Linux
                # macOS: Use IOPlatformUUID
                if os.uname().sysname == 'Darwin':
                    import subprocess
                    result = subprocess.run(
                        ['ioreg', '-rd1', '-c', 'IOPlatformExpertDevice'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    for line in result.stdout.split('\n'):
                        if 'IOPlatformUUID' in line:
                            machine_id = line.split('"')[3]
                            logger.debug(f"Machine ID obtained from IOPlatformUUID")
                            return machine_id
                
                # Linux: Use /etc/machine-id or /var/lib/dbus/machine-id
                machine_id_paths = [
                    Path('/etc/machine-id'),
                    Path('/var/lib/dbus/machine-id')
                ]
                for path in machine_id_paths:
                    if path.exists():
                        machine_id = read_text_file(path)
                        if machine_id:
                            logger.debug(f"Machine ID obtained from {path}")
                            return machine_id.strip()
            
            # Fallback: Use uuid.getnode() (MAC address)
            mac = uuid.getnode()
            machine_id = str(mac)
            logger.warning("Using MAC address as machine ID (fallback)")
            return machine_id
        
        except Exception as e:
            logger.error(f"Failed to get machine ID: {e}")
            # Last resort: generate random but persistent ID
            fallback_id_file = self.key_file.parent / ".machine_id"
            if fallback_id_file.exists():
                fallback_id = read_text_file(fallback_id_file)
                if fallback_id:
                    return fallback_id.strip()
            
            # Generate and save new ID
            fallback_id = str(uuid.uuid4())
            write_text_file(fallback_id_file, fallback_id)
            logger.warning("Generated fallback machine ID")
            return fallback_id
    
    def _get_encryption_key(self) -> bytes:
        """
        Derive encryption key from machine ID
        
        Returns:
            Encryption key bytes
        """
        try:
            machine_id = self._get_machine_id()
            
            # Use PBKDF2HMAC to derive a key from machine ID
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'insightos_salt_v1',
                iterations=100000,
            )
            
            key = base64.urlsafe_b64encode(kdf.derive(machine_id.encode()))
            logger.debug("Encryption key derived from machine ID")
            return key
        
        except Exception as e:
            logger.error(f"Failed to derive encryption key: {e}")
            raise
    
    def _encrypt_key(self, api_key: str) -> str:
        """
        Encrypt API key
        
        Args:
            api_key: Plain text API key
        
        Returns:
            Base64-encoded encrypted key
        """
        try:
            fernet = Fernet(self._encryption_key)
            encrypted = fernet.encrypt(api_key.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Failed to encrypt API key: {e}")
            raise
    
    def _decrypt_key(self, encrypted_key: str) -> str:
        """
        Decrypt API key
        
        Args:
            encrypted_key: Base64-encoded encrypted key
        
        Returns:
            Plain text API key
        """
        try:
            fernet = Fernet(self._encryption_key)
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_key.encode())
            decrypted = fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt API key: {e}")
            raise
    
    # ========================================================================
    # Public API
    # ========================================================================
    
    def key_exists(self) -> bool:
        """
        Check if encrypted key file exists
        
        Returns:
            True if key file exists, False otherwise
        """
        return self.key_file.exists()
    
    def save_encrypted_key(self, api_key: str) -> bool:
        """
        Encrypt and save API key
        
        Args:
            api_key: Plain text API key
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate format before encrypting
            from utils.validators import validate_api_key_format
            is_valid, error = validate_api_key_format(api_key)
            
            if not is_valid:
                logger.error(f"Invalid API key format: {error}")
                return False
            
            # Encrypt
            encrypted_key = self._encrypt_key(api_key)
            
            # Save to file
            success = write_text_file(self.key_file, encrypted_key)
            
            if success:
                # Set secure permissions (read/write for owner only)
                from utils.file_utils import set_file_permissions
                set_file_permissions(self.key_file, 0o600)
                logger.info("API key encrypted and saved")
            
            # Clear from memory
            del api_key
            del encrypted_key
            
            return success
        
        except Exception as e:
            logger.error(f"Failed to save encrypted key: {e}")
            return False
    
    def get_decrypted_key(self) -> Optional[str]:
        """
        Read and decrypt API key
        
        Returns:
            Decrypted API key or None if not found/error
        
        IMPORTANT: Caller must clear the returned key from memory after use
        by setting the variable to None and calling del.
        
        Example:
            api_key = key_manager.get_decrypted_key()
            # Use api_key...
            api_key = None
            del api_key
        """
        try:
            if not self.key_exists():
                logger.warning("No encrypted key file found")
                return None
            
            # Read encrypted key
            encrypted_key = read_text_file(self.key_file)
            if not encrypted_key:
                logger.error("Failed to read encrypted key file")
                return None
            
            # Decrypt
            api_key = self._decrypt_key(encrypted_key.strip())
            
            # Clear encrypted key from memory
            del encrypted_key
            
            logger.debug("API key decrypted")
            return api_key
        
        except Exception as e:
            logger.error(f"Failed to decrypt key: {e}")
            logger.error("Key may have been encrypted on a different machine")
            return None
    
    def delete_key(self) -> bool:
        """
        Delete encrypted key file
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.key_exists():
                logger.warning("No key file to delete")
                return True
            
            self.key_file.unlink()
            logger.info("Encrypted key file deleted")
            return True
        
        except Exception as e:
            logger.error(f"Failed to delete key file: {e}")
            return False
    
    def validate_api_key(self, api_key: str) -> bool:
        """
        Validate API key with test call to Claude API
        
        Args:
            api_key: API key to validate
        
        Returns:
            True if valid, False otherwise
        """
        try:
            from anthropic import Anthropic
            
            # Create client with test key
            client = Anthropic(api_key=api_key)
            
            # Make minimal test call
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
            )
            
            # If we got here, key is valid
            logger.info("API key validated successfully")
            
            # Clear response from memory
            del response
            del client
            
            return True
        
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return False
    
    def change_key(self, old_key: str, new_key: str) -> bool:
        """
        Change API key (validates old key first)
        
        Args:
            old_key: Current API key (for verification)
            new_key: New API key to save
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current key and verify
            current_key = self.get_decrypted_key()
            
            if not current_key:
                logger.error("No current key found")
                return False
            
            if current_key != old_key:
                logger.error("Old key does not match current key")
                # Clear from memory
                del current_key
                del old_key
                return False
            
            # Clear old keys from memory
            del current_key
            del old_key
            
            # Validate new key
            if not self.validate_api_key(new_key):
                logger.error("New API key is invalid")
                return False
            
            # Save new key
            return self.save_encrypted_key(new_key)
        
        except Exception as e:
            logger.error(f"Failed to change key: {e}")
            return False
    
    def rotate_encryption(self) -> bool:
        """
        Re-encrypt existing key with current machine ID
        (Useful if machine ID changed or encryption upgraded)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current decrypted key
            api_key = self.get_decrypted_key()
            
            if not api_key:
                logger.error("No key to rotate")
                return False
            
            # Re-encrypt and save
            success = self.save_encrypted_key(api_key)
            
            # Clear from memory
            del api_key
            
            if success:
                logger.info("Encryption rotated successfully")
            
            return success
        
        except Exception as e:
            logger.error(f"Failed to rotate encryption: {e}")
            return False
    
    def get_key_info(self) -> dict:
        """
        Get information about stored key (without decrypting)
        
        Returns:
            Dictionary with key metadata
        """
        info = {
            'exists': self.key_exists(),
            'file_path': str(self.key_file),
            'is_readable': False,
            'file_size': 0,
            'modified_time': None,
        }
        
        if info['exists']:
            try:
                from utils.file_utils import (
                    is_readable,
                    get_file_size,
                    get_file_modified_time
                )
                
                info['is_readable'] = is_readable(self.key_file)
                info['file_size'] = get_file_size(self.key_file)
                info['modified_time'] = get_file_modified_time(self.key_file)
            except Exception as e:
                logger.error(f"Failed to get key info: {e}")
        
        return info


# Convenience function for testing
def test_encryption_decryption():
    """
    Test encryption and decryption functionality
    
    Returns:
        True if test passes, False otherwise
    """
    try:
        logger.info("Testing encryption/decryption...")
        
        key_manager = KeyManager()
        
        # Test key
        test_key = "sk-ant-test123456789"
        
        # Encrypt and save
        logger.info("Encrypting test key...")
        success = key_manager.save_encrypted_key(test_key)
        if not success:
            logger.error("Failed to encrypt test key")
            return False
        
        # Decrypt and verify
        logger.info("Decrypting test key...")
        decrypted_key = key_manager.get_decrypted_key()
        
        if decrypted_key != test_key:
            logger.error("Decrypted key does not match original")
            return False
        
        # Clean up
        key_manager.delete_key()
        
        logger.info("Encryption/decryption test PASSED")
        return True
    
    except Exception as e:
        logger.error(f"Encryption/decryption test FAILED: {e}")
        return False


if __name__ == "__main__":
    # Run test when executed directly
    test_encryption_decryption()