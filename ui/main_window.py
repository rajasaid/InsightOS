"""
ui/main_window.py
Main application window with MCP, agent, and RAG integration
"""

from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QMessageBox, QSplitter
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtCore import QThread, pyqtSignal

from config import settings
from ui.widgets.sidebar_widget import SidebarWidget
from ui.widgets.chat_widget import ChatWidget
from ui.widgets.generated_files_browser import GeneratedFilesBrowser
from ui.dialogs.setup_wizard import SetupWizard
from ui.dialogs.settings_dialog import SettingsDialog
from security.config_manager import ConfigManager, get_config_manager
from indexing.indexer import Indexer
from core.rag_retriever import RAGRetriever
from agent import ClaudeClient
from mcp_servers import get_mcp_config
from utils.logger import get_logger

logger = get_logger(__name__)


class IndexingThread(QThread):
    """Background thread for indexing operations"""
    
    progress_update = pyqtSignal(int, int, str)  # current, total, message
    finished = pyqtSignal(object)  # IndexingResult
    
    def __init__(self, indexer, directory, is_reindex=False, directories=None):
        super().__init__()
        self.indexer = indexer
        self.directory = directory
        self.is_reindex = is_reindex
        self.directories = directories or []
    
    def run(self):
        """Run indexing in background thread"""
        try:
            if self.is_reindex:
                # Re-index all directories
                result = self.indexer.reindex_all(
                    self.directories,
                    progress_callback=self._progress_callback
                )
            else:
                # Index single directory
                result = self.indexer.index_directory(
                    self.directory,
                    progress_callback=self._progress_callback
                )
            
            self.finished.emit(result)
        
        except Exception as e:
            logger.error(f"Error in indexing thread: {e}")
            # Create error result
            from indexing.indexer import IndexingResult
            result = IndexingResult()
            result.errors.append(str(e))
            result.mark_complete()
            self.finished.emit(result)
    
    def _progress_callback(self, current, total, message):
        """Emit progress update signal"""
        self.progress_update.emit(current, total, message)


