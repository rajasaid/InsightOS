"""
indexing/normalizer.py
Text normalization for improving search quality and consistency
"""

import re
import unicodedata
from typing import Optional, Dict, Any

from utils.logger import get_logger

logger = get_logger(__name__)


class Normalizer:
    """
    Normalizes text before chunking and indexing
    
    Handles:
    - Unicode normalization
    - Whitespace cleanup
    - Line break normalization
    - Special character handling
    - Case normalization (optional)
    - Number normalization (optional)
    """
    
    def __init__(
        self,
        normalize_unicode: bool = True,
        normalize_whitespace: bool = True,
        normalize_linebreaks: bool = True,
        normalize_quotes: bool = True,
        normalize_dashes: bool = True,
        remove_control_chars: bool = True,
        lowercase: bool = False,
        normalize_numbers: bool = False,
        remove_urls: bool = False,
        remove_emails: bool = False
    ):
        """
        Initialize normalizer with configuration
        
        Args:
            normalize_unicode: Normalize Unicode to NFC form
            normalize_whitespace: Clean up excessive whitespace
            normalize_linebreaks: Normalize line breaks
            normalize_quotes: Normalize quote characters
            normalize_dashes: Normalize dash/hyphen characters
            remove_control_chars: Remove control characters
            lowercase: Convert to lowercase (not recommended for most cases)
            normalize_numbers: Normalize number formats (e.g., 1,000 -> 1000)
            remove_urls: Remove URLs from text
            remove_emails: Remove email addresses from text
        """
        self.normalize_unicode = normalize_unicode
        self.normalize_whitespace = normalize_whitespace
        self.normalize_linebreaks = normalize_linebreaks
        self.normalize_quotes = normalize_quotes
        self.normalize_dashes = normalize_dashes
        self.remove_control_chars = remove_control_chars
        self.lowercase = lowercase
        self.normalize_numbers = normalize_numbers
        self.remove_urls = remove_urls
        self.remove_emails = remove_emails
        
        logger.debug(f"Normalizer initialized with {self._get_config_summary()}")
    
    def normalize(self, text: str) -> str:
        """
        Normalize text with all enabled normalizations
        
        Args:
            text: Raw text to normalize
            
        Returns:
            Normalized text
        """
        if not text:
            return ""
        
        original_length = len(text)
        
        # Apply normalizations in order
        if self.normalize_unicode:
            text = self._normalize_unicode(text)
        
        if self.remove_control_chars:
            text = self._remove_control_chars(text)
        
        if self.remove_urls:
            text = self._remove_urls(text)
        
        if self.remove_emails:
            text = self._remove_emails(text)
        
        if self.normalize_quotes:
            text = self._normalize_quotes(text)
        
        if self.normalize_dashes:
            text = self._normalize_dashes(text)
        
        if self.normalize_numbers:
            text = self._normalize_numbers(text)
        
        if self.normalize_linebreaks:
            text = self._normalize_linebreaks(text)
        
        if self.normalize_whitespace:
            text = self._normalize_whitespace(text)
        
        if self.lowercase:
            text = text.lower()
        
        # Final cleanup
        text = text.strip()
        
        normalized_length = len(text)
        
        if original_length != normalized_length:
            logger.debug(
                f"Normalized text: {original_length} -> {normalized_length} chars "
                f"({normalized_length/original_length*100:.1f}%)"
            )
        
        return text
    
    # ========================================================================
    # Normalization Methods
    # ========================================================================
    
    def _normalize_unicode(self, text: str) -> str:
        """
        Normalize Unicode to NFC (Canonical Decomposition + Composition)
        
        This ensures that characters like é are represented consistently:
        - é (single char) vs e + ́ (combining accent)
        
        Args:
            text: Text to normalize
            
        Returns:
            Unicode-normalized text
        """
        return unicodedata.normalize('NFC', text)
    
    def _remove_control_chars(self, text: str) -> str:
        """
        Remove control characters (except newlines and tabs)
        
        Args:
            text: Text to clean
            
        Returns:
            Text without control characters
        """
        # Keep newlines, tabs, and carriage returns
        return ''.join(
            char for char in text
            if unicodedata.category(char)[0] != 'C' or char in '\n\t\r'
        )
    
    def _normalize_quotes(self, text: str) -> str:
        """
        Normalize various quote characters to standard ASCII quotes
        
        Converts:
        - " " (smart quotes) → " (straight quotes)
        - ' ' (smart single quotes) → ' (straight single quote)
        - « » (guillemets) → " (straight quotes)
        
        Args:
            text: Text to normalize
            
        Returns:
            Text with normalized quotes
        """
        # Double quotes
        text = re.sub(r'[""«»„]', '"', text)
        
        # Single quotes
        text = re.sub(r'[''‚‛]', "'", text)
        
        return text
    
    def _normalize_dashes(self, text: str) -> str:
        """
        Normalize various dash/hyphen characters
        
        Converts:
        - — (em dash) → -
        - – (en dash) → -
        - ‐ (hyphen) → -
        
        Args:
            text: Text to normalize
            
        Returns:
            Text with normalized dashes
        """
        return re.sub(r'[—–‐]', '-', text)
    
    def _normalize_linebreaks(self, text: str) -> str:
        """
        Normalize line breaks
        
        - Converts \\r\\n to \\n
        - Removes excessive blank lines (max 2 consecutive newlines)
        
        Args:
            text: Text to normalize
            
        Returns:
            Text with normalized line breaks
        """
        # Normalize line endings
        text = text.replace('\r\n', '\n')
        text = text.replace('\r', '\n')
        
        # Remove excessive blank lines (max 1 blank line)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text
    
    def _normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace
        
        - Multiple spaces → single space
        - Tab → space
        - Remove trailing whitespace from lines
        
        Args:
            text: Text to normalize
            
        Returns:
            Text with normalized whitespace
        """
        # Convert tabs to spaces
        text = text.replace('\t', ' ')
        
        # Multiple spaces to single space (preserve newlines)
        lines = text.split('\n')
        lines = [re.sub(r' {2,}', ' ', line.strip()) for line in lines]
        text = '\n'.join(lines)
        
        return text
    
    def _normalize_numbers(self, text: str) -> str:
        """
        Normalize number formats
        
        - 1,000 → 1000
        - 1.000 (European) → 1000
        - Preserve decimals (1.5 stays 1.5)
        
        Args:
            text: Text to normalize
            
        Returns:
            Text with normalized numbers
        """
        # Remove thousand separators (commas and periods)
        # But preserve decimals
        
        # Pattern: number with commas (1,000,000)
        text = re.sub(r'(\d),(\d{3})', r'\1\2', text)
        
        # Pattern: European format (1.000.000)
        text = re.sub(r'(\d)\.(\d{3})', r'\1\2', text)
        
        return text
    
    def _remove_urls(self, text: str) -> str:
        """
        Remove URLs from text
        
        Args:
            text: Text to clean
            
        Returns:
            Text without URLs
        """
        # Match http/https URLs
        text = re.sub(
            r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b[-a-zA-Z0-9()@:%_\+.~#?&/=]*',
            '',
            text
        )
        
        # Match www URLs without protocol
        text = re.sub(
            r'www\.[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b[-a-zA-Z0-9()@:%_\+.~#?&/=]*',
            '',
            text
        )
        
        return text
    
    def _remove_emails(self, text: str) -> str:
        """
        Remove email addresses from text
        
        Args:
            text: Text to clean
            
        Returns:
            Text without email addresses
        """
        return re.sub(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            '',
            text
        )
    
    # ========================================================================
    # Statistics & Debugging
    # ========================================================================
    
    def get_normalization_stats(self, original: str, normalized: str) -> Dict[str, Any]:
        """
        Get statistics about normalization changes
        
        Args:
            original: Original text
            normalized: Normalized text
            
        Returns:
            Dictionary with statistics
        """
        return {
            'original_length': len(original),
            'normalized_length': len(normalized),
            'chars_removed': len(original) - len(normalized),
            'reduction_percent': (
                (len(original) - len(normalized)) / len(original) * 100
                if len(original) > 0 else 0
            ),
            'original_lines': original.count('\n') + 1,
            'normalized_lines': normalized.count('\n') + 1,
        }
    
    def _get_config_summary(self) -> str:
        """Get summary of enabled normalizations"""
        enabled = []
        if self.normalize_unicode: enabled.append('unicode')
        if self.normalize_whitespace: enabled.append('whitespace')
        if self.normalize_linebreaks: enabled.append('linebreaks')
        if self.normalize_quotes: enabled.append('quotes')
        if self.normalize_dashes: enabled.append('dashes')
        if self.remove_control_chars: enabled.append('control_chars')
        if self.lowercase: enabled.append('lowercase')
        if self.normalize_numbers: enabled.append('numbers')
        if self.remove_urls: enabled.append('urls')
        if self.remove_emails: enabled.append('emails')
        
        return f"{len(enabled)} normalizations enabled: {', '.join(enabled)}"


# ============================================================================
# Convenience Functions
# ============================================================================

def get_default_normalizer() -> Normalizer:
    """
    Get default normalizer with recommended settings
    
    Returns:
        Normalizer instance with default config
    """
    return Normalizer(
        normalize_unicode=True,
        normalize_whitespace=True,
        normalize_linebreaks=True,
        normalize_quotes=True,
        normalize_dashes=True,
        remove_control_chars=True,
        lowercase=False,  # Keep original case for better search
        normalize_numbers=False,  # Keep original number format
        remove_urls=False,  # Keep URLs (might be useful)
        remove_emails=False  # Keep emails (might be useful)
    )


def get_aggressive_normalizer() -> Normalizer:
    """
    Get aggressive normalizer (removes more content)
    
    Returns:
        Normalizer instance with aggressive config
    """
    return Normalizer(
        normalize_unicode=True,
        normalize_whitespace=True,
        normalize_linebreaks=True,
        normalize_quotes=True,
        normalize_dashes=True,
        remove_control_chars=True,
        lowercase=False,
        normalize_numbers=True,  # Normalize numbers
        remove_urls=True,  # Remove URLs
        remove_emails=True  # Remove emails
    )


def normalize_text(
    text: str,
    normalizer: Optional[Normalizer] = None
) -> str:
    """
    Convenience function to normalize text
    
    Args:
        text: Text to normalize
        normalizer: Optional normalizer instance (uses default if None)
        
    Returns:
        Normalized text
    """
    if normalizer is None:
        normalizer = get_default_normalizer()
    
    return normalizer.normalize(text)


# ============================================================================
# Testing/Debug
# ============================================================================

def test_normalizer():
    """Test normalizer"""
    logger.info("Testing Normalizer...")
    
    normalizer = get_default_normalizer()
    
    test_text = """
    This is a "test" with smart quotes and—em dashes.
    
    
    
    Multiple    spaces   and blank lines.
    
    Number: 1,000,000
    
    URL: https://example.com
    Email: test@example.com
    """
    
    normalized = normalizer.normalize(test_text)
    
    logger.info("Original:")
    logger.info(test_text)
    logger.info("\nNormalized:")
    logger.info(normalized)
    
    stats = normalizer.get_normalization_stats(test_text, normalized)
    logger.info(f"\nStats: {stats}")


if __name__ == "__main__":
    test_normalizer()