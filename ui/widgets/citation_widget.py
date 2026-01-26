"""
ui/widgets/citation_widget.py
Expandable citation widget showing document sources
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QFont, QCursor, QDesktopServices
from PySide6.QtCore import QUrl
from pathlib import Path

from utils.logger import get_logger

logger = get_logger(__name__)


class CitationWidget(QWidget):
    """Expandable widget displaying source citations"""
    
    # Signals
    citation_clicked = Signal(str)  # Emitted when citation is clicked with filepath
    
    def __init__(self, citations: list, parent=None):
        super().__init__(parent)
        
        self.citations = citations  # List of citation dicts
        self.is_expanded = False
        
        self._setup_ui()
        self._apply_styles()
    
    def _setup_ui(self):
        """Setup citation widget UI"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(4)
        
        # Header (always visible, clickable to expand/collapse)
        self.header = self._create_header()
        main_layout.addWidget(self.header)
        
        # Citations content (expandable)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(4)
        
        # Add individual citation items
        for citation in self.citations:
            citation_item = self._create_citation_item(citation)
            self.content_layout.addWidget(citation_item)
        
        # Initially hidden
        self.content_widget.setVisible(False)
        self.content_widget.setMaximumHeight(0)
        
        main_layout.addWidget(self.content_widget)
    
    def _create_header(self):
        """Create expandable header"""
        header = QFrame()
        header.setObjectName("citation_header")
        header.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 12, 8)
        header_layout.setSpacing(8)
        
        # Expand/collapse icon
        self.expand_icon = QLabel("▶")
        self.expand_icon.setFont(QFont("SF Pro Text", 10))
        from ui.styles.colors import TEXT_SECONDARY
        self.expand_icon.setStyleSheet(f"color: {TEXT_SECONDARY};")
        header_layout.addWidget(self.expand_icon)
        
        # Title
        citation_count = len(self.citations)
        title_text = f"Sources ({citation_count})" if citation_count != 1 else "Source (1)"
        title_label = QLabel(title_text)
        title_label.setFont(QFont("SF Pro Text", 12, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Make header clickable
        header.mousePressEvent = lambda e: self.toggle_expand()
        
        return header
    
    def _create_citation_item(self, citation: dict):
        """Create individual citation item"""
        item = QFrame()
        item.setObjectName("citation_item")
        
        item_layout = QVBoxLayout(item)
        item_layout.setContentsMargins(12, 10, 12, 10)
        item_layout.setSpacing(6)
        
        # File info row
        file_row = QHBoxLayout()
        file_row.setSpacing(8)
        
        # File icon
        file_icon = QLabel("📄")
        file_icon.setFont(QFont("SF Pro Text", 14))
        file_row.addWidget(file_icon)
        
        # File path and name
        file_info_layout = QVBoxLayout()
        file_info_layout.setSpacing(2)
        
        # Filename (bold)
        filename = citation.get('filename', 'Unknown file')
        if '/' in filename or '\\' in filename:
            # Extract just the filename from path
            filename = Path(filename).name
        
        filename_label = QLabel(filename)
        filename_label.setFont(QFont("SF Pro Text", 13, QFont.Weight.Bold))
        filename_label.setWordWrap(True)
        file_info_layout.addWidget(filename_label)
        
        # Full path (smaller, gray)
        filepath = citation.get('filepath', citation.get('filename', ''))
        if filepath:
            path_label = QLabel(filepath)
            path_label.setFont(QFont("SF Pro Text", 10))
            from ui.styles.colors import TEXT_SECONDARY
            path_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
            path_label.setWordWrap(True)
            file_info_layout.addWidget(path_label)
        
        file_row.addLayout(file_info_layout, stretch=1)
        
        # Open button
        if filepath:
            open_btn = QPushButton("Open")
            open_btn.setObjectName("open_btn")
            open_btn.setMaximumWidth(60)
            open_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            open_btn.clicked.connect(lambda: self._open_file(filepath))
            file_row.addWidget(open_btn)
        
        item_layout.addLayout(file_row)
        
        # Excerpt or context (if available)
        excerpt = citation.get('excerpt', citation.get('content', ''))
        if excerpt:
            excerpt_label = QLabel(f'"{excerpt}"')
            excerpt_label.setFont(QFont("SF Pro Text", 12))
            excerpt_label.setStyleSheet("font-style: italic;")
            excerpt_label.setWordWrap(True)
            excerpt_label.setMaximumHeight(100)  # Limit height
            item_layout.addWidget(excerpt_label)
        
        # Metadata row (line numbers, confidence, etc.)
        metadata_parts = []
        
        # Line numbers
        if 'line_start' in citation:
            line_start = citation['line_start']
            line_end = citation.get('line_end', line_start)
            if line_start == line_end:
                metadata_parts.append(f"Line {line_start}")
            else:
                metadata_parts.append(f"Lines {line_start}-{line_end}")
        
        # Chunk index
        if 'chunk_index' in citation:
            metadata_parts.append(f"Chunk {citation['chunk_index']}")
        
        # Confidence score
        if 'confidence' in citation:
            confidence = citation['confidence']
            if isinstance(confidence, float):
                metadata_parts.append(f"Confidence: {confidence:.2%}")
        
        # Relevance score
        if 'relevance_score' in citation:
            score = citation['relevance_score']
            if isinstance(score, float):
                metadata_parts.append(f"Relevance: {score:.2f}")
        
        if metadata_parts:
            metadata_text = " • ".join(metadata_parts)
            metadata_label = QLabel(metadata_text)
            metadata_label.setFont(QFont("SF Pro Text", 10))
            from ui.styles.colors import TEXT_SECONDARY
            metadata_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
            item_layout.addWidget(metadata_label)
        
        return item
    
    def _apply_styles(self):
        """Apply styling to citation widget"""
        from ui.styles.colors import (
            BACKGROUND, TEXT_PRIMARY, TEXT_SECONDARY,
            BORDER_COLOR, ACCENT_COLOR
        )
        
        self.setStyleSheet(f"""
            QFrame#citation_header {{
                background-color: #F5F5F7;
                border: 1px solid {BORDER_COLOR};
                border-radius: 8px;
            }}
            
            QFrame#citation_header:hover {{
                background-color: #EBEBED;
            }}
            
            QFrame#citation_item {{
                background-color: white;
                border: 1px solid {BORDER_COLOR};
                border-radius: 8px;
            }}
            
            QLabel {{
                color: {TEXT_PRIMARY};
            }}
            
            QPushButton#open_btn {{
                background-color: {ACCENT_COLOR};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: bold;
            }}
            
            QPushButton#open_btn:hover {{
                background-color: #0051D5;
            }}
            
            QPushButton#open_btn:pressed {{
                background-color: #003DB3;
            }}
        """)
    
    def toggle_expand(self):
        """Toggle expand/collapse state"""
        if self.is_expanded:
            self.collapse()
        else:
            self.expand()
    
    def expand(self):
        """Expand to show citations"""
        if self.is_expanded:
            return
        
        self.is_expanded = True
        
        # Update icon
        self.expand_icon.setText("▼")
        
        # Show content
        self.content_widget.setVisible(True)
        
        # Animate height
        self.animation = QPropertyAnimation(self.content_widget, b"maximumHeight")
        self.animation.setDuration(200)
        self.animation.setStartValue(0)
        
        # Calculate target height
        self.content_widget.setMaximumHeight(16777215)  # Remove limit temporarily
        target_height = self.content_widget.sizeHint().height()
        
        self.animation.setEndValue(target_height)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.start()
        
        logger.debug(f"Citations expanded, showing {len(self.citations)} sources")
    
    def collapse(self):
        """Collapse to hide citations"""
        if not self.is_expanded:
            return
        
        self.is_expanded = False
        
        # Update icon
        self.expand_icon.setText("▶")
        
        # Animate height
        self.animation = QPropertyAnimation(self.content_widget, b"maximumHeight")
        self.animation.setDuration(200)
        self.animation.setStartValue(self.content_widget.height())
        self.animation.setEndValue(0)
        self.animation.setEasingCurve(QEasingCurve.Type.InCubic)
        self.animation.finished.connect(lambda: self.content_widget.setVisible(False))
        self.animation.start()
        
        logger.debug("Citations collapsed")
    
    def _open_file(self, filepath: str):
        """Open file in default application"""
        try:
            path = Path(filepath)
            if path.exists():
                # Open file with default application
                url = QUrl.fromLocalFile(str(path.absolute()))
                QDesktopServices.openUrl(url)
                logger.info(f"Opening file: {filepath}")
                
                # Emit signal
                self.citation_clicked.emit(filepath)
            else:
                logger.warning(f"File not found: {filepath}")
                # TODO: Show error message to user
        except Exception as e:
            logger.error(f"Error opening file {filepath}: {e}")
    
    def get_citation_count(self):
        """Get number of citations"""
        return len(self.citations)
    
    def get_citations(self):
        """Get list of citations"""
        return self.citations