class MainWindow(QMainWindow):
    """Main application window with MCP and agent integration"""
    
    def __init__(self, indexer: Indexer = None):
        super().__init__()
        
        # Initialize config manager
        self.config_manager = get_config_manager()
        config = self.config_manager.get_config()
        
        # Initialize MCP configuration
        self.mcp_config = get_mcp_config()
        logger.info(f"MCP initialized: {list(self.mcp_config.get_enabled_servers().keys())}")
        
        # Initialize indexer
        self.indexer = indexer if indexer else Indexer()
        
        # Initialize RAG retriever
        top_k = config.get('top_k', 5)
        self.rag_retriever = RAGRetriever(top_k=top_k)
        logger.info(f"RAG retriever initialized (top_k={top_k})")
        
        # Initialize Claude agent (only if API key exists)
        self.claude_client = None
        if self.config_manager.has_api_key():
            try:
                self.claude_client = ClaudeClient(config_manager=self.config_manager)
                logger.info("Claude client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Claude client: {e}")
                self.claude_client = None
        else:
            logger.warning("No API key configured - Claude client not initialized")
        
        # Indexing thread reference
        self.indexing_thread = None

        # Setup UI
        self._setup_ui()
        self._setup_menu_bar()
        self._setup_status_bar()
        self._connect_signals()
        
        # Check if first launch (no API key configured)
        if not self.config_manager.is_configured():
            logger.info("First launch detected, showing setup wizard")
            self._show_setup_wizard()
        else:
            # Load existing index stats
            self._load_existing_index()
        
        logger.info("MainWindow initialized with MCP and agent support")
    
    def _setup_ui(self):
        """Setup main window UI"""
        self.setWindowTitle("InsightOS - Knowledge Assistant")
        self.setMinimumSize(1200, 700)
        self.resize(1400, 800)
        
        # Central widget with horizontal layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Sidebar (left)
        self.sidebar = SidebarWidget()
        self.sidebar.setMaximumWidth(320)
        self.sidebar.indexer = self.indexer  # Pass indexer to sidebar
        layout.addWidget(self.sidebar)
        
        # Main area splitter (chat + generated files)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Chat area (center)
        self.chat_widget = ChatWidget(
            agent_client=self.claude_client,
            rag_retriever=self.rag_retriever
        )
        splitter.addWidget(self.chat_widget)
        
        # Generated files browser (right)
        self.generated_files_browser = GeneratedFilesBrowser()
        self.generated_files_browser.setMaximumWidth(350)
        splitter.addWidget(self.generated_files_browser)
        
        # Set initial splitter sizes (70% chat, 30% files)
        splitter.setSizes([700, 300])
        
        layout.addWidget(splitter, stretch=1)
        
        logger.info("UI setup complete with generated files browser")
    
    def _setup_menu_bar(self):
        """Setup menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        new_conversation_action = QAction("New Conversation", self)
        new_conversation_action.setShortcut(QKeySequence("Ctrl+N"))
        new_conversation_action.triggered.connect(self._new_conversation)
        file_menu.addAction(new_conversation_action)
        
        file_menu.addSeparator()
        
        add_directory_action = QAction("Add Directory...", self)
        add_directory_action.setShortcut(QKeySequence("Ctrl+O"))
        add_directory_action.triggered.connect(self.sidebar.add_directory)
        file_menu.addAction(add_directory_action)
        
        reindex_action = QAction("Re-index All", self)
        reindex_action.setShortcut(QKeySequence("Ctrl+R"))
        reindex_action.triggered.connect(self.sidebar.reindex_all)
        file_menu.addAction(reindex_action)
        
        file_menu.addSeparator()
        
        # Open generated files folder
        open_generated_action = QAction("Open Generated Files Folder", self)
        open_generated_action.setShortcut(QKeySequence("Ctrl+Shift+O"))
        open_generated_action.triggered.connect(self.generated_files_browser.open_output_folder)
        file_menu.addAction(open_generated_action)
        
        file_menu.addSeparator()
        
        settings_action = QAction("Settings...", self)
        settings_action.setShortcut(QKeySequence("Ctrl+,"))
        settings_action.triggered.connect(self._show_settings)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        quit_action = QAction("Quit", self)
        quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        
        clear_conversation_action = QAction("Clear Conversation", self)
        clear_conversation_action.setShortcut(QKeySequence("Ctrl+K"))
        clear_conversation_action.triggered.connect(self._clear_conversation)
        edit_menu.addAction(clear_conversation_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        refresh_generated_action = QAction("Refresh Generated Files", self)
        refresh_generated_action.setShortcut(QKeySequence("Ctrl+Shift+R"))
        refresh_generated_action.triggered.connect(self.generated_files_browser.refresh_files)
        view_menu.addAction(refresh_generated_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        mcp_status_action = QAction("MCP Server Status", self)
        mcp_status_action.triggered.connect(self._show_mcp_status)
        help_menu.addAction(mcp_status_action)
        
        help_menu.addSeparator()
        
        about_action = QAction("About InsightOS", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
        
        documentation_action = QAction("Documentation", self)
        documentation_action.setShortcut(QKeySequence("Ctrl+?"))
        documentation_action.triggered.connect(self._show_documentation)
        help_menu.addAction(documentation_action)
    
    def _setup_status_bar(self):
        """Setup status bar"""
        statusbar = self.statusBar()
        
        # Show MCP and API status
        mcp_status = "🟢 MCP" if self.mcp_config.validate_filesystem_access() else "🔴 MCP"
        api_status = "🟢 API Key" if self.config_manager.has_api_key() else "🔴 API Key"
        agent_status = "🟢 Agent" if self.claude_client else "🔴 Agent"
        
        statusbar.showMessage(
            f"{api_status}  |  {agent_status}  |  {mcp_status}  |  📁 Ready"
        )
    
    def _connect_signals(self):
        """Connect signals from widgets"""
        # Sidebar signals
        self.sidebar.directory_added.connect(self._on_directory_added)
        self.sidebar.directory_removed.connect(self._on_directory_removed)
        self.sidebar.reindex_requested.connect(self._on_reindex_requested)
        self.sidebar.settings_requested.connect(self._show_settings)
        
        # Chat signals
        self.chat_widget.message_submitted.connect(self._on_message_submitted)
        
        # Generated files browser signals
        self.generated_files_browser.file_opened.connect(self._on_generated_file_opened)
        self.generated_files_browser.file_selected.connect(self._on_generated_file_selected)
    
    def closeEvent(self, event):
        """Handle window close - wait for indexing thread if running"""
        if self.indexing_thread and self.indexing_thread.isRunning():
            reply = QMessageBox.question(
                self,
                "Indexing in Progress",
                "Indexing is still running. Are you sure you want to quit?\n\n"
                "This may leave the index in an incomplete state.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Wait for thread to finish (with timeout)
                self.indexing_thread.wait(5000)  # Wait max 5 seconds
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    # ========================================================================
    # Setup Wizard
    # ========================================================================
    
    def _show_setup_wizard(self):
        """Show setup wizard on first launch"""
        logger.info("Showing setup wizard")
        
        # Create wizard with indexer
        wizard = SetupWizard(indexer=self.indexer, parent=self)
        wizard.setup_completed.connect(self._on_setup_completed)
        
        result = wizard.exec()
        
        if result == SetupWizard.DialogCode.Accepted:
            logger.info("Setup wizard completed")
            # Reinitialize Claude client with new API key
            self._reinitialize_agent()
        else:
            logger.warning("Setup wizard cancelled")
            # Ask if user wants to quit
            reply = QMessageBox.question(
                self,
                "Setup Cancelled",
                "Setup was not completed. Would you like to exit the application?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.close()
    
    def _on_setup_completed(self):
        """Handle setup wizard completion"""
        logger.info("Setup completed, loading configuration")
        
        # Get config from wizard
        wizard = self.sender()
        config_data = wizard.get_config_data()
        
        # Save API key
        if config_data.get('api_key'):
            self.config_manager.save_api_key(config_data['api_key'])
            logger.info("API key saved from setup wizard")
        
        # Save directories (but don't add to sidebar yet - avoid re-indexing)
        directories = config_data.get('directories', [])
        for directory in directories:
            self.config_manager.add_monitored_directory(directory)
            # Just add to list WITHOUT triggering the signal
            self.sidebar.add_directory_to_list(directory)
        
        # Update status bar
        self._update_status_bar()
        
        # Update sidebar stats from the indexing that already happened in wizard
        stats = self.indexer.get_stats()
        self.sidebar.update_file_count(stats['total_chunks'])
        
        from datetime import datetime
        self.sidebar.update_last_indexed(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    # ========================================================================
    # Agent Management
    # ========================================================================
    
    def _reinitialize_agent(self):
        """Reinitialize Claude client after API key change"""
        try:
            self.claude_client = ClaudeClient()
            self.chat_widget.set_agent_client(self.claude_client)
            logger.info("Claude client reinitialized successfully")
            self._update_status_bar()
        except Exception as e:
            logger.error(f"Failed to reinitialize Claude client: {e}")
            QMessageBox.critical(
                self,
                "Agent Initialization Error",
                f"Failed to initialize Claude client:\n{str(e)}\n\n"
                "Please check your API key in Settings."
            )
    
    def _update_status_bar(self):
        """Update status bar with current state"""
        mcp_status = "🟢 MCP" if self.mcp_config.validate_filesystem_access() else "🔴 MCP"
        api_status = "🟢 API Key" if self.config_manager.has_api_key() else "🔴 API Key"
        agent_status = "🟢 Agent" if self.claude_client else "🔴 Agent"
        
        stats = self.indexer.get_stats()
        chunks_status = f"📁 {stats['total_chunks']} chunks indexed"
        
        self.statusBar().showMessage(
            f"{api_status}  |  {agent_status}  |  {mcp_status}  |  {chunks_status}"
        )
    
    # ========================================================================
    # Load Existing Index
    # ========================================================================
    
    def _load_existing_index(self):
        """Load stats from existing ChromaDB index"""
        try:
            stats = self.indexer.get_stats()
            
            if stats['total_chunks'] > 0:
                self.sidebar.update_file_count(stats['total_chunks'])
                logger.info(
                    f"Loaded existing index: {stats['indexed_files']} files, "
                    f"{stats['total_chunks']} chunks"
                )
            
            # Load monitored directories from config
            directories = self.config_manager.get_monitored_directories()
            for directory in directories:
                self.sidebar.add_directory_to_list(directory)
            
            self._update_status_bar()
        
        except Exception as e:
            logger.error(f"Error loading existing index: {e}")
    
    # ========================================================================
    # Indexing Event Handlers
    # ========================================================================
    
    def _on_directory_added(self, directory: str):
        """Handle directory added - start indexing in background thread"""
        logger.info(f"Directory added, starting indexing: {directory}")
        
        # Save to config
        self.config_manager.add_monitored_directory(directory)
        
        # Disable UI during indexing
        self.sidebar.add_btn.setEnabled(False)
        self.sidebar.reindex_btn.setEnabled(False)
        
        # Create and start indexing thread
        self.indexing_thread = IndexingThread(
            indexer=self.indexer,
            directory=directory,
            is_reindex=False
        )
        
        # Connect signals
        self.indexing_thread.progress_update.connect(self._on_indexing_progress)
        self.indexing_thread.finished.connect(self._on_indexing_finished)
        
        # Start thread
        self.indexing_thread.start()
        
        logger.info("Indexing thread started")
    
    def _on_directory_removed(self, directory: str):
        """Handle directory removed"""
        logger.info(f"Directory removed: {directory}")
        
        # Remove from config
        self.config_manager.remove_monitored_directory(directory)
        
        # Update file count
        self._update_status_bar()
    
    def _on_reindex_requested(self):
        """Handle re-index all request in background thread"""
        directories = self.sidebar.get_directories()
        
        if not directories:
            QMessageBox.information(
                self,
                "No Directories",
                "Please add directories to monitor before re-indexing."
            )
            return
        
        logger.info(f"Re-indexing {len(directories)} directories")
        
        # Disable UI during indexing
        self.sidebar.add_btn.setEnabled(False)
        self.sidebar.reindex_btn.setEnabled(False)
        
        # Create and start indexing thread
        self.indexing_thread = IndexingThread(
            indexer=self.indexer,
            directory=None,
            is_reindex=True,
            directories=directories
        )
        
        # Connect signals
        self.indexing_thread.progress_update.connect(self._on_indexing_progress)
        self.indexing_thread.finished.connect(self._on_reindex_finished)
        
        # Start thread
        self.indexing_thread.start()
        
        logger.info("Re-indexing thread started")
    
    def _on_indexing_progress(self, current: int, total: int, message: str):
        """Handle progress update from indexing thread"""
        if total > 0:
            progress = int((current / total) * 100)
            self.sidebar.set_indexing(True, progress, message)
            
            # Also update status bar
            self.statusBar().showMessage(f"Indexing: {message}")
    
    def _on_indexing_finished(self, result):
        """Handle indexing completion (single directory)"""
        logger.info(f"Indexing finished: {result}")
        
        # Re-enable UI
        self.sidebar.set_indexing(False)
        self.sidebar.add_btn.setEnabled(True)
        self.sidebar.reindex_btn.setEnabled(True)
        
        # Update stats
        self._update_status_bar()
        stats = self.indexer.get_stats()
        self.sidebar.update_file_count(stats['total_chunks'])
        
        # Update last indexed time
        from datetime import datetime
        self.sidebar.update_last_indexed(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # Show result in status bar
        if result.files_failed > 0:
            self.statusBar().showMessage(
                f"⚠️ Indexed: {result.files_processed} files, {result.files_failed} failed",
                5000
            )
        else:
            self.statusBar().showMessage(
                f"✅ Indexed: {result.files_processed} files, {result.chunks_created} chunks",
                5000
            )
        
        # Show errors if any
        if result.errors:
            error_msg = f"Indexing completed with {len(result.errors)} errors:\n\n"
            error_msg += "\n".join(result.errors[:5])
            if len(result.errors) > 5:
                error_msg += f"\n\n...and {len(result.errors) - 5} more errors"
            
            QMessageBox.warning(self, "Indexing Errors", error_msg)
        
        # Clean up thread
        self.indexing_thread = None
        
        logger.info("Indexing complete, UI updated")
    
    def _on_reindex_finished(self, result):
        """Handle re-indexing completion (all directories)"""
        logger.info(f"Re-indexing finished: {result}")
        
        # Re-enable UI
        self.sidebar.set_indexing(False)
        self.sidebar.add_btn.setEnabled(True)
        self.sidebar.reindex_btn.setEnabled(True)
        
        # Update stats
        self._update_status_bar()
        stats = self.indexer.get_stats()
        self.sidebar.update_file_count(stats['total_chunks'])
        
        from datetime import datetime
        self.sidebar.update_last_indexed(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # Show result
        if result.files_failed > 0:
            self.statusBar().showMessage(
                f"⚠️ Re-indexed: {result.files_processed} files, {result.files_failed} failed",
                5000
            )
        else:
            self.statusBar().showMessage(
                f"✅ Re-indexed: {result.files_processed} files, {result.chunks_created} chunks",
                5000
            )
        
        # Show errors if any
        if result.errors:
            error_msg = f"Re-indexing completed with {len(result.errors)} errors:\n\n"
            error_msg += "\n".join(result.errors[:5])
            if len(result.errors) > 5:
                error_msg += f"\n\n...and {len(result.errors) - 5} more errors"
            
            QMessageBox.warning(self, "Re-indexing Errors", error_msg)
        
        # Clean up thread
        self.indexing_thread = None
        
        logger.info("Re-indexing complete, UI updated")
    
    # ========================================================================
    # Chat Event Handlers
    # ========================================================================
    
    def _on_message_submitted(self, query: str):
        """
        Handle user query - this is now handled by ChatWidget's worker thread
        This method is kept for additional processing if needed
        """
        logger.info(f"Message submitted: {query[:100]}...")
        # ChatWidget now handles the entire flow asynchronously
        # We just log it here for tracking
    
    # ========================================================================
    # Generated Files Event Handlers
    # ========================================================================
    
    def _on_generated_file_opened(self, filepath):
        """Handle generated file opened"""
        logger.info(f"Generated file opened: {filepath}")
    
    def _on_generated_file_selected(self, filepath):
        """Handle generated file selected"""
        logger.debug(f"Generated file selected: {filepath}")
    
    # ========================================================================
    # Menu Actions
    # ========================================================================
    
    def _new_conversation(self):
        """Start new conversation"""
        if not self.chat_widget.is_empty():
            reply = QMessageBox.question(
                self,
                "New Conversation",
                "Start a new conversation? Current conversation will be cleared.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.chat_widget.clear_conversation()
                logger.info("New conversation started")
    
    def _clear_conversation(self):
        """Clear current conversation"""
        if not self.chat_widget.is_empty():
            self.chat_widget.clear_conversation()
            logger.info("Conversation cleared")
    
    def _show_settings(self):
        """Show settings dialog"""
        logger.info("Opening settings dialog")
        
        dialog = SettingsDialog(parent=self)
        dialog.settings_changed.connect(self._on_settings_changed)
        dialog.api_key_changed.connect(self._on_api_key_changed)
        dialog.exec()
    
    def _on_settings_changed(self, settings: dict):
        """Handle settings changes"""
        logger.info("Settings changed")
        
        # Update indexer settings if chunk size/overlap changed
        if 'chunk_size' in settings:
            self.indexer.chunk_size = settings['chunk_size']
        if 'chunk_overlap' in settings:
            self.indexer.chunk_overlap = settings['chunk_overlap']
        
        # Update RAG top_k
        if 'top_k' in settings:
            self.rag_retriever.set_top_k(settings['top_k'])
            logger.info(f"RAG top_k updated to: {settings['top_k']}")
        
        # MCP settings are handled by mcp_config automatically
        # Just update status bar
        self._update_status_bar()
    
    def _on_api_key_changed(self, api_key: str):
        """Handle API key change"""
        logger.info("API key changed, reinitializing agent")
        self._reinitialize_agent()
    
    def _show_mcp_status(self):
        """Show MCP server status"""
        security_summary = self.mcp_config.get_security_summary()
        
        status_text = "MCP Server Status:\n\n"
        status_text += f"Output Directory: {security_summary['output_dir']}\n"
        status_text += f"Filesystem Restricted: {'Yes ✓' if security_summary['filesystem_restricted'] else 'No ✗'}\n"
        status_text += f"Filesystem Enabled: {'Yes' if security_summary['filesystem_enabled'] else 'No'}\n\n"
        status_text += f"Enabled Servers ({len(security_summary['enabled_servers'])}):\n"
        
        if security_summary['enabled_servers']:
            for server in security_summary['enabled_servers']:
                status_text += f"  • {server}\n"
        else:
            status_text += "  None\n"
        
        status_text += f"\nConfig File: {self.mcp_config.config_file}"
        
        QMessageBox.information(self, "MCP Server Status", status_text)
    
    def _show_about(self):
        """Show about dialog"""
        from config import APP_NAME, APP_VERSION, APP_DESCRIPTION
        
        QMessageBox.about(
            self,
            f"About {APP_NAME}",
            f"<h2>{APP_NAME}</h2>"
            f"<p>Version {APP_VERSION}</p>"
            f"<p>{APP_DESCRIPTION}</p>"
            f"<p>Built with PyQt6, Claude AI, and MCP</p>"
            f"<p>Features: RAG, Agentic Mode, File Generation</p>"
        )
    
    def _show_documentation(self):
        """Show documentation"""
        QMessageBox.information(
            self,
            "Documentation",
            "Documentation is available at:\n"
            "https://github.com/yourusername/insightos\n\n"
            "For support, please visit the GitHub issues page."
        )