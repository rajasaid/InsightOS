"""
ui/styles/fonts.py
macOS-native font definitions for InsightOS
"""

from PyQt6.QtGui import QFont

# ============================================================================
# Font Family Constants
# ============================================================================

# San Francisco fonts (macOS system fonts)
SF_PRO_DISPLAY = "SF Pro Display"   # For large text (titles, headers)
SF_PRO_TEXT = "SF Pro Text"         # For body text (13pt and smaller)
SF_MONO = "SF Mono"                 # For code and monospaced text

# Fallback fonts for non-macOS systems
FALLBACK_DISPLAY = "Segoe UI"       # Windows
FALLBACK_TEXT = "Segoe UI"          # Windows
FALLBACK_MONO = "Consolas"          # Windows / "Monaco" for older macOS

# ============================================================================
# Font Size Constants (in points)
# ============================================================================

# Display sizes (for titles and headers)
SIZE_DISPLAY_LARGE = 24             # Very large titles
SIZE_DISPLAY_MEDIUM = 20            # Section titles
SIZE_DISPLAY_SMALL = 18             # Subsection titles

# Text sizes (for body content)
SIZE_TITLE = 16                     # Card/panel titles
SIZE_HEADLINE = 14                  # Prominent text
SIZE_BODY = 13                      # Standard body text
SIZE_CALLOUT = 12                   # De-emphasized text
SIZE_SUBHEAD = 11                   # Small labels
SIZE_FOOTNOTE = 10                  # Very small text
SIZE_CAPTION = 9                    # Captions and metadata

# Monospace sizes
SIZE_MONO_LARGE = 13                # Code blocks
SIZE_MONO_MEDIUM = 12               # Inline code
SIZE_MONO_SMALL = 11                # Small code snippets

# ============================================================================
# Font Weight Constants
# ============================================================================

WEIGHT_ULTRALIGHT = QFont.Weight.ExtraLight  # 200
WEIGHT_THIN = QFont.Weight.Thin              # 100
WEIGHT_LIGHT = QFont.Weight.Light            # 300
WEIGHT_REGULAR = QFont.Weight.Normal         # 400
WEIGHT_MEDIUM = QFont.Weight.Medium          # 500
WEIGHT_SEMIBOLD = QFont.Weight.DemiBold      # 600
WEIGHT_BOLD = QFont.Weight.Bold              # 700
WEIGHT_HEAVY = QFont.Weight.ExtraBold        # 800
WEIGHT_BLACK = QFont.Weight.Black            # 900

# ============================================================================
# Pre-configured Font Functions
# ============================================================================

def get_display_font(size: int = SIZE_DISPLAY_MEDIUM, 
                     weight: QFont.Weight = WEIGHT_BOLD) -> QFont:
    """
    Get SF Pro Display font for titles and headers
    
    Args:
        size: Font size in points
        weight: Font weight
    
    Returns:
        QFont configured for display text
    """
    font = QFont(SF_PRO_DISPLAY, size, weight)
    font.setStyleHint(QFont.StyleHint.System)
    return font


def get_text_font(size: int = SIZE_BODY, 
                  weight: QFont.Weight = WEIGHT_REGULAR) -> QFont:
    """
    Get SF Pro Text font for body text
    
    Args:
        size: Font size in points
        weight: Font weight
    
    Returns:
        QFont configured for body text
    """
    font = QFont(SF_PRO_TEXT, size, weight)
    font.setStyleHint(QFont.StyleHint.System)
    return font


def get_mono_font(size: int = SIZE_MONO_MEDIUM,
                  weight: QFont.Weight = WEIGHT_REGULAR) -> QFont:
    """
    Get SF Mono font for code and monospaced text
    
    Args:
        size: Font size in points
        weight: Font weight
    
    Returns:
        QFont configured for monospaced text
    """
    font = QFont(SF_MONO, size, weight)
    font.setStyleHint(QFont.StyleHint.Monospace)
    font.setFixedPitch(True)
    return font


# ============================================================================
# Common Font Presets
# ============================================================================

# App title (sidebar header)
FONT_APP_TITLE = get_display_font(SIZE_DISPLAY_MEDIUM, WEIGHT_BOLD)

# Section headers
FONT_SECTION_HEADER = get_display_font(SIZE_HEADLINE, WEIGHT_BOLD)

# Button text
FONT_BUTTON = get_text_font(SIZE_BODY, WEIGHT_SEMIBOLD)

# Message bubbles
FONT_MESSAGE = get_text_font(SIZE_BODY, WEIGHT_REGULAR)

# Input fields
FONT_INPUT = get_text_font(SIZE_BODY, WEIGHT_REGULAR)

# Labels and captions
FONT_LABEL = get_text_font(SIZE_SUBHEAD, WEIGHT_REGULAR)
FONT_CAPTION = get_text_font(SIZE_FOOTNOTE, WEIGHT_REGULAR)

# Status text
FONT_STATUS = get_text_font(SIZE_SUBHEAD, WEIGHT_REGULAR)

# Code
FONT_CODE_BLOCK = get_mono_font(SIZE_MONO_LARGE, WEIGHT_REGULAR)
FONT_CODE_INLINE = get_mono_font(SIZE_MONO_MEDIUM, WEIGHT_REGULAR)

# ============================================================================
# Helper Functions
# ============================================================================

def apply_font_to_widget(widget, font_type: str = "body"):
    """
    Apply a predefined font to a widget
    
    Args:
        widget: Qt widget to apply font to
        font_type: Type of font ("title", "body", "caption", "code", etc.)
    """
    font_map = {
        "app_title": FONT_APP_TITLE,
        "section_header": FONT_SECTION_HEADER,
        "button": FONT_BUTTON,
        "message": FONT_MESSAGE,
        "input": FONT_INPUT,
        "label": FONT_LABEL,
        "caption": FONT_CAPTION,
        "status": FONT_STATUS,
        "code_block": FONT_CODE_BLOCK,
        "code_inline": FONT_CODE_INLINE,
        "body": FONT_MESSAGE,  # Default
    }
    
    font = font_map.get(font_type, FONT_MESSAGE)
    widget.setFont(font)


def scale_font(font: QFont, scale_factor: float) -> QFont:
    """
    Scale a font by a given factor
    
    Args:
        font: Base font
        scale_factor: Scaling factor (e.g., 1.5 for 150%)
    
    Returns:
        Scaled QFont
    """
    new_font = QFont(font)
    new_size = int(font.pointSize() * scale_factor)
    new_font.setPointSize(new_size)
    return new_font


def make_bold(font: QFont) -> QFont:
    """Make a font bold"""
    bold_font = QFont(font)
    bold_font.setWeight(WEIGHT_BOLD)
    return bold_font


def make_italic(font: QFont) -> QFont:
    """Make a font italic"""
    italic_font = QFont(font)
    italic_font.setItalic(True)
    return italic_font


# ============================================================================
# Font Loading (for custom fonts if needed)
# ============================================================================

def load_custom_font(font_path: str) -> int:
    """
    Load a custom font file
    
    Args:
        font_path: Path to font file (.ttf, .otf)
    
    Returns:
        Font ID (or -1 if failed)
    """
    from PyQt6.QtGui import QFontDatabase
    font_id = QFontDatabase.addApplicationFont(font_path)
    if font_id == -1:
        print(f"Failed to load font: {font_path}")
    return font_id


def list_available_fonts():
    """Print list of available fonts (useful for debugging)"""
    from PyQt6.QtGui import QFontDatabase
    fonts = QFontDatabase.families()
    print("Available fonts:")
    for font in sorted(fonts):
        print(f"  - {font}")