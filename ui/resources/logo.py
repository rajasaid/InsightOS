"""
ui/resources/logo.py
Logo utilities for InsightOS
"""

from pathlib import Path
from PyQt6.QtWidgets import QLabel
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

# Logo file paths
RESOURCES_DIR = Path(__file__).parent
LOGO_PATH = RESOURCES_DIR / "images" / "InsightOS-Logo.png"

def create_logo_label(size: int = 200) -> QLabel:
    """
    Create logo label from PNG file
    
    Args:
        size: Maximum size (maintains aspect ratio)
    
    Returns:
        QLabel with logo pixmap
    """
    if not LOGO_PATH.exists():
        # Fallback if logo not found
        label = QLabel("🔍")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 48px;")
        return label
    
    # Load pixmap
    pixmap = QPixmap(str(LOGO_PATH))
    
    # Scale to fill width while keeping reasonable height
    # For sidebar, we want full width (around 280-300px) with proportional height
    pixmap = pixmap.scaled(
        size, 
        int(size * 0.4),  # Height is 40% of width for banner-like appearance
        Qt.AspectRatioMode.IgnoreAspectRatio,  # Stretch to fill
        Qt.TransformationMode.SmoothTransformation
    )
    
    label = QLabel()
    label.setPixmap(pixmap)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    
    return label
