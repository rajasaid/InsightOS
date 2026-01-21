"""
ui/styles/colors.py
macOS-native color scheme for InsightOS
"""

# ============================================================================
# Primary Colors
# ============================================================================

# Main backgrounds
BACKGROUND = "#FFFFFF"              # Pure white for main content area
SIDEBAR_BACKGROUND = "#F5F5F7"      # Light gray for sidebar (macOS style)

# Text colors
TEXT_PRIMARY = "#000000"            # Black for primary text
TEXT_SECONDARY = "#8E8E93"          # Gray for secondary text/labels
TEXT_TERTIARY = "#C7C7CC"           # Light gray for disabled/placeholder

# ============================================================================
# Accent Colors
# ============================================================================

# System blue (macOS accent color)
ACCENT_COLOR = "#007AFF"            # Primary blue for buttons, links
ACCENT_HOVER = "#0051D5"            # Darker blue for hover state
ACCENT_PRESSED = "#003DB3"          # Even darker for pressed state

# ============================================================================
# UI Element Colors
# ============================================================================

# Borders and dividers
BORDER_COLOR = "#D1D1D6"            # Light gray for borders
DIVIDER_COLOR = "#E5E5EA"           # Very light gray for subtle dividers

# Buttons
BUTTON_BACKGROUND = "#F0F0F0"       # Light gray for secondary buttons
BUTTON_HOVER = "#E8E8E8"            # Slightly darker on hover
BUTTON_PRESSED = "#D0D0D0"          # Even darker when pressed
BUTTON_DISABLED = "#F5F5F5"         # Very light gray when disabled

# ============================================================================
# Message Bubbles
# ============================================================================

# User message (blue, right-aligned)
USER_MESSAGE_BG = ACCENT_COLOR      # System blue
USER_MESSAGE_TEXT = "#FFFFFF"       # White text

# Assistant message (gray, left-aligned)
ASSISTANT_MESSAGE_BG = "#E5E5EA"    # Light gray
ASSISTANT_MESSAGE_TEXT = TEXT_PRIMARY

# ============================================================================
# Status Colors
# ============================================================================

# Success (green)
SUCCESS_COLOR = "#34C759"           # System green
SUCCESS_BG = "#E8F5E9"              # Light green background
SUCCESS_BORDER = "#C8E6C9"          # Green border

# Warning (orange)
WARNING_COLOR = "#FF9500"           # System orange
WARNING_BG = "#FFF3E0"              # Light orange background
WARNING_BORDER = "#FFE0B2"          # Orange border

# Error (red)
ERROR_COLOR = "#FF3B30"             # System red
ERROR_BG = "#FFEBEE"                # Light red background
ERROR_BORDER = "#FFCDD2"            # Red border

# Info (blue)
INFO_COLOR = "#0A84FF"              # System light blue
INFO_BG = "#E3F2FD"                 # Light blue background
INFO_BORDER = "#BBDEFB"             # Blue border

# ============================================================================
# Input Fields
# ============================================================================

INPUT_BG = "#FFFFFF"                # White background
INPUT_BORDER = BORDER_COLOR         # Standard border
INPUT_BORDER_FOCUS = ACCENT_COLOR   # Blue border when focused
INPUT_PLACEHOLDER = TEXT_TERTIARY   # Light gray placeholder text

# ============================================================================
# Progress & Loading
# ============================================================================

PROGRESS_BG = "#F0F0F0"             # Light gray background
PROGRESS_FILL = ACCENT_COLOR        # Blue fill

# ============================================================================
# Scrollbars
# ============================================================================

SCROLLBAR_BG = "transparent"        # Invisible background
SCROLLBAR_HANDLE = "#C0C0C0"        # Gray handle
SCROLLBAR_HANDLE_HOVER = "#A0A0A0"  # Darker on hover

# ============================================================================
# Citations
# ============================================================================

CITATION_HEADER_BG = "#F5F5F7"      # Light gray for header
CITATION_HEADER_HOVER = "#EBEBED"   # Slightly darker on hover
CITATION_ITEM_BG = "#FFFFFF"        # White for individual items
CITATION_BORDER = BORDER_COLOR      # Standard border

# ============================================================================
# Special Elements
# ============================================================================

# Code blocks
CODE_BG = "#F0F0F0"                 # Light gray background
CODE_BORDER = "#D0D0D0"             # Darker border
CODE_TEXT = "#1D1D1F"               # Almost black text

# Links
LINK_COLOR = ACCENT_COLOR           # Blue for links
LINK_HOVER = ACCENT_HOVER           # Darker blue on hover
LINK_VISITED = "#5856D6"            # Purple for visited links

# Selection
SELECTION_BG = ACCENT_COLOR         # Blue background
SELECTION_TEXT = "#FFFFFF"          # White text

# ============================================================================
# Dark Mode (Future Enhancement)
# ============================================================================
# Placeholder for dark mode colors - not implemented yet
# Can be added later with theme switching functionality

DARK_BACKGROUND = "#1C1C1E"
DARK_SIDEBAR_BACKGROUND = "#2C2C2E"
DARK_TEXT_PRIMARY = "#FFFFFF"
DARK_TEXT_SECONDARY = "#98989D"
DARK_BORDER_COLOR = "#38383A"

# ============================================================================
# Helper Functions
# ============================================================================

def hex_to_rgba(hex_color: str, alpha: float = 1.0) -> str:
    """
    Convert hex color to RGBA string
    
    Args:
        hex_color: Hex color string (e.g., "#007AFF")
        alpha: Alpha value 0.0-1.0
    
    Returns:
        RGBA string (e.g., "rgba(0, 122, 255, 1.0)")
    """
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


def lighten_color(hex_color: str, amount: float = 0.2) -> str:
    """
    Lighten a hex color by a certain amount
    
    Args:
        hex_color: Hex color string
        amount: Amount to lighten (0.0-1.0)
    
    Returns:
        Lightened hex color string
    """
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    
    r = min(255, int(r + (255 - r) * amount))
    g = min(255, int(g + (255 - g) * amount))
    b = min(255, int(b + (255 - b) * amount))
    
    return f"#{r:02x}{g:02x}{b:02x}"


def darken_color(hex_color: str, amount: float = 0.2) -> str:
    """
    Darken a hex color by a certain amount
    
    Args:
        hex_color: Hex color string
        amount: Amount to darken (0.0-1.0)
    
    Returns:
        Darkened hex color string
    """
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    
    r = max(0, int(r * (1 - amount)))
    g = max(0, int(g * (1 - amount)))
    b = max(0, int(b * (1 - amount)))
    
    return f"#{r:02x}{g:02x}{b:02x}"