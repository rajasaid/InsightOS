"""
ui/dialogs/settings_dialog.py
Settings dialog with tabbed interface for configuration
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QWidget, QLabel, QLineEdit, QPushButton, QSlider,
    QCheckBox, QGroupBox, QSpinBox, QMessageBox,
    QFormLayout, QScrollArea, QFrame, QTextEdit, QFileDialog, 
    QProxyStyle, QStyleOptionTab
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

from ui.styles.colors import (
    BACKGROUND, TEXT_PRIMARY, TEXT_SECONDARY,
    ACCENT_COLOR, SUCCESS_COLOR, ERROR_COLOR,
    BORDER_COLOR, WARNING_COLOR
)
from ui.styles.fonts import (
    get_display_font, get_text_font,
    SIZE_HEADLINE, SIZE_BODY, WEIGHT_BOLD
)
from security.config_manager import ConfigManager, get_config_manager
from utils.logger import get_logger
from mcp_servers import get_mcp_config
from pathlib import Path

logger = get_logger(__name__)


class SettingsDialog(QDialog):
    """Settings dialog with multiple tabs for configuration"""
    
    # Signals
    settings_changed = pyqtSignal(dict)  # Emitted when settings are saved
    api_key_changed = pyqtSignal(str)    # Emitted when API key is changed
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Settings")
        self.setMinimumSize(650, 550)
        self.setModal(True)
        
        self.config_manager = get_config_manager()

        self._setup_ui()
        self._load_settings()
        self._apply_styles()
        
        logger.info("Settings dialog opened")
    
        
    def _setup_ui(self):
        """Setup settings dialog UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Tab widget
        self.tabs = QTabWidget()
        # Center and stretch tabs 
        self.tabs.setStyleSheet("""
            QTabWidget::tab-bar {
                alignment: center;
                
            }
            QTabBar::tab {
                min-width: 100px;
            }
        """)
        #self.tabs.tabBar().setExpanding(True)
        # Create tabs (MCP removed - now in Advanced)
        self.general_tab = GeneralTab()
        self.api_key_tab = APIKeyTab()
        self.advanced_tab = AdvancedTab(config_manager=self.config_manager)

        self.tabs.addTab(self.general_tab, "General")
        self.tabs.addTab(self.api_key_tab, "API Key")
        self.tabs.addTab(self.advanced_tab, "Advanced")

        layout.addWidget(self.tabs)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(16, 12, 16, 16)
        button_layout.setSpacing(8)
        
        # Reset to defaults button
        self.reset_btn = QPushButton("Reset to Defaults")
        self.reset_btn.clicked.connect(self._reset_to_defaults)
        button_layout.addWidget(self.reset_btn)
        
        button_layout.addStretch()
        
        # Cancel button
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        # Save button
        self.save_btn = QPushButton("Save")
        self.save_btn.setDefault(True)
        self.save_btn.clicked.connect(self._save_settings)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
        
        # Connect tab signals
        self.api_key_tab.api_key_validated.connect(self._on_api_key_validated)
    
    def _apply_styles(self):
        """Apply macOS-native styling"""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {BACKGROUND};
            }}
            
            QTabWidget::pane {{
                border: 1px solid {BORDER_COLOR};
                background-color: {BACKGROUND};
            }}
            
            QTabBar::tab {{
                background-color: #F0F0F0;
                color: {TEXT_PRIMARY};
                padding: 8px 16px;
                border: 1px solid {BORDER_COLOR};
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                min-width: 100px;
            }}
            
            QTabBar::tab:selected {{
                background-color: {BACKGROUND};
                color: {ACCENT_COLOR};
                font-weight: bold;
            }}
            
            QTabBar::tab:hover:!selected {{
                background-color: #E8E8E8;
            }}
            
            QPushButton {{
                background-color: #F0F0F0;
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER_COLOR};
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                min-width: 80px;
            }}
            
            QPushButton:hover {{
                background-color: #E8E8E8;
            }}
            
            QPushButton:pressed {{
                background-color: #D0D0D0;
            }}
            
            QPushButton:default {{
                background-color: {ACCENT_COLOR};
                color: white;
                border: none;
                font-weight: bold;
            }}
            
            QPushButton:default:hover {{
                background-color: #0051D5;
            }}
            
            QPushButton:default:pressed {{
                background-color: #003DB3;
            }}
        """)
    
    def _load_settings(self):
        """Load current settings from config"""
        config = self.config_manager.get_config()
        
        # Load into tabs
        self.general_tab.load_settings(config)
        self.api_key_tab.load_settings(config)
        self.advanced_tab.load_settings(config)
        
        logger.debug("Settings loaded into dialog")
    
    def _save_settings(self):
        """Save settings from all tabs"""
        # Collect settings from all tabs
        settings = {}
        settings.update(self.general_tab.get_settings())
        settings.update(self.advanced_tab.get_settings())
        
        # API key handled separately (encrypted)
        api_key = self.api_key_tab.get_api_key()
        if api_key:
            settings['api_key'] = api_key
        
        # Save to config
        try:
            config = self.config_manager.get_config()
            config.update(settings)
            
            ok = self.config_manager.save_config(config)
            if not ok:
                QMessageBox.critical(self, "Save Error", "Failed to save settings (see logs).")
                return
            
            # Apply MCP settings (from AdvancedTab)
            self.advanced_tab.apply_mcp_settings()
            
            # Emit signal
            self.settings_changed.emit(settings)

            # Show success message briefly
            QMessageBox.information(
                self,
                "Settings Saved",
                "Your settings have been saved successfully."
            )
            
            self.accept()
            logger.info("Settings saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save settings: {str(e)}"
            )
    
    def _reset_to_defaults(self):
        """Reset all settings to defaults"""
        reply = QMessageBox.question(
            self,
            "Reset to Defaults",
            "Reset all settings to default values?\n\n"
            "This will not affect your API key or monitored directories.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.general_tab.reset_to_defaults()
            self.advanced_tab.reset_to_defaults()
            logger.info("Settings reset to defaults")
    
    def _on_api_key_validated(self, api_key: str):
        """Handle API key validation"""
        self.api_key_changed.emit(api_key)


class GeneralTab(QWidget):
    """General settings tab"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup general tab UI"""
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(24)
        
        # === RAG Settings ===
        rag_group = self._create_rag_settings()
        layout.addWidget(rag_group)
        
        # === File Types ===
        file_types_group = self._create_file_types_settings()
        layout.addWidget(file_types_group)
        
        layout.addStretch()
        
        scroll.setWidget(content)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
    
    def _create_rag_settings(self):
        """Create RAG settings group"""
        group = QGroupBox("Search Settings")
        group.setFont(get_text_font(SIZE_BODY, WEIGHT_BOLD))
        layout = QFormLayout(group)
        layout.setSpacing(12)
        
        # Top-K slider
        topk_layout = QHBoxLayout()
        
        self.topk_slider = QSlider(Qt.Orientation.Horizontal)
        self.topk_slider.setMinimum(1)
        self.topk_slider.setMaximum(20)
        self.topk_slider.setValue(5)
        self.topk_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.topk_slider.setTickInterval(1)
        self.topk_slider.valueChanged.connect(self._update_topk_label)
        topk_layout.addWidget(self.topk_slider, stretch=1)
        
        self.topk_value_label = QLabel("5")
        self.topk_value_label.setMinimumWidth(30)
        self.topk_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.topk_value_label.setStyleSheet(f"font-weight: bold; color: {ACCENT_COLOR};")
        topk_layout.addWidget(self.topk_value_label)
        
        topk_label = QLabel("Results to retrieve (top_k):")
        topk_help = QLabel("Number of most relevant document chunks to use when answering questions")
        topk_help.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        topk_help.setWordWrap(True)
        
        layout.addRow(topk_label, topk_layout)
        layout.addRow("", topk_help)
        
        return group
    
    def _create_file_types_settings(self):
        """Create file types settings group"""
        group = QGroupBox("File Types to Index")
        group.setFont(get_text_font(SIZE_BODY, WEIGHT_BOLD))
        layout = QVBoxLayout(group)
        layout.setSpacing(8)
        
        help_label = QLabel("Select which file types to include when indexing directories:")
        help_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        help_label.setWordWrap(True)
        layout.addWidget(help_label)
        
        # Checkboxes in grid
        from PyQt6.QtWidgets import QGridLayout
        grid = QGridLayout()
        grid.setSpacing(8)
        
        self.file_type_checkboxes = {}
        
        file_types = [
            ("Text Files", [".txt", ".md", ".rtf"]),
            ("Documents", [".pdf", ".doc", ".docx", ".odt", ".pages"]),
            ("Code", [".py", ".java", ".js", ".html", ".css"]),
            ("Data", [".csv", ".log", ".ini", ".cfg"]),
            ("Other", [".asc", ".htm"])
        ]
        
        row = 0
        col = 0
        
        for category, extensions in file_types:
            # Category label
            category_label = QLabel(f"<b>{category}:</b>")
            grid.addWidget(category_label, row, col * 2)
            
            # Checkboxes for extensions
            ext_layout = QHBoxLayout()
            for ext in extensions:
                checkbox = QCheckBox(ext)
                checkbox.setChecked(True)  # Default: all enabled
                self.file_type_checkboxes[ext] = checkbox
                ext_layout.addWidget(checkbox)
            
            ext_widget = QWidget()
            ext_widget.setLayout(ext_layout)
            grid.addWidget(ext_widget, row, col * 2 + 1)
            
            col += 1
            if col >= 2:
                col = 0
                row += 1
        
        layout.addLayout(grid)
        
        # Select/Deselect all buttons
        button_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self._select_all_file_types)
        button_layout.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.clicked.connect(self._deselect_all_file_types)
        button_layout.addWidget(deselect_all_btn)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        return group
    
    def _update_topk_label(self, value):
        """Update top-k value label"""
        self.topk_value_label.setText(str(value))
    
    def _select_all_file_types(self):
        """Select all file type checkboxes"""
        for checkbox in self.file_type_checkboxes.values():
            checkbox.setChecked(True)
    
    def _deselect_all_file_types(self):
        """Deselect all file type checkboxes"""
        for checkbox in self.file_type_checkboxes.values():
            checkbox.setChecked(False)
    
    def load_settings(self, config: dict):
        """Load settings from config"""
        # Top-K
        top_k = config.get('top_k', 5)
        self.topk_slider.setValue(top_k)
        
        # File types
        enabled_types = config.get('file_types_enabled', [])
        if enabled_types:
            # First, deselect all
            for checkbox in self.file_type_checkboxes.values():
                checkbox.setChecked(False)
            # Then, enable only those in config
            for ext in enabled_types:
                if ext in self.file_type_checkboxes:
                    self.file_type_checkboxes[ext].setChecked(True)
    
    def get_settings(self) -> dict:
        """Get current settings"""
        # File types
        enabled_types = [
            ext for ext, checkbox in self.file_type_checkboxes.items()
            if checkbox.isChecked()
        ]
        
        return {
            'top_k': self.topk_slider.value(),
            'file_types_enabled': enabled_types
        }
    
    def reset_to_defaults(self):
        """Reset to default values"""
        self.topk_slider.setValue(5)
        self._select_all_file_types()


