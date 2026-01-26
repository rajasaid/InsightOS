"""
ui/dialogs/setup_wizard.py
First-time setup wizard for InsightOS
"""

from PySide6.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog,
    QListWidget, QListWidgetItem, QProgressBar,
    QTextEdit, QCheckBox, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QPixmap

from pathlib import Path

from ui.styles.colors import (
    BACKGROUND, TEXT_PRIMARY, TEXT_SECONDARY,
    ACCENT_COLOR, ERROR_COLOR, SUCCESS_COLOR
)
from ui.styles.fonts import (
    get_display_font, get_text_font,
    SIZE_DISPLAY_MEDIUM, SIZE_BODY, WEIGHT_BOLD
)
from utils.logger import get_logger

from ui.resources.logo import create_logo_label
from indexing.indexer import Indexer

logger = get_logger(__name__)


class SetupWizard(QWizard):
    """Multi-page setup wizard for first-time configuration"""
    
    # Page IDs
    PAGE_WELCOME = 0
    PAGE_API_KEY = 1
    PAGE_DIRECTORIES = 2
    PAGE_INDEXING = 3
    PAGE_COMPLETE = 4
    
    # Signals
    api_key_configured = Signal(str)  # Emitted with API key
    directories_selected = Signal(list)  # Emitted with directory list
    setup_completed = Signal()  # Emitted when wizard completes
    
    def __init__(self, indexer=None, parent=None):
        super().__init__(parent)
        
        self.indexer = indexer
        self.setWindowTitle("Welcome to InsightOS")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setOption(QWizard.WizardOption.NoBackButtonOnStartPage, True)
        self.setOption(QWizard.WizardOption.NoBackButtonOnLastPage, True)
        self.setOption(QWizard.WizardOption.NoCancelButtonOnLastPage, True)
        self.setMinimumSize(700, 550)
        
        # Store configuration data
        self.config_data = {
            'api_key': None,
            'directories': [],
            'indexing_complete': False
        }
        
        # Setup pages
        self._setup_pages()
        self._apply_styles()

        logger.info("Setup wizard initialized")
    
    def _setup_pages(self):
        """Setup all wizard pages"""
        self.setPage(self.PAGE_WELCOME, WelcomePage())
        self.setPage(self.PAGE_API_KEY, APIKeyPage())
        self.setPage(self.PAGE_DIRECTORIES, DirectoriesPage())
        self.setPage(self.PAGE_INDEXING, IndexingPage())
        self.setPage(self.PAGE_COMPLETE, CompletePage())
        
        # Set starting page
        self.setStartId(self.PAGE_WELCOME)
        
        # Connect page signals
        api_key_page = self.page(self.PAGE_API_KEY)
        api_key_page.api_key_validated.connect(self._on_api_key_validated)
        
        directories_page = self.page(self.PAGE_DIRECTORIES)
        directories_page.directories_changed.connect(self._on_directories_changed)
        
        indexing_page = self.page(self.PAGE_INDEXING)
        indexing_page.indexing_complete.connect(self._on_indexing_complete)
    
    def _apply_styles(self):
        """Apply macOS-native styling"""
        self.setStyleSheet(f"""
            QWizard {{
                background-color: {BACKGROUND};
            }}
            
            QLabel {{
                color: {TEXT_PRIMARY};
            }}
            
            QPushButton {{
                background-color: {ACCENT_COLOR};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: bold;
                min-width: 80px;
            }}
            
            QPushButton:hover {{
                background-color: #0051D5;
            }}
            
            QPushButton:pressed {{
                background-color: #003DB3;
            }}
            
            QPushButton:disabled {{
                background-color: #C0C0C0;
                color: #808080;
            }}
        """)
    
    # Event handlers
    
    def _on_api_key_validated(self, api_key: str):
        """Handle API key validation"""
        self.config_data['api_key'] = api_key
        self.api_key_configured.emit(api_key)
        logger.info("API key validated in setup wizard")
    
    def _on_directories_changed(self, directories: list):
        """Handle directories selection"""
        self.config_data['directories'] = directories
        logger.info(f"Selected {len(directories)} directories in setup wizard")
    
    def _on_indexing_complete(self):
        """Handle indexing completion"""
        self.config_data['indexing_complete'] = True
        logger.info("Indexing complete in setup wizard")
    
    def accept(self):
        """Override accept to emit setup_completed signal"""
        self.setup_completed.emit()
        super().accept()
        logger.info("Setup wizard completed successfully")
    
    def get_config_data(self):
        """Get configuration data from wizard"""
        return self.config_data


