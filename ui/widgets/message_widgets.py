"""
ui/widgets/message_widgets.py
Message bubble widgets for user and assistant messages
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ui.widgets.citation_widget import CitationWidget
from utils.logger import get_logger

logger = get_logger(__name__)


class UserMessageWidget(QWidget):
    """User message bubble (right-aligned, blue)"""
    
    def __init__(self, message: str, parent=None):
        super().__init__(parent)
        
        self.message = message
        
        self._setup_ui()
        self._apply_styles()
    
    def _setup_ui(self):
        """Setup user message UI"""
        # Main layout (right-aligned)
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Left spacer (pushes message to right)
        main_layout.addStretch(1)
        
        # Message bubble
        bubble = QFrame()
        bubble.setObjectName("user_bubble")
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(12, 10, 12, 10)
        bubble_layout.setSpacing(0)
        
        # Message text
        message_label = QLabel(self.message)
        message_label.setWordWrap(True)
        message_label.setFont(QFont("SF Pro Text", 13))
        message_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        bubble_layout.addWidget(message_label)
        
        # Set maximum width (60% of parent)
        bubble.setMaximumWidth(600)
        bubble.setSizePolicy(
            QSizePolicy.Policy.Maximum,
            QSizePolicy.Policy.Preferred
        )
        
        main_layout.addWidget(bubble)
    
    def _apply_styles(self):
        """Apply styling to user message bubble"""
        from ui.styles.colors import ACCENT_COLOR
        
        self.setStyleSheet(f"""
            QFrame#user_bubble {{
                background-color: {ACCENT_COLOR};
                border-radius: 24px;
                border-bottom-right-radius: 12px;
            }}
            
            QLabel {{
                color: black;
            }}
        """)


class AssistantMessageWidget(QWidget):
    """Assistant message bubble (left-aligned, gray) with citations"""
    
    def __init__(self, message: str, citations: list = None, parent=None):
        super().__init__(parent)
        
        self.message = message
        self.citations = citations or []
        
        self._setup_ui()
        self._apply_styles()
    
    def _setup_ui(self):
        """Setup assistant message UI"""
        # Main layout (left-aligned)
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Content container (bubble + citations)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)
        
        # Message bubble
        bubble = QFrame()
        bubble.setObjectName("assistant_bubble")
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(12, 10, 12, 10)
        bubble_layout.setSpacing(0)
        
        # Message text with markdown-like formatting
        message_label = QLabel(self._format_message(self.message))
        message_label.setWordWrap(True)
        message_label.setFont(QFont("SF Pro Text", 13))
        message_label.setTextFormat(Qt.TextFormat.RichText)
        message_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse |
            Qt.TextInteractionFlag.LinksAccessibleByMouse
        )
        message_label.setOpenExternalLinks(True)
        bubble_layout.addWidget(message_label)
        
        # Set maximum width (70% of parent)
        bubble.setMaximumWidth(700)
        bubble.setSizePolicy(
            QSizePolicy.Policy.Maximum,
            QSizePolicy.Policy.Preferred
        )
        
        content_layout.addWidget(bubble)
        
        # Citations section (if any)
        if self.citations:
            citations_widget = CitationWidget(self.citations)
            citations_widget.setMaximumWidth(700)
            content_layout.addWidget(citations_widget)
        
        main_layout.addWidget(content_widget)
        
        # Right spacer (keeps message on left)
        main_layout.addStretch(1)
    
    def _format_message(self, text: str) -> str:
        """Format message text with basic markdown-like styling"""
        # Convert **bold** to <b>bold</b>
        import re
        
        # Escape HTML special characters first
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        # Bold: **text** or __text__
        text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'__(.+?)__', r'<b>\1</b>', text)
        
        # Italic: *text* or _text_
        text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
        text = re.sub(r'_(.+?)_', r'<i>\1</i>', text)
        
        # Code: `code`
        text = re.sub(
            r'`(.+?)`',
            r'<span style="background-color: #F0F0F0; padding: 2px 4px; border-radius: 3px; font-family: SF Mono;">\1</span>',
            text
        )
        
        # Line breaks
        text = text.replace('\n', '<br>')
        
        # Numbered lists: lines starting with "1. ", "2. ", etc.
        lines = text.split('<br>')
        formatted_lines = []
        in_list = False
        
        for line in lines:
            # Check if line starts with number and dot
            if re.match(r'^\d+\.\s', line):
                if not in_list:
                    formatted_lines.append('<ol style="margin: 8px 0; padding-left: 24px;">')
                    in_list = True
                # Remove the number and dot, wrap in <li>
                item_text = re.sub(r'^\d+\.\s', '', line)
                formatted_lines.append(f'<li>{item_text}</li>')
            else:
                if in_list:
                    formatted_lines.append('</ol>')
                    in_list = False
                formatted_lines.append(line)
        
        if in_list:
            formatted_lines.append('</ol>')
        
        text = '<br>'.join(formatted_lines)
        
        # Bullet lists: lines starting with "- " or "* "
        lines = text.split('<br>')
        formatted_lines = []
        in_list = False
        
        for line in lines:
            # Check if line starts with bullet
            if re.match(r'^[-*]\s', line):
                if not in_list:
                    formatted_lines.append('<ul style="margin: 8px 0; padding-left: 24px;">')
                    in_list = True
                # Remove the bullet, wrap in <li>
                item_text = re.sub(r'^[-*]\s', '', line)
                formatted_lines.append(f'<li>{item_text}</li>')
            else:
                if in_list:
                    formatted_lines.append('</ul>')
                    in_list = False
                formatted_lines.append(line)
        
        if in_list:
            formatted_lines.append('</ul>')
        
        text = '<br>'.join(formatted_lines)
        
        return text
    
    def _apply_styles(self):
        """Apply styling to assistant message bubble"""
        from ui.styles.colors import ASSISTANT_MESSAGE_BG, TEXT_PRIMARY
        
        self.setStyleSheet(f"""
            QFrame#assistant_bubble {{
                background-color: {ASSISTANT_MESSAGE_BG};
                border-radius: 12px;
                border-bottom-left-radius: 4px;
            }}
            
            QLabel {{
                color: {TEXT_PRIMARY};
            }}
        """)


class SystemMessageWidget(QWidget):
    """System message widget for notifications and status updates"""
    
    def __init__(self, message: str, message_type: str = "info", parent=None):
        super().__init__(parent)
        
        self.message = message
        self.message_type = message_type  # "info", "warning", "error", "success"
        
        self._setup_ui()
        self._apply_styles()
    
    def _setup_ui(self):
        """Setup system message UI"""
        # Main layout (centered)
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 8, 0, 8)
        main_layout.setSpacing(0)
        
        # Center the message
        main_layout.addStretch(1)
        
        # Message container
        message_widget = QFrame()
        message_widget.setObjectName("system_message")
        message_layout = QHBoxLayout(message_widget)
        message_layout.setContentsMargins(12, 8, 12, 8)
        message_layout.setSpacing(8)
        
        # Icon based on type
        icon_map = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "success": "✅"
        }
        icon = icon_map.get(self.message_type, "ℹ️")
        
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("SF Pro Text", 12))
        message_layout.addWidget(icon_label)
        
        # Message text
        text_label = QLabel(self.message)
        text_label.setFont(QFont("SF Pro Text", 12))
        text_label.setWordWrap(True)
        message_layout.addWidget(text_label)
        
        message_widget.setMaximumWidth(500)
        main_layout.addWidget(message_widget)
        
        main_layout.addStretch(1)
    
    def _apply_styles(self):
        """Apply styling based on message type"""
        from ui.styles.colors import TEXT_PRIMARY
        
        # Colors based on type
        color_map = {
            "info": ("#E3F2FD", "#1976D2"),      # Light blue, dark blue
            "warning": ("#FFF3E0", "#F57C00"),   # Light orange, dark orange
            "error": ("#FFEBEE", "#D32F2F"),     # Light red, dark red
            "success": ("#E8F5E9", "#388E3C")    # Light green, dark green
        }
        
        bg_color, text_color = color_map.get(self.message_type, color_map["info"])
        
        self.setStyleSheet(f"""
            QFrame#system_message {{
                background-color: {bg_color};
                border: 1px solid {text_color}40;
                border-radius: 8px;
            }}
            
            QLabel {{
                color: {text_color};
            }}
        """)