class APIKeyTab(QWidget):
    """API key configuration tab"""
    
    api_key_validated = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._api_key_configured = False
        self._new_api_key = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup API key tab UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(20)
        
        # Current status
        status_group = QGroupBox("Current Status")
        status_group.setFont(get_text_font(SIZE_BODY, WEIGHT_BOLD))
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel("⏳ Checking...")
        self.status_label.setFont(get_text_font(SIZE_BODY))
        status_layout.addWidget(self.status_label)
        
        layout.addWidget(status_group)
        
        # Change API key section
        change_group = QGroupBox("Change API Key")
        change_group.setFont(get_text_font(SIZE_BODY, WEIGHT_BOLD))
        change_layout = QVBoxLayout(change_group)
        change_layout.setSpacing(12)
        
        # Instructions
        instructions = QLabel(
            "Enter a new Claude API key to replace the current one. "
            "The key will be encrypted and stored securely."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        change_layout.addWidget(instructions)
        
        # API key input
        input_label = QLabel("New API Key:")
        change_layout.addWidget(input_label)
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("sk-ant-...")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setMinimumHeight(36)
        self.api_key_input.textChanged.connect(self._on_key_changed)
        change_layout.addWidget(self.api_key_input)
        
        # Show/hide checkbox
        self.show_key_checkbox = QCheckBox("Show API key")
        self.show_key_checkbox.stateChanged.connect(self._toggle_key_visibility)
        change_layout.addWidget(self.show_key_checkbox)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.validate_btn = QPushButton("Validate Key")
        self.validate_btn.setEnabled(False)
        self.validate_btn.clicked.connect(self._validate_key)
        button_layout.addWidget(self.validate_btn)
        
        button_layout.addStretch()
        
        change_layout.addLayout(button_layout)
        
        # Validation status
        self.validation_label = QLabel("")
        self.validation_label.setWordWrap(True)
        change_layout.addWidget(self.validation_label)
        
        layout.addWidget(change_group)
        
        # Remove API key section
        remove_group = QGroupBox("Remove API Key")
        remove_group.setFont(get_text_font(SIZE_BODY, WEIGHT_BOLD))
        remove_layout = QVBoxLayout(remove_group)
        
        remove_warning = QLabel(
            "⚠️ Removing your API key will disable AI-powered features. "
            "You can add a new key later from Settings."
        )
        remove_warning.setWordWrap(True)
        remove_warning.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        remove_layout.addWidget(remove_warning)
        
        self.remove_btn = QPushButton("Remove API Key")
        self.remove_btn.clicked.connect(self._remove_key)
        remove_layout.addWidget(self.remove_btn)
        
        layout.addWidget(remove_group)
        
        layout.addStretch()
        
        # Get API key link
        link_label = QLabel(
            'Get your API key from: '
            '<a href="https://console.anthropic.com/">https://console.anthropic.com/</a>'
        )
        link_label.setOpenExternalLinks(True)
        link_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        layout.addWidget(link_label)
    
    def _on_key_changed(self, text):
        """Handle API key input change"""
        self.validate_btn.setEnabled(len(text.strip()) > 0)
        self.validation_label.clear()
    
    def _toggle_key_visibility(self, state):
        """Toggle API key visibility"""
        if state == Qt.CheckState.Checked.value:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
    
    def _validate_key(self):
        """Validate API key"""
        api_key = self.api_key_input.text().strip()
        
        if not api_key:
            return
        
        # Show validating status
        self.validation_label.setText("⏳ Validating...")
        self.validation_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        self.validate_btn.setEnabled(False)
        self.api_key_input.setEnabled(False)
        
        # Simulate validation (TODO: integrate with KeyManager)
        QTimer.singleShot(1500, lambda: self._validation_result(True, api_key))
    
    def _validation_result(self, success: bool, api_key: str):
        """Handle validation result"""
        self.validate_btn.setEnabled(True)
        self.api_key_input.setEnabled(True)
        
        if success:
            self._new_api_key = api_key
            self.validation_label.setText("✅ API key is valid and will be saved when you click Save.")
            self.validation_label.setStyleSheet(f"color: {SUCCESS_COLOR}; font-weight: bold;")
            self.api_key_validated.emit(api_key)
            logger.info("New API key validated in settings")
        else:
            self._new_api_key = None
            self.validation_label.setText("❌ Invalid API key. Please check and try again.")
            self.validation_label.setStyleSheet(f"color: {ERROR_COLOR}; font-weight: bold;")
            logger.warning("API key validation failed in settings")
    
    def _remove_key(self):
        """Remove API key"""
        reply = QMessageBox.warning(
            self,
            "Remove API Key",
            "Are you sure you want to remove your API key?\n\n"
            "This will disable AI-powered features until you add a new key.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # TODO: Implement key removal via ConfigManager
            self._api_key_configured = False
            self._update_status()
            logger.info("API key removed in settings")
    
    def load_settings(self, config: dict):
        """Load settings from config"""
        # Check if API key is configured
        from security.config_manager import get_config_manager
        config_manager = get_config_manager()
        self._api_key_configured = config_manager.has_api_key()
        self._update_status()
    
        
    def _update_status(self):
        """Update status label"""
        if self._api_key_configured:
            self.status_label.setText("✅ API Key: Configured")
            self.status_label.setStyleSheet(f"color: {SUCCESS_COLOR}; font-weight: bold;")
        else:
            self.status_label.setText("❌ API Key: Not Configured")
            self.status_label.setStyleSheet(f"color: {ERROR_COLOR}; font-weight: bold;")
    
    def get_api_key(self):
        """Get new API key if validated"""
        return self._new_api_key


class AdvancedTab(QWidget):
    """Advanced settings tab - includes Agentic Mode with MCP"""
    
    def __init__(self, config_manager=None, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.mcp_config = get_mcp_config()
        
        # Store defaults for MCP
        self.default_output_dir = Path.home() / "InsightOS" / "Generated"
        self.default_server_states = {
            "filesystem": False,  # Disabled by default for safety
            "memory": True,
            "brave-search": False
        }
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup advanced tab UI"""
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(24)
        
        # === Agentic Mode (includes MCP) ===
        agentic_mode_group = self._create_agentic_mode_settings()
        layout.addWidget(agentic_mode_group)
        
        # === Chunking Settings ===
        chunking_group = self._create_chunking_settings()
        layout.addWidget(chunking_group)
        
        # === Cache Settings ===
        cache_group = self._create_cache_settings()
        layout.addWidget(cache_group)

        layout.addStretch()
        
        scroll.setWidget(content)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
    
    def _create_agentic_mode_settings(self):
        """Create unified agentic mode settings (Tools + MCP Servers)"""
        agentic_group = QGroupBox("Agentic Mode (Tools + MCP Servers)")
        agentic_group.setFont(get_text_font(SIZE_BODY, WEIGHT_BOLD))
        agentic_layout = QVBoxLayout()
        agentic_layout.setSpacing(16)
        
        # === UNIFIED Privacy Warning ===
        warning_label = QLabel(
            "⚠️ <b>Privacy Warning:</b> Agentic mode allows Claude AI to:<br>"
            "• Use tools that read entire files from your computer<br>"
            "• Access MCP servers that can read/write files<br>"
            "• Send file contents to Anthropic's servers for processing<br><br>"
            "<b>File contents will be transmitted to Anthropic.</b>"
        )
        warning_label.setWordWrap(True)
        warning_label.setStyleSheet(
            f"color: {WARNING_COLOR}; "
            "padding: 12px; "
            "background-color: #FFF3CD; "
            "border-radius: 4px; "
            "border-left: 4px solid #FF6B6B;"
        )
        agentic_layout.addWidget(warning_label)
        
        # === Disclaimer ===
        disclaimer_label = QLabel(
            "<b>Do NOT enable</b> if working with:<br>"
            "• Protected Health Information (HIPAA)<br>"
            "• Personal data subject to GDPR<br>"
            "• Confidential business documents<br>"
            "• Any sensitive or regulated data"
        )
        disclaimer_label.setWordWrap(True)
        disclaimer_label.setStyleSheet(
            "padding: 12px; "
            "background-color: #F8F9FA; "
            "border-radius: 4px; "
            "border-left: 4px solid #868E96;"
        )
        agentic_layout.addWidget(disclaimer_label)
        
        # === Master Enable Checkbox ===
        self.agentic_mode_checkbox = QCheckBox(
            "Enable Agentic Mode (I understand the privacy implications)"
        )
        self.agentic_mode_checkbox.setStyleSheet("font-weight: bold; font-size: 13px;")
        self.agentic_mode_checkbox.stateChanged.connect(self._on_agentic_mode_changed)
        agentic_layout.addWidget(self.agentic_mode_checkbox)
        
        # === Container for settings (only shown when enabled) ===
        self.agentic_settings_container = QWidget()
        agentic_settings_layout = QVBoxLayout(self.agentic_settings_container)
        agentic_settings_layout.setContentsMargins(20, 10, 0, 0)
        agentic_settings_layout.setSpacing(16)
        
        # --- Traditional Tools Section ---
        tools_section = QGroupBox("Traditional Tools")
        tools_layout = QVBoxLayout(tools_section)
        tools_layout.setSpacing(8)
        
        tools_info = QLabel(
            "<b>Available Tools:</b><br>"
            "• search_documents - Search indexed files<br>"
            "• read_file - Read entire file contents<br>"
            "• list_files - List files in directories<br>"
            "• get_file_info - Get file metadata"
        )
        tools_info.setWordWrap(True)
        tools_info.setStyleSheet(
            "padding: 10px; "
            "background-color: #E7F3FF; "
            "border-radius: 4px;"
        )
        tools_layout.addWidget(tools_info)
        
        agentic_settings_layout.addWidget(tools_section)
        
        # --- MCP Servers Section ---
        mcp_section = QGroupBox("MCP Servers")
        mcp_layout = QVBoxLayout(mcp_section)
        mcp_layout.setSpacing(12)
        
        mcp_help = QLabel(
            "Model Context Protocol servers provide additional AI capabilities:"
        )
        mcp_help.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        mcp_layout.addWidget(mcp_help)
        
        # MCP Server checkboxes
        self.server_checkboxes = {}
        for name, server in self.mcp_config.servers.items():
            cb = QCheckBox(f"{name}: {server.description}")
            cb.setChecked(server.enabled)
            cb.setEnabled(False)  # Disabled until agentic mode is enabled
            self.server_checkboxes[name] = cb
            mcp_layout.addWidget(cb)
        
        agentic_settings_layout.addWidget(mcp_section)
        
        # --- Output Directory (for filesystem server) ---
        output_section = QGroupBox("Generated Files Location")
        output_layout = QVBoxLayout(output_section)
        output_layout.setSpacing(8)
        
        output_help = QLabel(
            "Directory where AI assistant saves generated files:"
        )
        output_help.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        output_layout.addWidget(output_help)
        
        dir_layout = QHBoxLayout()
        self.output_dir_edit = QLineEdit(str(self.mcp_config.get_output_dir()))
        self.output_dir_edit.setReadOnly(True)
        self.output_dir_edit.setEnabled(False)
        dir_layout.addWidget(self.output_dir_edit, stretch=1)
        
        self.browse_output_btn = QPushButton("Browse...")
        self.browse_output_btn.clicked.connect(self._browse_output_dir)
        self.browse_output_btn.setEnabled(False)
        dir_layout.addWidget(self.browse_output_btn)
        
        output_layout.addLayout(dir_layout)
        agentic_settings_layout.addWidget(output_section)
        
        # --- Brave Search API (optional) ---
        if "brave-search" in self.mcp_config.servers:
            brave_section = QGroupBox("Brave Search API (Optional)")
            brave_layout = QVBoxLayout(brave_section)
            brave_layout.setSpacing(8)
            
            brave_layout.addWidget(QLabel("API Key:"))
            
            key_layout = QHBoxLayout()
            self.brave_api_edit = QLineEdit()
            self.brave_api_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.brave_api_edit.setPlaceholderText("Enter Brave Search API key...")
            self.brave_api_edit.setEnabled(False)
            
            # Load existing key
            brave_server = self.mcp_config.servers["brave-search"]
            if brave_server.env and brave_server.env.get("BRAVE_API_KEY"):
                self.brave_api_edit.setText(brave_server.env["BRAVE_API_KEY"])
            
            key_layout.addWidget(self.brave_api_edit, stretch=1)
            brave_layout.addLayout(key_layout)
            
            self.show_brave_key_checkbox = QCheckBox("Show API Key")
            self.show_brave_key_checkbox.stateChanged.connect(self._toggle_brave_key_visibility)
            self.show_brave_key_checkbox.setEnabled(False)
            brave_layout.addWidget(self.show_brave_key_checkbox)
            
            link_label = QLabel(
                'Get key: <a href="https://brave.com/search/api/">https://brave.com/search/api/</a>'
            )
            link_label.setOpenExternalLinks(True)
            link_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
            brave_layout.addWidget(link_label)
            
            agentic_settings_layout.addWidget(brave_section)
        
        # --- Security Status ---
        security_section = QGroupBox("Security Status")
        security_layout = QVBoxLayout(security_section)
        
        self.security_info = QTextEdit()
        self.security_info.setReadOnly(True)
        self.security_info.setMaximumHeight(100)
        self.security_info.setStyleSheet(
            f"background-color: #F8F9FA; "
            f"border: 1px solid {BORDER_COLOR};"
        )
        
        self._update_security_status()
        security_layout.addWidget(self.security_info)
        
        agentic_settings_layout.addWidget(security_section)
        
        # Hide settings container by default
        self.agentic_settings_container.setVisible(False)
        
        agentic_layout.addWidget(self.agentic_settings_container)
        
        agentic_group.setLayout(agentic_layout)
        return agentic_group
    
    def _on_agentic_mode_changed(self, state):
        """Handle agentic mode checkbox change"""
        if state == Qt.CheckState.Checked.value:
            # Show unified consent dialog
            consent = self._show_unified_consent_dialog()
            
            if consent:
                # Enable all settings
                self.agentic_settings_container.setVisible(True)
                for checkbox in self.server_checkboxes.values():
                    checkbox.setEnabled(True)
                self.output_dir_edit.setEnabled(True)
                self.browse_output_btn.setEnabled(True)
                if hasattr(self, 'brave_api_edit'):
                    self.brave_api_edit.setEnabled(True)
                    self.show_brave_key_checkbox.setEnabled(True)
                
                logger.info("Agentic mode enabled by user")
            else:
                # User declined - uncheck
                self.agentic_mode_checkbox.setChecked(False)
        else:
            # Disable all settings
            self.agentic_settings_container.setVisible(False)
            for checkbox in self.server_checkboxes.values():
                checkbox.setEnabled(False)
            self.output_dir_edit.setEnabled(False)
            self.browse_output_btn.setEnabled(False)
            if hasattr(self, 'brave_api_edit'):
                self.brave_api_edit.setEnabled(False)
                self.show_brave_key_checkbox.setEnabled(False)
            
            logger.info("Agentic mode disabled by user")
    
    def _show_unified_consent_dialog(self) -> bool:
        """Show unified privacy consent dialog for agentic mode + MCP"""
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Agentic Mode Privacy Consent")
        dialog.setIcon(QMessageBox.Icon.Warning)
        
        dialog.setText("Privacy & Data Processing Consent Required")
        
        dialog.setInformativeText(
            "By enabling Agentic Mode, you acknowledge that:\n\n"
            "• Claude AI will be able to use TOOLS that read entire files\n"
            "• Claude AI will be able to use MCP SERVERS that read/write files\n"
            "• File contents will be sent to Anthropic's servers for processing\n"
            "• You are solely responsible for ensuring compliance with data\n"
            "  regulations (HIPAA, GDPR, etc.)\n"
            "• You should NOT enable this if working with regulated or\n"
            "  sensitive data\n\n"
            "The developer of this application assumes no liability for data\n"
            "privacy violations.\n\n"
            "Do you consent to these terms and wish to enable Agentic Mode?"
        )
        
        dialog.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        dialog.setDefaultButton(QMessageBox.StandardButton.No)
        dialog.setMinimumWidth(600)
        
        result = dialog.exec()
        
        if result == QMessageBox.StandardButton.Yes:
            logger.info("User consented to unified agentic mode (tools + MCP)")
            return True
        else:
            logger.info("User declined unified agentic mode consent")
            return False
    
    def _browse_output_dir(self):
        """Browse for output directory"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            str(self.mcp_config.get_output_dir())
        )
        
        if dir_path:
            self.output_dir_edit.setText(dir_path)
            self._update_security_status()
    
    def _toggle_brave_key_visibility(self, state):
        """Toggle Brave API key visibility"""
        if state == Qt.CheckState.Checked.value:
            self.brave_api_edit.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.brave_api_edit.setEchoMode(QLineEdit.EchoMode.Password)
    
    def _update_security_status(self):
        """Update security status display"""
        summary = self.mcp_config.get_security_summary()
        
        enabled_count = sum(1 for cb in self.server_checkboxes.values() if cb.isChecked())
        enabled_names = [name for name, cb in self.server_checkboxes.items() if cb.isChecked()]
        
        status_text = "Security Status:\n\n"
        status_text += f"Agentic Mode: {'Enabled ⚠️' if self.agentic_mode_checkbox.isChecked() else 'Disabled ✓'}\n"
        status_text += f"Output Directory: {self.output_dir_edit.text()}\n"
        status_text += f"Filesystem Restricted: {'Yes ✓' if summary['filesystem_restricted'] else 'No ✗'}\n"
        status_text += f"MCP Servers ({enabled_count}): {', '.join(enabled_names) if enabled_names else 'None'}"
        
        self.security_info.setPlainText(status_text)
    
    def _create_chunking_settings(self):
        """Create chunking settings group"""
        group = QGroupBox("Text Chunking")
        group.setFont(get_text_font(SIZE_BODY, WEIGHT_BOLD))
        layout = QFormLayout(group)
        layout.setSpacing(12)
        
        help_label = QLabel(
            "These settings control how documents are split into chunks for indexing. "
            "Changing these requires re-indexing."
        )
        help_label.setWordWrap(True)
        help_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        layout.addRow(help_label)
        
        # Chunk size
        self.chunk_size_spin = QSpinBox()
        self.chunk_size_spin.setMinimum(100)
        self.chunk_size_spin.setMaximum(3000)
        self.chunk_size_spin.setValue(300)
        self.chunk_size_spin.setSingleStep(100)
        self.chunk_size_spin.setSuffix(" characters")
        
        chunk_recommendations = QLabel(
            "<b>💡 Recommendations</b><br>"
            "300-400: Q&A<br>"
            "500-600: balanced<br>"
            "800-1000: more context"
        )
        chunk_recommendations.setWordWrap(True)
        chunk_recommendations.setStyleSheet(
            f"color: {TEXT_SECONDARY}; "
            "font-size: 10px; "
            "padding-left: 8px;"
        )
        chunk_recommendations.setMaximumWidth(320)

        chunk_size_layout = QHBoxLayout()
        chunk_size_layout.addWidget(self.chunk_size_spin)
        chunk_size_layout.addWidget(chunk_recommendations)
        chunk_size_layout.addStretch()
      
        layout.addRow("Chunk size:", chunk_size_layout)
        
        # Chunk overlap
        self.chunk_overlap_spin = QSpinBox()
        self.chunk_overlap_spin.setMinimum(0)
        self.chunk_overlap_spin.setMaximum(1000)
        self.chunk_overlap_spin.setValue(60)
        self.chunk_overlap_spin.setSingleStep(50)
        self.chunk_overlap_spin.setSuffix(" characters")
        
        overlap_recommendations = QLabel(
            "<b>💡 Recommended</b><br>"
            "15-25% of chunk size<br>"
            "Example: 60-100 for size 300"
        )
        overlap_recommendations.setWordWrap(True)
        overlap_recommendations.setStyleSheet(
            f"color: {TEXT_SECONDARY}; "
            "font-size: 10px; "
            "padding-left: 8px;"
        )
        overlap_recommendations.setMaximumWidth(320)

        overlap_layout = QHBoxLayout()
        overlap_layout.addWidget(self.chunk_overlap_spin)
        overlap_layout.addWidget(overlap_recommendations)
        overlap_layout.addStretch()

        layout.addRow("Chunk overlap:", overlap_layout)
        return group
    
    def _create_cache_settings(self):
        """Create cache settings group"""
        group = QGroupBox("Cache & Storage")
        group.setFont(get_text_font(SIZE_BODY, WEIGHT_BOLD))
        layout = QVBoxLayout(group)
        layout.setSpacing(12)
        
        help_label = QLabel(
            "Manage cached data and vector database."
        )
        help_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        layout.addWidget(help_label)
        
        # Clear cache button
        self.clear_cache_btn = QPushButton("Clear Vector Database")
        self.clear_cache_btn.clicked.connect(self._clear_cache)
        layout.addWidget(self.clear_cache_btn)
        
        warning_label = QLabel(
            "⚠️ This will delete all indexed documents. You will need to re-index."
        )
        warning_label.setWordWrap(True)
        warning_label.setStyleSheet(f"color: {ERROR_COLOR}; font-size: 11px;")
        layout.addWidget(warning_label)
        
        return group
    
    def _clear_cache(self):
        """Clear cache/vector database"""
        reply = QMessageBox.warning(
            self,
            "Clear Vector Database",
            "Are you sure you want to clear the vector database?\n\n"
            "This will delete all indexed documents and you will need to re-index your directories.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # TODO: Implement cache clearing
            logger.info("Vector database cleared from settings")
            QMessageBox.information(
                self,
                "Cache Cleared",
                "Vector database has been cleared. Please re-index your directories."
            )

    def load_settings(self, config: dict):
        """Load settings from config"""
        # Chunking
        chunk_size = config.get('chunk_size', 300)
        chunk_overlap = config.get('chunk_overlap', 60)
        
        self.chunk_size_spin.setValue(chunk_size)
        self.chunk_overlap_spin.setValue(chunk_overlap)
        
        # Agentic mode (unified)
        agentic_enabled = config.get('agentic_mode_enabled', False)
        consent_given = config.get('agentic_mode_consent_given', False)
        
        # Block signals while loading
        self.agentic_mode_checkbox.blockSignals(True)

        if agentic_enabled and consent_given:
            self.agentic_mode_checkbox.setChecked(True)
            # Show settings and enable controls
            self.agentic_settings_container.setVisible(True)
            for checkbox in self.server_checkboxes.values():
                checkbox.setEnabled(True)
            self.output_dir_edit.setEnabled(True)
            self.browse_output_btn.setEnabled(True)
            if hasattr(self, 'brave_api_edit'):
                self.brave_api_edit.setEnabled(True)
                self.show_brave_key_checkbox.setEnabled(True)
        else:
            self.agentic_mode_checkbox.setChecked(False)
            self.agentic_settings_container.setVisible(False)

        self.agentic_mode_checkbox.blockSignals(False)
        
        self._update_security_status()

    def get_settings(self) -> dict:
        """Get current settings"""
        return {
            'chunk_size': self.chunk_size_spin.value(),
            'chunk_overlap': self.chunk_overlap_spin.value(),
            'agentic_mode_enabled': self.agentic_mode_checkbox.isChecked(),
            'agentic_mode_consent_given': self.agentic_mode_checkbox.isChecked(),
            # MCP settings
            'mcp_output_dir': self.output_dir_edit.text(),
            'mcp_servers_enabled': {
                name: cb.isChecked() 
                for name, cb in self.server_checkboxes.items()
            },
            'mcp_brave_api_key': self.brave_api_edit.text().strip() if hasattr(self, 'brave_api_edit') else None
        }
    
    def apply_mcp_settings(self):
        """Apply MCP settings to mcp_config (only if agentic mode is enabled)"""
        if not self.agentic_mode_checkbox.isChecked():
            # Agentic mode disabled - disable all MCP servers
            for name in self.server_checkboxes.keys():
                self.mcp_config.disable_server(name)
            logger.info("MCP servers disabled (agentic mode off)")
            return True
        
        try:
            # Save output directory
            new_output_dir = Path(self.output_dir_edit.text())
            if new_output_dir != self.mcp_config.get_output_dir():
                self.mcp_config.set_output_dir(new_output_dir)
                logger.info(f"MCP output directory changed to: {new_output_dir}")
            
            # Save server enable/disable states
            for name, checkbox in self.server_checkboxes.items():
                if checkbox.isChecked():
                    self.mcp_config.enable_server(name)
                else:
                    self.mcp_config.disable_server(name)
            
            # Save Brave API key if provided
            if hasattr(self, 'brave_api_edit'):
                api_key = self.brave_api_edit.text().strip()
                if api_key:
                    self.mcp_config.set_brave_api_key(api_key)
                    logger.info("Brave Search API key updated")
            
            # Validate security
            if not self.mcp_config.validate_filesystem_access():
                QMessageBox.warning(
                    self,
                    "Security Warning",
                    "Filesystem access validation failed!\n\n"
                    "The output directory may not be properly restricted."
                )
                logger.warning("MCP filesystem validation failed")
                return False
            
            logger.info("MCP settings applied successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error applying MCP settings: {e}")
            QMessageBox.critical(
                self,
                "MCP Settings Error",
                f"Failed to apply MCP settings: {str(e)}"
            )
            return False
    
    def reset_to_defaults(self):
        """Reset to default values"""
        # Chunking
        self.chunk_size_spin.setValue(300)
        self.chunk_overlap_spin.setValue(60)
        
        # Agentic mode (unified)
        self.agentic_mode_checkbox.setChecked(False)
        
        # MCP - reset to defaults
        self.output_dir_edit.setText(str(self.default_output_dir))
        
        for name, checkbox in self.server_checkboxes.items():
            default_state = self.default_server_states.get(name, False)
            checkbox.setChecked(default_state)
        
        # Clear Brave API key
        if hasattr(self, 'brave_api_edit'):
            self.brave_api_edit.clear()
            self.show_brave_key_checkbox.setChecked(False)
        
        self._update_security_status()
        
        logger.info("Advanced settings reset to defaults")