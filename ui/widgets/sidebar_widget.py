"""
ui/widgets/sidebar_widget.py
Sidebar widget with directory management and status display
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem,
    QFileDialog, QProgressBar, QMessageBox,
    QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from pathlib import Path

from indexing.indexer import Indexer
from utils.logger import get_logger

logger = get_logger(__name__)


class SidebarWidget(QWidget):
    """Sidebar widget for directory management and status display"""
    
    # Signals
    directory_added = pyqtSignal(str)  # Emitted when directory is added
    directory_removed = pyqtSignal(str)  # Emitted when directory is removed
    reindex_requested = pyqtSignal()  # Emitted when re-index is requested
    settings_requested = pyqtSignal()  # Emitted when settings button clicked
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._is_indexing = False
        self.indexer = Indexer()  # To be set externally
        self._setup_ui()
        self._apply_styles()
        
        logger.info("Sidebar widget initialized")
    
    def _setup_ui(self):
        """Setup sidebar UI components"""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # === App Header ===
        self._setup_header(layout)
        
        # === Separator ===
        layout.addWidget(self._create_separator())
        
        # === Monitored Directories Section ===
        self._setup_directories_section(layout)
        
        # === Separator ===
        layout.addWidget(self._create_separator())
        
        # === Indexing Status Section ===
        self._setup_status_section(layout)
        
        # === Spacer ===
        layout.addStretch()
        
        # === Separator ===
        layout.addWidget(self._create_separator())
        
        # === Settings Button ===
        self._setup_settings_button(layout)
    
    def _setup_header(self, layout):
        """Setup app header with logo and title"""
        header_layout = QVBoxLayout()
        header_layout.setSpacing(8)
        
        # === Logo ===
        from ui.resources.logo import create_logo_label
        logo_label = create_logo_label(size=280)  # 280px logo for sidebar
        header_layout.addWidget(logo_label)
        
        # === App title ===
        title_label = QLabel("InsightOS")
        title_label.setFont(QFont("SF Pro Display", 18, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label)
        
        # === Subtitle ===
        subtitle_label = QLabel("Knowledge Assistant")
        subtitle_label.setFont(QFont("SF Pro Text", 11))
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        from ui.styles.colors import TEXT_SECONDARY
        subtitle_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        header_layout.addWidget(subtitle_label)
        
        layout.addLayout(header_layout)
   
    
    def _setup_directories_section(self, layout):
        """Setup monitored directories section"""
        # Section header
        dirs_label = QLabel("Monitored Directories")
        dirs_label.setFont(QFont("SF Pro Display", 14, QFont.Weight.Bold))
        layout.addWidget(dirs_label)
        
        # Directory list
        self.dirs_list = QListWidget()
        self.dirs_list.setMinimumHeight(200)
        self.dirs_list.setMaximumHeight(400)
        self.dirs_list.setAlternatingRowColors(True)
        self.dirs_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        layout.addWidget(self.dirs_list)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)
        
        # Add button
        self.add_btn = QPushButton("Add")
        self.add_btn.setMinimumHeight(32)
        self.add_btn.clicked.connect(self.add_directory)
        buttons_layout.addWidget(self.add_btn)
        
        # Remove button
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.setMinimumHeight(32)
        self.remove_btn.clicked.connect(self.remove_directory)
        self.remove_btn.setEnabled(False)  # Disabled until selection
        buttons_layout.addWidget(self.remove_btn)
        
        layout.addLayout(buttons_layout)
        
        # Re-index button (full width)
        self.reindex_btn = QPushButton("Re-index All")
        self.reindex_btn.setMinimumHeight(32)
        self.reindex_btn.clicked.connect(self.reindex_all)
        self.reindex_btn.setEnabled(False)  # Disabled until directories added
        layout.addWidget(self.reindex_btn)
        
        # Connect selection change
        self.dirs_list.itemSelectionChanged.connect(self._on_selection_changed)
    
    def _setup_status_section(self, layout):
        """Setup indexing status section"""
        # Section header
        status_label = QLabel("Indexing Status")
        status_label.setFont(QFont("SF Pro Display", 14, QFont.Weight.Bold))
        layout.addWidget(status_label)
        
        # File count label
        self.file_count_label = QLabel("No files indexed")
        self.file_count_label.setFont(QFont("SF Pro Text", 12))
        from ui.styles.colors import TEXT_SECONDARY
        self.file_count_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        layout.addWidget(self.file_count_label)
        
        # Last indexed label
        self.last_indexed_label = QLabel("Never indexed")
        self.last_indexed_label.setFont(QFont("SF Pro Text", 11))
        self.last_indexed_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        layout.addWidget(self.last_indexed_label)
        
        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(20)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Progress status label (hidden by default)
        self.progress_label = QLabel("")
        self.progress_label.setFont(QFont("SF Pro Text", 11))
        self.progress_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        self.progress_label.setVisible(False)
        self.progress_label.setWordWrap(True)
        layout.addWidget(self.progress_label)
    
    def _setup_settings_button(self, layout):
        """Setup settings button at bottom"""
        self.settings_btn = QPushButton("⚙️  Settings")
        self.settings_btn.setMinimumHeight(40)
        self.settings_btn.setFont(QFont("SF Pro Text", 13))
        self.settings_btn.clicked.connect(self._on_settings_clicked)
        layout.addWidget(self.settings_btn)
    
    def _create_separator(self):
        """Create a horizontal separator line"""
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        from ui.styles.colors import BORDER_COLOR
        line.setStyleSheet(f"background-color: {BORDER_COLOR};")
        return line
    
    def _apply_styles(self):
        """Apply macOS-native styling"""
        from ui.styles.colors import (
            SIDEBAR_BACKGROUND, TEXT_PRIMARY, TEXT_SECONDARY,
            BORDER_COLOR, ACCENT_COLOR, BUTTON_BACKGROUND
        )
        
        # Sidebar background
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {SIDEBAR_BACKGROUND};
            }}
            
            QLabel {{
                color: {TEXT_PRIMARY};
            }}
            
            QListWidget {{
                background-color: white;
                border: 1px solid {BORDER_COLOR};
                border-radius: 6px;
                padding: 4px;
                color: {TEXT_PRIMARY};
            }}
            
            QListWidget::item {{
                padding: 8px;
                border-radius: 4px;
            }}
            
            QListWidget::item:selected {{
                background-color: {ACCENT_COLOR};
                color: white;
            }}
            
            QListWidget::item:hover {{
                background-color: #F0F0F0;
            }}
            
            QPushButton {{
                background-color: {BUTTON_BACKGROUND};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER_COLOR};
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 13px;
            }}
            
            QPushButton:hover {{
                background-color: #E8E8E8;
            }}
            
            QPushButton:pressed {{
                background-color: #D0D0D0;
            }}
            
            QPushButton:disabled {{
                background-color: #F5F5F5;
                color: #C0C0C0;
                border: 1px solid #E0E0E0;
            }}
            
            QPushButton#settings_btn {{
                background-color: {ACCENT_COLOR};
                color: white;
                border: none;
                font-weight: bold;
            }}
            
            QPushButton#settings_btn:hover {{
                background-color: #0051D5;
            }}
            
            QPushButton#settings_btn:pressed {{
                background-color: #003DB3;
            }}
            
            QProgressBar {{
                border: 1px solid {BORDER_COLOR};
                border-radius: 6px;
                text-align: center;
                background-color: white;
            }}
            
            QProgressBar::chunk {{
                background-color: {ACCENT_COLOR};
                border-radius: 5px;
            }}
        """)
        
        # Set object name for settings button styling
        self.settings_btn.setObjectName("settings_btn")
    
    # Event handlers
    
    def _on_selection_changed(self):
        """Handle directory selection change"""
        has_selection = len(self.dirs_list.selectedItems()) > 0
        self.remove_btn.setEnabled(has_selection)
    
    def _on_settings_clicked(self):
        """Handle settings button click"""
        logger.info("Settings button clicked")
        self.settings_requested.emit()
    
    # Public methods
    
    def add_directory(self):
        """Open directory picker and add directory"""
        logger.info("Opening directory picker")
        
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Directory to Monitor",
            str(Path.home()),
            QFileDialog.Option.ShowDirsOnly
        )
        
        if directory:
            # Check if already added
            for i in range(self.dirs_list.count()):
                if self.dirs_list.item(i).text() == directory:
                    QMessageBox.information(
                        self,
                        "Directory Already Added",
                        f"The directory '{directory}' is already being monitored."
                    )
                    return
            
            # Add to list
            self.add_directory_to_list(directory)
            
            # Enable re-index button
            self.reindex_btn.setEnabled(True)
            
            # Emit signal
            self.directory_added.emit(directory)
            
            logger.info(f"Directory added: {directory}")
    
    def _on_directory_added(self, directory: str):
        """Handle directory added signal (if needed)"""
        # Index with progress updates
        def update_progress(current, total, message):
            progress = int((current / total) * 100)
            self.set_indexing(True, progress, message)
        
        result = self.indexer.index_directory(
            directory,
            progress_callback=update_progress
        )
            # Update UI
        self.set_indexing(False)
        self.update_file_count(result.chunks_created)

    def add_directory_to_list(self, directory: str):
        """Add directory to list widget (without emitting signal)"""
        item = QListWidgetItem(directory)
        item.setToolTip(directory)
        self.dirs_list.addItem(item)
        
        # Enable re-index button if this is the first directory
        if self.dirs_list.count() > 0:
            self.reindex_btn.setEnabled(True)
    
    def remove_directory(self):
        """Remove selected directory"""
        selected_items = self.dirs_list.selectedItems()
        if not selected_items:
            return
        
        item = selected_items[0]
        directory = item.text()
        
        # Confirm removal
        reply = QMessageBox.question(
            self,
            "Remove Directory",
            f"Remove '{directory}' from monitoring?\n\n"
            "Files from this directory will no longer be searchable.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Remove from index (if indexer is available)
            if hasattr(self, 'indexer') and self.indexer:
                # Get all indexed files from this directory
                indexed_files = self.indexer.get_indexed_files()
                files_to_remove = [
                    f for f in indexed_files 
                    if f.startswith(directory)
                ]
                
                # Remove each file from index
                for filepath in files_to_remove:
                    self.indexer.remove_file(filepath)
                
                logger.info(f"Removed {len(files_to_remove)} files from index for directory: {directory}")
            
            # Remove from list
            self.dirs_list.takeItem(self.dirs_list.row(item))
            
            # Disable re-index button if no directories left
            if self.dirs_list.count() == 0:
                self.reindex_btn.setEnabled(False)
            
            # Emit signal
            self.directory_removed.emit(directory)
            
            logger.info(f"Directory removed: {directory}")
            
    # def remove_directory(self):
    #     """Remove selected directory"""
    #     selected_items = self.dirs_list.selectedItems()
    #     if not selected_items:
    #         return
        
    #     item = selected_items[0]
    #     directory = item.text()
        
    #     # Confirm removal
    #     reply = QMessageBox.question(
    #         self,
    #         "Remove Directory",
    #         f"Remove '{directory}' from monitoring?\n\n"
    #         "Files from this directory will no longer be searchable.",
    #         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
    #         QMessageBox.StandardButton.No
    #     )
        
    #     if reply == QMessageBox.StandardButton.Yes:
    #         # Remove from list
    #         self.dirs_list.takeItem(self.dirs_list.row(item))
            
    #         # Disable re-index button if no directories left
    #         if self.dirs_list.count() == 0:
    #             self.reindex_btn.setEnabled(False)
            
    #         # Emit signal
    #         self.directory_removed.emit(directory)
            
    #         logger.info(f"Directory removed: {directory}")
    
    def reindex_all(self):
        """Request re-indexing of all directories"""
        if self.dirs_list.count() == 0:
            return
        
        # Confirm re-index
        reply = QMessageBox.question(
            self,
            "Re-index All Directories",
            f"Re-index all {self.dirs_list.count()} monitored directories?\n\n"
            "This will update the search index with any new or modified files.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Emit signal
            self.reindex_requested.emit()
            
            logger.info("Re-index requested for all directories")
    
    def set_indexing(self, is_indexing: bool, progress: int = 0, message: str = ""):
        """Update indexing status display"""
        self._is_indexing = is_indexing
        
        if is_indexing:
            # Show progress bar and status
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(progress)
            self.progress_label.setVisible(True)
            self.progress_label.setText(message)
            
            # Disable buttons during indexing
            self.add_btn.setEnabled(False)
            self.remove_btn.setEnabled(False)
            self.reindex_btn.setEnabled(False)
        else:
            # Hide progress bar and status
            self.progress_bar.setVisible(False)
            self.progress_label.setVisible(False)
            
            # Re-enable buttons
            self.add_btn.setEnabled(True)
            has_selection = len(self.dirs_list.selectedItems()) > 0
            self.remove_btn.setEnabled(has_selection)
            has_directories = self.dirs_list.count() > 0
            self.reindex_btn.setEnabled(has_directories)
    
    def update_file_count(self, count: int):
        """Update indexed file count display"""
        if count == 0:
            self.file_count_label.setText("No files indexed")
        elif count == 1:
            self.file_count_label.setText("1 file indexed")
        else:
            self.file_count_label.setText(f"{count:,} files indexed")
    
    def update_last_indexed(self, timestamp: str):
        """Update last indexed timestamp"""
        if timestamp:
            self.last_indexed_label.setText(f"Last indexed: {timestamp}")
        else:
            self.last_indexed_label.setText("Never indexed")
    
    def get_directories(self):
        """Get list of all monitored directories"""
        directories = []
        for i in range(self.dirs_list.count()):
            directories.append(self.dirs_list.item(i).text())
        return directories
    
    def clear_directories(self):
        """Clear all directories from list"""
        self.dirs_list.clear()
        self.reindex_btn.setEnabled(False)