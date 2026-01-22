"""
ui/styles/__init__.py
UI styles package initialization
"""

# Import commonly used colors
from ui.styles.colors import (
    BACKGROUND,
    SIDEBAR_BACKGROUND,
    BACKGROUND_SECONDARY,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    ACCENT_COLOR,
    USER_MESSAGE_BG,
    ASSISTANT_MESSAGE_BG,
    SUCCESS_COLOR,
    WARNING_COLOR,
    ERROR_COLOR,
)

# Import commonly used font functions
from ui.styles.fonts import (
    get_display_font,
    get_text_font,
    get_mono_font,
    FONT_APP_TITLE,
    FONT_SECTION_HEADER,
    FONT_MESSAGE,
)

__all__ = [
    # Colors
    'BACKGROUND',
    'SIDEBAR_BACKGROUND',
    'TEXT_PRIMARY',
    'TEXT_SECONDARY',
    'ACCENT_COLOR',
    'USER_MESSAGE_BG',
    'ASSISTANT_MESSAGE_BG',
    'SUCCESS_COLOR',
    'WARNING_COLOR',
    'ERROR_COLOR',
    # Fonts
    'get_display_font',
    'get_text_font',
    'get_mono_font',
    'FONT_APP_TITLE',
    'FONT_SECTION_HEADER',
    'FONT_MESSAGE',
]