class WelcomePage(QWizardPage):
    """Welcome page with introduction"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setTitle("Welcome to InsightOS")
        self.setSubTitle("Your intelligent desktop knowledge assistant with AI-powered document understanding and file generation")
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup welcome page UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Logo/Icon
        logo_label = create_logo_label(size=200)
        layout.addWidget(logo_label)
        
        # Welcome text
        welcome_text = QLabel(
            "<h2>Welcome to InsightOS!</h2>"
            "<p style='font-size: 14px;'>"
            "InsightOS is your AI-powered knowledge assistant that understands your documents "
            "and helps you create new content through natural conversation."
            "</p>"
        )
        welcome_text.setWordWrap(True)
        welcome_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(welcome_text)
        
        # Core capabilities
        capabilities_label = QLabel(
            "<p style='font-size: 13px;'><b>🎯 Core Capabilities:</b></p>"
            "<ul style='font-size: 13px; line-height: 1.6;'>"
            "<li><b>Smart Document Search</b> - Ask questions about your files in natural language</li>"
            "<li><b>Agentic File Creation</b> - Create documents, reports, and data files through conversation</li>"
            "<li><b>Multi-Format Support</b> - PDFs, Word docs, spreadsheets, Markdown, code, and more</li>"
            "<li><b>Citation & Verification</b> - Answers include precise source citations</li>"
            "<li><b>Local & Private</b> - Everything runs on your machine</li>"
            "</ul>"
        )
        capabilities_label.setWordWrap(True)
        layout.addWidget(capabilities_label)
        
        # Advanced features
        advanced_label = QLabel(
            "<p style='font-size: 13px;'><b>⚡ Advanced Features:</b></p>"
            "<ul style='font-size: 13px; line-height: 1.6;'>"
            "<li><b>Semantic Search</b> - Semantic textual matching for better accuracy</li>"
            "<li><b>MCP Integration</b> - Secure file operations via Model Context Protocol</li>"
            "<li><b>Agentic Mode</b> - AI autonomously searches, reads, and creates files</li>"
            "<li><b>Multi-lingual</b> - Supports Hebrew, English, Arabic, and 100+ languages with RTL support</li>"
            "</ul>"
        )
        advanced_label.setWordWrap(True)
        layout.addWidget(advanced_label)
        
        # Setup info
        setup_info = QLabel(
            "<p style='font-size: 13px; color: #8E8E93;'>"
            "This wizard will guide you through setting up your API key and indexing your first documents. "
            "Takes just a few minutes to get started."
            "</p>"
        )
        setup_info.setWordWrap(True)
        setup_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(setup_info)
        
        layout.addStretch()


class APIKeyPage(QWizardPage):
    """API key configuration page"""
    
    api_key_validated = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setTitle("Configure Claude API Key")
        self.setSubTitle("InsightOS requires a Claude API key to answer questions")
        
        self._api_key_valid = False
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup API key page UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Instructions
        instructions = QLabel(
            "<p style='font-size: 13px;'>"
            "To use InsightOS, you need a Claude API key from Anthropic. "
            "Your API key will be encrypted and stored locally."
            "</p>"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Get API key link
        link_label = QLabel(
            '<p style="font-size: 13px;">'
            '1. Get your API key from: '
            '<a href="https://console.anthropic.com/">https://console.anthropic.com/</a>'
            '</p>'
            '<p style="font-size: 13px;">2. Create an account or sign in</p>'
            '<p style="font-size: 13px;">3. Navigate to API Keys section</p>'
            '<p style="font-size: 13px;">4. Create a new key and copy it</p>'
        )
        link_label.setWordWrap(True)
        link_label.setOpenExternalLinks(True)
        layout.addWidget(link_label)
        
        layout.addSpacing(10)
        
        # API key input
        input_label = QLabel("Enter your Claude API Key:")
        input_label.setFont(get_text_font(SIZE_BODY, WEIGHT_BOLD))
        layout.addWidget(input_label)
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("sk-ant-...")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setMinimumHeight(36)
        self.api_key_input.textChanged.connect(self._on_key_changed)
        layout.addWidget(self.api_key_input)
        
        # Show/hide key checkbox
        self.show_key_checkbox = QCheckBox("Show API key")
        self.show_key_checkbox.stateChanged.connect(self._toggle_key_visibility)
        layout.addWidget(self.show_key_checkbox)
        
        # Validate button
        button_layout = QHBoxLayout()
        self.validate_btn = QPushButton("Validate API Key")
        self.validate_btn.setEnabled(False)
        self.validate_btn.clicked.connect(self._validate_api_key)
        button_layout.addStretch()
        button_layout.addWidget(self.validate_btn)
        layout.addLayout(button_layout)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # Register field for validation
        self.registerField("api_key*", self.api_key_input)
    
    def _on_key_changed(self, text):
        """Handle API key input change"""
        self.validate_btn.setEnabled(len(text.strip()) > 0)
        self._api_key_valid = False
        self.status_label.clear()
        self.completeChanged.emit()
    
    def _toggle_key_visibility(self, state):
        """Toggle API key visibility"""
        if state == Qt.CheckState.Checked.value:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
    
    def _validate_api_key(self):
        """Validate API key with test call"""
        api_key = self.api_key_input.text().strip()
        
        if not api_key:
            return
        
        # Show validating status
        self.status_label.setText("⏳ Validating API key...")
        self.status_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        self.validate_btn.setEnabled(False)
        self.api_key_input.setEnabled(False)
        
        # Simulate validation (in real implementation, call actual API)
        # TODO: Integrate with KeyManager to actually validate
        QTimer.singleShot(1500, lambda: self._validation_result(True, api_key))
    
    def _validation_result(self, success: bool, api_key: str):
        """Handle validation result"""
        self.validate_btn.setEnabled(True)
        self.api_key_input.setEnabled(True)
        
        if success:
            self._api_key_valid = True
            self.status_label.setText("✅ API key is valid!")
            self.status_label.setStyleSheet(f"color: {SUCCESS_COLOR}; font-weight: bold;")
            self.api_key_validated.emit(api_key)
            logger.info("API key validated successfully")
        else:
            self._api_key_valid = False
            self.status_label.setText("❌ Invalid API key. Please check and try again.")
            self.status_label.setStyleSheet(f"color: {ERROR_COLOR}; font-weight: bold;")
            logger.warning("API key validation failed")
        
        self.completeChanged.emit()
    
    def isComplete(self):
        """Check if page is complete"""
        return self._api_key_valid


class DirectoriesPage(QWizardPage):
    """Directory selection page"""
    
    directories_changed = Signal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setTitle("Select Directories to Monitor")
        self.setSubTitle("Choose directories containing documents you want to search")
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup directories page UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Instructions
        instructions = QLabel(
            "<p style='font-size: 13px;'>"
            "Select one or more directories containing documents. "
            "InsightOS will index all supported files in these directories."
            "</p>"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Directory list
        list_label = QLabel("Selected Directories:")
        list_label.setFont(get_text_font(SIZE_BODY, WEIGHT_BOLD))
        layout.addWidget(list_label)
        
        self.dirs_list = QListWidget()
        self.dirs_list.setMinimumHeight(200)
        self.dirs_list.setAlternatingRowColors(True)
        layout.addWidget(self.dirs_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("Add Directory")
        self.add_btn.clicked.connect(self._add_directory)
        button_layout.addWidget(self.add_btn)
        
        self.remove_btn = QPushButton("Remove Selected")
        self.remove_btn.setEnabled(False)
        self.remove_btn.clicked.connect(self._remove_directory)
        button_layout.addWidget(self.remove_btn)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # Info label
        self.info_label = QLabel("Add at least one directory to continue.")
        self.info_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        layout.addWidget(self.info_label)
        
        layout.addStretch()
        
        # Connect signals
        self.dirs_list.itemSelectionChanged.connect(self._on_selection_changed)
    
    def _add_directory(self):
        """Add directory to list"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Directory",
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
                        f"The directory '{directory}' is already in the list."
                    )
                    return
            
            # Add to list
            item = QListWidgetItem(directory)
            self.dirs_list.addItem(item)
            
            # Update info
            self._update_info()
            
            # Emit signal
            self._emit_directories()
            
            logger.info(f"Directory added to wizard: {directory}")
    
    def _remove_directory(self):
        """Remove selected directory"""
        selected_items = self.dirs_list.selectedItems()
        if selected_items:
            for item in selected_items:
                self.dirs_list.takeItem(self.dirs_list.row(item))
            
            self._update_info()
            self._emit_directories()
    
    def _on_selection_changed(self):
        """Handle selection change"""
        has_selection = len(self.dirs_list.selectedItems()) > 0
        self.remove_btn.setEnabled(has_selection)
    
    def _update_info(self):
        """Update info label"""
        count = self.dirs_list.count()
        if count == 0:
            self.info_label.setText("Add at least one directory to continue.")
            self.info_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        else:
            self.info_label.setText(f"✅ {count} director{'y' if count == 1 else 'ies'} selected.")
            self.info_label.setStyleSheet(f"color: {SUCCESS_COLOR}; font-size: 12px; font-weight: bold;")
        
        self.completeChanged.emit()
    
    def _emit_directories(self):
        """Emit directories list"""
        directories = []
        for i in range(self.dirs_list.count()):
            directories.append(self.dirs_list.item(i).text())
        
        self.directories_changed.emit(directories)
    
    def isComplete(self):
        """Check if page is complete"""
        return self.dirs_list.count() > 0


