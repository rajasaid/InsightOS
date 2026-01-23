"""
ui/generated_files_browser.py
Widget for browsing and managing AI-generated files
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget,
    QTreeWidgetItem, QPushButton, QLabel, QTextEdit,
    QMenu, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QFileSystemWatcher
from PyQt6.QtGui import QIcon, QAction
from pathlib import Path
from datetime import datetime
import os
import subprocess
import platform

from mcp_servers import get_mcp_config
from ui.styles.colors import (
    BACKGROUND, TEXT_PRIMARY, TEXT_SECONDARY,
    ACCENT_COLOR, BORDER_COLOR
)
from ui.styles.fonts import get_text_font, SIZE_BODY, WEIGHT_BOLD
from utils.logger import get_logger

logger = get_logger(__name__)


class GeneratedFilesBrowser(QWidget):
    """Widget for browsing AI-generated files"""
    
    # Signals
    file_opened = pyqtSignal(Path)  # Emitted when file is opened
    file_selected = pyqtSignal(Path)  # Emitted when file is selected
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.mcp_config = get_mcp_config()
        self.output_dir = self.mcp_config.get_output_dir()
        
        # File system watcher for auto-refresh
        self.file_watcher = QFileSystemWatcher()
        if self.output_dir.exists():
            self.file_watcher.addPath(str(self.output_dir))
            self.file_watcher.directoryChanged.connect(self._on_directory_changed)
        
        self._setup_ui()
        self._apply_styles()
        self.refresh_files()
        
        logger.info(f"Generated files browser initialized for: {self.output_dir}")
    
    def _setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # === Header ===
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        # Title
        title_label = QLabel("Generated Files")
        title_label.setFont(get_text_font(SIZE_BODY, WEIGHT_BOLD))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Refresh button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_files)
        self.refresh_btn.setToolTip("Refresh file list")
        header_layout.addWidget(self.refresh_btn)
        
        # Open folder button
        self.open_folder_btn = QPushButton("Open Folder")
        self.open_folder_btn.clicked.connect(self.open_output_folder)
        self.open_folder_btn.setToolTip("Open output folder in file explorer")
        header_layout.addWidget(self.open_folder_btn)
        
        layout.addLayout(header_layout)
        
        # === File Tree ===
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Name", "Size", "Modified"])
        self.tree.setColumnWidth(0, 200)
        self.tree.setColumnWidth(1, 80)
        self.tree.setColumnWidth(2, 120)
        
        # Enable context menu
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        
        # Connect signals
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.tree.itemSelectionChanged.connect(self._on_selection_changed)
        
        layout.addWidget(self.tree, stretch=1)
        
        # === Info Label ===
        self.info_label = QLabel(f"Location: {self.output_dir}")
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        layout.addWidget(self.info_label)
    
    def _apply_styles(self):
        """Apply styling"""
        self.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {BACKGROUND};
                border: 1px solid {BORDER_COLOR};
                border-radius: 4px;
                font-size: 12px;
            }}
            
            QTreeWidget::item {{
                padding: 4px;
            }}
            
            QTreeWidget::item:selected {{
                background-color: {ACCENT_COLOR};
                color: white;
            }}
            
            QTreeWidget::item:hover {{
                background-color: #E8E8E8;
            }}
            
            QPushButton {{
                background-color: #F0F0F0;
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER_COLOR};
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 12px;
            }}
            
            QPushButton:hover {{
                background-color: #E8E8E8;
            }}
            
            QPushButton:pressed {{
                background-color: #D0D0D0;
            }}
        """)
    
    def refresh_files(self):
        """Refresh the file tree (show ALL folders and files under output_dir)."""
        self.tree.clear()

        # Ensure output directory exists
        if not self.output_dir.exists():
            self.output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created output directory: {self.output_dir}")

        # Keep watcher in sync with actual folders
        self._sync_watcher_dirs(self.output_dir)

        # Root node
        root_item = QTreeWidgetItem(self.tree)
        root_item.setText(0, f"📁 {self.output_dir.name}")
        root_item.setData(0, Qt.ItemDataRole.UserRole, self.output_dir)
        root_item.setFont(0, get_text_font(SIZE_BODY, WEIGHT_BOLD))

        total_files = self._add_dir_to_tree(root_item, self.output_dir)
        root_item.setText(0, f"📁 {self.output_dir.name} ({total_files})")
        root_item.setExpanded(True)

        # Update info label
        self.info_label.setText(
            f"Location: {self.output_dir} | {total_files} file(s)"
        )

        logger.debug(f"Refreshed file browser: {total_files} files found")

    def _iter_dirs_recursive(self, root: Path) -> list[Path]:
        """Return all directories under root (including root)."""
        dirs = []
        try:
            for p in root.rglob("*"):
                if p.is_dir():
                    dirs.append(p)
        except Exception as e:
            logger.error(f"Error walking directory tree: {e}")
        return [root] + dirs


    def _sync_watcher_dirs(self, root: Path):
        """Ensure watcher tracks all directories under root (best effort)."""
        try:
            desired = set(str(p) for p in self._iter_dirs_recursive(root))
            current = set(self.file_watcher.directories())

            to_add = list(desired - current)
            to_remove = list(current - desired)

            if to_remove:
                self.file_watcher.removePaths(to_remove)

            # QFileSystemWatcher can have OS limits; add best effort
            if to_add:
                self.file_watcher.addPaths(to_add)

        except Exception as e:
            logger.warning(f"Failed to sync file watcher directories: {e}")


    def _add_dir_to_tree(self, parent_item: QTreeWidgetItem, directory: Path) -> int:
        """
        Add a directory node and all its children to the tree.
        Returns number of files added under this directory (recursive).
        """
        file_count = 0

        # List children (dirs first, then files), sorted by name
        try:
            children = list(directory.iterdir())
        except Exception as e:
            logger.error(f"Error listing directory {directory}: {e}")
            return 0

        dirs = sorted([c for c in children if c.is_dir()], key=lambda p: p.name.lower())
        files = sorted([c for c in children if c.is_file()], key=lambda p: p.name.lower())

        # Add subdirectories
        for d in dirs:
            dir_item = QTreeWidgetItem(parent_item)
            dir_item.setText(0, f"📁 {d.name}")
            dir_item.setData(0, Qt.ItemDataRole.UserRole, d)
            dir_item.setFont(0, get_text_font(SIZE_BODY, WEIGHT_BOLD))

            # Recurse
            sub_count = self._add_dir_to_tree(dir_item, d)
            if sub_count > 0:
                dir_item.setText(0, f"📁 {d.name} ({sub_count})")
            # Expand folders by default if you want
            dir_item.setExpanded(True)

            file_count += sub_count

        # Add files
        for f in files:
            try:
                st = f.stat()
            except Exception:
                # Skip unreadable entries gracefully
                continue

            file_item = QTreeWidgetItem(parent_item)
            icon = self._get_file_icon(f)
            file_item.setText(0, f"{icon} {f.name}")
            file_item.setText(1, self._format_size(st.st_size))
            file_item.setText(2, self._format_time(st.st_mtime))
            file_item.setData(0, Qt.ItemDataRole.UserRole, f)
            file_count += 1

        return file_count

    def _get_file_icon(self, filepath: Path) -> str:
        """Get icon emoji for file type"""
        ext = filepath.suffix.lower()
        
        icon_map = {
            '.md': '📝',
            '.txt': '📄',
            '.pdf': '📕',
            '.docx': '📘',
            '.doc': '📘',
            '.csv': '📊',
            '.xlsx': '📊',
            '.json': '🔧',
            '.html': '🌐',
            '.py': '🐍',
        }
        
        return icon_map.get(ext, '📄')
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
    
    def _format_time(self, timestamp: float) -> str:
        """Format timestamp to readable string"""
        dt = datetime.fromtimestamp(timestamp)
        
        # Show relative time for recent files
        now = datetime.now()
        diff = now - dt
        
        if diff.days == 0:
            if diff.seconds < 60:
                return "Just now"
            elif diff.seconds < 3600:
                mins = diff.seconds // 60
                return f"{mins} min ago"
            else:
                hours = diff.seconds // 3600
                return f"{hours}h ago"
        elif diff.days == 1:
            return "Yesterday"
        elif diff.days < 7:
            return f"{diff.days} days ago"
        else:
            return dt.strftime("%Y-%m-%d %H:%M")
    
    def _on_item_double_clicked(self, item, column):
        """Handle double-click on item"""
        filepath = item.data(0, Qt.ItemDataRole.UserRole)
        
        if isinstance(filepath, Path) and filepath.is_file():
            self.open_file(filepath)
    
    def _on_selection_changed(self):
        """Handle selection change"""
        selected_items = self.tree.selectedItems()
        
        if selected_items:
            item = selected_items[0]
            filepath = item.data(0, Qt.ItemDataRole.UserRole)
            
            if isinstance(filepath, Path) and filepath.is_file():
                self.file_selected.emit(filepath)
    
    def _show_context_menu(self, position):
        """Show context menu for file operations"""
        item = self.tree.itemAt(position)
        
        if not item:
            return
        
        filepath = item.data(0, Qt.ItemDataRole.UserRole)
        
        if not isinstance(filepath, Path) or not filepath.is_file():
            return
        
        # Create context menu
        menu = QMenu(self)
        
        # Open action
        open_action = QAction("Open", self)
        open_action.triggered.connect(lambda: self.open_file(filepath))
        menu.addAction(open_action)
        
        # Open with action
        open_with_action = QAction("Open With...", self)
        open_with_action.triggered.connect(lambda: self.open_file_with(filepath))
        menu.addAction(open_with_action)
        
        menu.addSeparator()
        
        # Show in folder action
        show_action = QAction("Show in Folder", self)
        show_action.triggered.connect(lambda: self.show_in_folder(filepath))
        menu.addAction(show_action)
        
        # Copy path action
        copy_path_action = QAction("Copy Path", self)
        copy_path_action.triggered.connect(lambda: self.copy_path(filepath))
        menu.addAction(copy_path_action)
        
        menu.addSeparator()
        
        # Delete action
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self.delete_file(filepath))
        menu.addAction(delete_action)
        
        # Show menu
        menu.exec(self.tree.viewport().mapToGlobal(position))
    
    def open_file(self, filepath: Path):
        """Open file with default application"""
        try:
            if platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', str(filepath)], check=True)
            elif platform.system() == 'Windows':
                os.startfile(str(filepath))
            else:  # Linux
                subprocess.run(['xdg-open', str(filepath)], check=True)
            
            self.file_opened.emit(filepath)
            logger.info(f"Opened file: {filepath}")
            
        except Exception as e:
            logger.error(f"Error opening file {filepath}: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to open file:\n{str(e)}"
            )
    
    def open_file_with(self, filepath: Path):
        """Open file with application chooser"""
        try:
            if platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', '-a', 'Finder', str(filepath)], check=True)
            elif platform.system() == 'Windows':
                # Windows "Open With" dialog
                subprocess.run(['rundll32.exe', 'shell32.dll,OpenAs_RunDLL', str(filepath)], check=True)
            else:  # Linux
                # Try to use file manager
                subprocess.run(['xdg-open', str(filepath.parent)], check=True)
            
            logger.info(f"Opened file with chooser: {filepath}")
            
        except Exception as e:
            logger.error(f"Error opening file with chooser {filepath}: {e}")
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to open file chooser:\n{str(e)}"
            )
    
    def show_in_folder(self, filepath: Path):
        """Show file in file explorer/finder"""
        try:
            if platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', '-R', str(filepath)], check=True)
            elif platform.system() == 'Windows':
                subprocess.run(['explorer', '/select,', str(filepath)], check=True)
            else:  # Linux
                # Open parent directory
                subprocess.run(['xdg-open', str(filepath.parent)], check=True)
            
            logger.info(f"Showed file in folder: {filepath}")
            
        except Exception as e:
            logger.error(f"Error showing file in folder {filepath}: {e}")
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to show file in folder:\n{str(e)}"
            )
    
    def copy_path(self, filepath: Path):
        """Copy file path to clipboard"""
        from PyQt6.QtWidgets import QApplication
        
        clipboard = QApplication.clipboard()
        clipboard.setText(str(filepath))
        
        logger.info(f"Copied path to clipboard: {filepath}")
    
    def delete_file(self, filepath: Path):
        """Delete file after confirmation"""
        reply = QMessageBox.question(
            self,
            "Delete File",
            f"Are you sure you want to delete this file?\n\n{filepath.name}\n\n"
            "This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                filepath.unlink()
                logger.info(f"Deleted file: {filepath}")
                
                # Refresh the tree
                self.refresh_files()
                
                QMessageBox.information(
                    self,
                    "File Deleted",
                    f"File deleted successfully:\n{filepath.name}"
                )
                
            except Exception as e:
                logger.error(f"Error deleting file {filepath}: {e}")
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to delete file:\n{str(e)}"
                )
    
    def open_output_folder(self):
        """Open output folder in file explorer"""
        try:
            if platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', str(self.output_dir)], check=True)
            elif platform.system() == 'Windows':
                os.startfile(str(self.output_dir))
            else:  # Linux
                subprocess.run(['xdg-open', str(self.output_dir)], check=True)
            
            logger.info(f"Opened output folder: {self.output_dir}")
            
        except Exception as e:
            logger.error(f"Error opening output folder: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to open output folder:\n{str(e)}"
            )
    
    def _on_directory_changed(self, path):
        """Handle directory change from file watcher"""
        logger.debug(f"Directory changed: {path}")
        # Auto-refresh after a short delay (avoid too frequent refreshes)
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(500, self.refresh_files)
    
    def get_selected_file(self) -> Path | None:
        """Get currently selected file path"""
        selected_items = self.tree.selectedItems()
        
        if selected_items:
            item = selected_items[0]
            filepath = item.data(0, Qt.ItemDataRole.UserRole)
            
            if isinstance(filepath, Path) and filepath.is_file():
                return filepath
        
        return None
    
    def clear_selection(self):
        """Clear file selection"""
        self.tree.clearSelection()
    
    def closeEvent(self, event):
        """Clean up file watcher on close"""
        self.file_watcher.removePaths(self.file_watcher.directories())
        super().closeEvent(event)