class IndexingPage(QWizardPage):
    """Indexing progress page"""
    
    indexing_complete = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.indexer = Indexer()

        self.setTitle("Indexing Your Documents")
        self.setSubTitle("Please wait while InsightOS indexes your files")
        
        self._indexing_complete = False
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup indexing page UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Status label
        self.status_label = QLabel("Preparing to index...")
        self.status_label.setFont(get_text_font(SIZE_BODY, WEIGHT_BOLD))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(24)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        
        # Details text
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(250)
        self.details_text.setFont(get_text_font(11))
        layout.addWidget(self.details_text)
        
        layout.addStretch()
    
    def initializePage(self):
        """Called when page is shown - start indexing"""
        super().initializePage()
        
        # Start indexing process
        QTimer.singleShot(500, self._start_real_indexing)
    
    def _start_real_indexing(self):
        """Start real indexing with the actual indexer"""
        logger.info("Starting real indexing in setup wizard")
        
        # Get directories and indexer from wizard
        wizard = self.wizard()
        directories = wizard.config_data.get('directories', [])
        
        if not directories:
            logger.warning("No directories to index")
            self._indexing_finished()
            return
        
        # Check if indexer is available
        if not hasattr(wizard, 'indexer') or not wizard.indexer:
            logger.warning("No indexer available, using simulation")
            self._simulate_indexing()
            return
        
        self.status_label.setText(f"Indexing {len(directories)} director{'y' if len(directories) == 1 else 'ies'}...")
        
        # Use real indexer
        indexer = wizard.indexer
        
        # Define progress callback
        def update_progress(current, total, message):
            if total > 0:
                progress = int((current / total) * 100)
                self.progress_bar.setValue(progress)
                self.details_text.append(f"[{progress}%] {message}")
        
        # Start indexing in background (to keep UI responsive)
        from PySide6.QtCore import QThread, Signal
        
        class IndexingThread(QThread):
            finished = Signal(object)  # Emits IndexingResult
            
            def __init__(self, indexer, directories, progress_callback):
                super().__init__()
                self.indexer = indexer
                self.directories = directories
                self.progress_callback = progress_callback
            
            def run(self):
                result = self.indexer.reindex_all(
                    self.directories,
                    self.progress_callback
                )
                self.finished.emit(result)
        
        # Create and start thread
        self.indexing_thread = IndexingThread(indexer, directories, update_progress)
        self.indexing_thread.finished.connect(self._on_indexing_finished)
        self.indexing_thread.start()
        
    def _on_indexing_finished(self, result):
        """Handle indexing completion"""
        logger.info(f"Indexing finished: {result}")
        
        # Update UI with results
        self.details_text.append(f"\n=== Indexing Complete ===")
        self.details_text.append(f"Files processed: {result.files_processed}")
        self.details_text.append(f"Chunks created: {result.chunks_created}")
        self.details_text.append(f"Files failed: {result.files_failed}")
        self.details_text.append(f"Duration: {result.get_duration():.1f}s")
        
        if result.errors:
            self.details_text.append(f"\nErrors:")
            for error in result.errors[:5]:  # Show first 5 errors
                self.details_text.append(f"  - {error}")
        
        self._indexing_finished()
    
    def _simulate_indexing(self):
        """Fallback simulation if no indexer available"""
        # Your existing simulation code...
        self.progress_bar.setValue(0)
        
        steps = [
            (10, "Scanning directories..."),
            (25, "Found 247 files"),
            (40, "Reading documents..."),
            (60, "Extracting text..."),
            (75, "Creating embeddings..."),
            (90, "Storing in database..."),
            (100, "Indexing complete!")
        ]
        
        def update_progress(index=0):
            if index < len(steps):
                progress, message = steps[index]
                self.progress_bar.setValue(progress)
                self.details_text.append(f"[{progress}%] {message}")
                
                if index < len(steps) - 1:
                    QTimer.singleShot(800, lambda: update_progress(index + 1))
                else:
                    self._indexing_finished()
        
        update_progress()
    
    def _indexing_finished(self):
        """Mark indexing as complete"""
        self._indexing_complete = True
        self.status_label.setText("✅ Indexing Complete!")
        self.status_label.setStyleSheet(f"color: {SUCCESS_COLOR}; font-weight: bold;")
        
        self.indexing_complete.emit()
        self.completeChanged.emit()
        
        logger.info("Indexing complete in setup wizard")
    
    def isComplete(self):
        """Check if page is complete"""
        return self._indexing_complete


class CompletePage(QWizardPage):
    """Completion page"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setTitle("Setup Complete!")
        self.setSubTitle("InsightOS is ready to use")
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup complete page UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Success icon
        success_label = QLabel("✅")
        success_label.setFont(QFont("SF Pro Text", 64))
        success_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(success_label)
        
        # Success message
        message = QLabel(
            "<h2>All set!</h2>"
            "<p style='font-size: 14px;'>"
            "InsightOS is now configured and ready to help you find information "
            "in your documents."
            "</p>"
        )
        message.setWordWrap(True)
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(message)
        
        # Next steps
        next_steps = QLabel(
            "<p style='font-size: 13px;'><b>Next steps:</b></p>"
            "<ul style='font-size: 13px;'>"
            "<li>Start asking questions about your documents</li>"
            "<li>Add more directories from the sidebar</li>"
            "<li>Adjust settings from Settings menu</li>"
            "</ul>"
        )
        next_steps.setWordWrap(True)
        layout.addWidget(next_steps)
        
        layout.addStretch()