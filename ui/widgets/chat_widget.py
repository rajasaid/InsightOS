"""
ui/widgets/chat_widget.py
Chat interface widget with message history and input field
Updated to integrate with agent layer and RAG retrieval
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QScrollArea, QLabel, QFrame,
    QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QThread
from PyQt6.QtGui import QFont, QTextCursor

from ui.widgets.message_widgets import UserMessageWidget, AssistantMessageWidget
from utils.logger import get_logger

logger = get_logger(__name__)


class ChatWorker(QThread):
    """Worker thread for async chat processing"""
    
    # Signals
    response_ready = pyqtSignal(str, list)  # (response_text, citations)
    error_occurred = pyqtSignal(str)  # error_message
    
    def __init__(self, agent_client, rag_retriever, message, conversation_history):
        super().__init__()
        self.agent_client = agent_client
        self.rag_retriever = rag_retriever
        self.message = message
        self.conversation_history = conversation_history
    
    def run(self):
        """Process message in background thread"""
        try:
            # Get RAG context
            context_package = self.rag_retriever.prepare_context_for_agent(
                query=self.message,
                conversation_history=self.conversation_history
            )
            
            rag_context = context_package['rag_context']
            has_context = context_package['has_context']
            
            logger.info(
                f"Retrieved RAG context: {context_package['num_chunks']} chunks "
                f"from {len(context_package['source_documents'])} documents"
            )
            
            # Get response from agent
            response = self.agent_client.chat(
                message=self.message,
                conversation_history=self.conversation_history,
                rag_context=rag_context if has_context else None
            )
            
            # Format citations from RAG results
            citations = []
            if has_context:
                for source in context_package['source_documents']:
                    citations.append({
                        'filename': source,
                        'relevance': 'High'  # Could use actual scores
                    })
            
            # Emit response
            self.response_ready.emit(response['content'], citations)
            
        except Exception as e:
            logger.error(f"Error in chat worker: {e}", exc_info=True)
            self.error_occurred.emit(str(e))


class ChatWidget(QWidget):
    """Chat interface with message history and input field"""
    
    # Signals
    message_submitted = pyqtSignal(str)  # Emitted when user submits a message
    
    def __init__(self, agent_client=None, rag_retriever=None, parent=None):
        """
        Initialize chat widget
        
        Args:
            agent_client: ClaudeClient instance from agent layer
            rag_retriever: RAGRetriever instance from core layer
            parent: Parent widget
        """
        super().__init__(parent)
        
        self._is_loading = False
        self._message_widgets = []  # Keep track of message widgets
        self._conversation_history = []  # Store conversation for context
        
        # Agent and RAG integration
        self.agent_client = agent_client
        self.rag_retriever = rag_retriever
        self.worker = None
        
        self._setup_ui()
        self._apply_styles()
        
        logger.info("Chat widget initialized with agent and RAG support")
    
    def set_agent_client(self, agent_client):
        """Set or update the agent client"""
        self.agent_client = agent_client
        logger.info("Agent client set for chat widget")
    
    def set_rag_retriever(self, rag_retriever):
        """Set or update the RAG retriever"""
        self.rag_retriever = rag_retriever
        logger.info("RAG retriever set for chat widget")
    
    def _setup_ui(self):
        """Setup chat UI components"""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # === Message History Area ===
        self._setup_message_area(layout)
        
        # === Input Area ===
        self._setup_input_area(layout)
    
    def _setup_message_area(self, layout):
        """Setup scrollable message history area"""
        # Scroll area for messages
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Container widget for messages
        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setContentsMargins(16, 16, 16, 16)
        self.messages_layout.setSpacing(16)
        self.messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Empty state label (shown when no messages)
        self.empty_state_label = QLabel(
            "👋 Welcome to InsightOS!\n\n"
            "Ask me anything about your documents.\n"
            "I'll search through your files and provide answers with citations."
        )
        self.empty_state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_state_label.setFont(QFont("SF Pro Text", 14))
        from ui.styles.colors import TEXT_SECONDARY
        self.empty_state_label.setStyleSheet(f"color: {TEXT_SECONDARY}; padding: 40px;")
        self.empty_state_label.setWordWrap(True)
        self.messages_layout.addWidget(self.empty_state_label)
        
        # Add stretch to push messages to top
        self.messages_layout.addStretch()
        
        self.scroll_area.setWidget(self.messages_container)
        layout.addWidget(self.scroll_area, stretch=1)
        
        # Loading indicator (hidden by default)
        self.loading_widget = self._create_loading_widget()
        self.loading_widget.setVisible(False)
        self.messages_layout.insertWidget(
            self.messages_layout.count() - 1,  # Before stretch
            self.loading_widget
        )
    
    def _setup_input_area(self, layout):
        """Setup message input area at bottom"""
        # Input container with border
        input_container = QFrame()
        from ui.styles.colors import BORDER_COLOR
        input_container.setStyleSheet(f"border-top: 1px solid {BORDER_COLOR};")
        
        input_layout = QVBoxLayout(input_container)
        input_layout.setContentsMargins(16, 12, 16, 12)
        input_layout.setSpacing(8)
        
        # Input field and button layout
        input_row = QHBoxLayout()
        input_row.setSpacing(8)
        
        # Multi-line text input
        self.input_field = QTextEdit()
        self.input_field.setPlaceholderText("Ask about your documents...")
        self.input_field.setFont(QFont("SF Pro Text", 13))
        self.input_field.setMaximumHeight(120)  # Max 5 lines
        self.input_field.setMinimumHeight(44)
        self.input_field.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.input_field.setAcceptRichText(False)
        
        # Auto-resize as user types
        self.input_field.textChanged.connect(self._adjust_input_height)
        
        input_row.addWidget(self.input_field, stretch=1)
        
        # Send button
        self.send_btn = QPushButton("Send")
        self.send_btn.setMinimumWidth(80)
        self.send_btn.setMinimumHeight(44)
        self.send_btn.setFont(QFont("SF Pro Text", 13, QFont.Weight.Bold))
        self.send_btn.clicked.connect(self._on_send_clicked)
        self.send_btn.setEnabled(False)  # Disabled when input is empty
        
        input_row.addWidget(self.send_btn)
        
        input_layout.addLayout(input_row)
        
        # Helper text
        helper_label = QLabel("Press Cmd+Enter to send")
        helper_label.setFont(QFont("SF Pro Text", 10))
        from ui.styles.colors import TEXT_SECONDARY
        helper_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        input_layout.addWidget(helper_label)
        
        layout.addWidget(input_container)
        
        # Connect text change to enable/disable send button
        self.input_field.textChanged.connect(self._on_input_changed)
        
        # Install event filter for Cmd+Enter shortcut
        self.input_field.installEventFilter(self)
    
    def _create_loading_widget(self):
        """Create loading indicator widget"""
        loading_widget = QWidget()
        loading_layout = QHBoxLayout(loading_widget)
        loading_layout.setContentsMargins(16, 8, 16, 8)
        
        # Typing animation with dots
        self.loading_label = QLabel("Thinking")
        self.loading_label.setFont(QFont("SF Pro Text", 13))
        from ui.styles.colors import TEXT_SECONDARY
        self.loading_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        loading_layout.addWidget(self.loading_label)
        
        loading_layout.addStretch()
        
        # Animate dots
        self.loading_timer = QTimer()
        self.loading_timer.timeout.connect(self._animate_loading)
        self.loading_dots = 0
        
        return loading_widget
    
    def _animate_loading(self):
        """Animate loading dots"""
        self.loading_dots = (self.loading_dots + 1) % 4
        dots = "." * self.loading_dots
        self.loading_label.setText(f"Thinking{dots}")
    
    def _adjust_input_height(self):
        """Auto-adjust input field height based on content"""
        doc_height = self.input_field.document().size().height()
        margins = self.input_field.contentsMargins()
        total_height = doc_height + margins.top() + margins.bottom() + 10
        
        # Clamp between min and max
        new_height = max(44, min(120, int(total_height)))
        self.input_field.setFixedHeight(new_height)
    
    def _apply_styles(self):
        """Apply macOS-native styling"""
        from ui.styles.colors import (
            BACKGROUND, TEXT_PRIMARY, TEXT_SECONDARY,
            BORDER_COLOR, ACCENT_COLOR, BUTTON_BACKGROUND
        )
        
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {BACKGROUND};
            }}
            
            QScrollArea {{
                border: none;
                background-color: {BACKGROUND};
            }}
            
            QTextEdit {{
                background-color: white;
                border: 1px solid {BORDER_COLOR};
                border-radius: 8px;
                padding: 8px 12px;
                color: {TEXT_PRIMARY};
                font-size: 13px;
            }}
            
            QTextEdit:focus {{
                border: 2px solid {ACCENT_COLOR};
                padding: 7px 11px;
            }}
            
            QPushButton {{
                background-color: {ACCENT_COLOR};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
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
            
            QScrollBar:vertical {{
                background-color: transparent;
                width: 10px;
                margin: 0;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: #C0C0C0;
                border-radius: 5px;
                min-height: 20px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: #A0A0A0;
            }}
            
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)
    
    # Event handlers
    
    def eventFilter(self, obj, event):
        """Handle keyboard events for shortcuts"""
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import QKeyEvent
        
        if obj == self.input_field and event.type() == QEvent.Type.KeyPress:
            key_event = event
            # Cmd+Enter to send (Cmd is Qt.Key.Key_Meta on macOS)
            if (key_event.key() == Qt.Key.Key_Return or key_event.key() == Qt.Key.Key_Enter) and \
               (key_event.modifiers() & Qt.KeyboardModifier.MetaModifier):
                self._on_send_clicked()
                return True
        
        return super().eventFilter(obj, event)
    
    def _on_input_changed(self):
        """Handle input text change"""
        text = self.input_field.toPlainText().strip()
        self.send_btn.setEnabled(len(text) > 0 and not self._is_loading)
    
    def _on_send_clicked(self):
        """Handle send button click"""
        text = self.input_field.toPlainText().strip()
        
        if not text or self._is_loading:
            return
        
        # Check if agent and RAG are configured
        if not self.agent_client:
            self.add_error_message(
                "Agent not configured. Please check your API key in Settings."
            )
            return
        
        if not self.rag_retriever:
            self.add_error_message(
                "RAG retriever not configured. Please restart the application."
            )
            return
        
        logger.info(f"User message: {text[:100]}...")
        
        # Hide empty state if visible
        if self.empty_state_label.isVisible():
            self.empty_state_label.setVisible(False)
        
        # Add user message to chat
        self.add_user_message(text)
        
        # Add to conversation history
        self._conversation_history.append({
            "role": "user",
            "content": text
        })
        
        # Clear input
        self.input_field.clear()
        self.input_field.setFixedHeight(44)  # Reset height
        
        # Disable input during processing
        self.input_field.setEnabled(False)
        self.send_btn.setEnabled(False)
        
        # Show loading
        self.set_loading(True)
        
        # Process in background thread
        self._process_message_async(text)
        
        # Emit signal
        self.message_submitted.emit(text)
    
    def _process_message_async(self, message: str):
        """Process message asynchronously with agent and RAG"""
        # Create worker thread
        self.worker = ChatWorker(
            agent_client=self.agent_client,
            rag_retriever=self.rag_retriever,
            message=message,
            conversation_history=self._conversation_history.copy()
        )
        
        # Connect signals
        self.worker.response_ready.connect(self._on_response_ready)
        self.worker.error_occurred.connect(self._on_error)
        self.worker.finished.connect(self._on_worker_finished)
        
        # Start processing
        self.worker.start()
    
    def _on_response_ready(self, response_text: str, citations: list):
        """Handle response from worker thread"""
        logger.info(f"Response received: {len(response_text)} chars, {len(citations)} citations")
        
        # Add assistant message
        self.add_assistant_message(response_text, citations)
        
        # Add to conversation history
        self._conversation_history.append({
            "role": "assistant",
            "content": response_text
        })
        
        # Hide loading
        self.set_loading(False)
    
    def _on_error(self, error_message: str):
        """Handle error from worker thread"""
        logger.error(f"Chat error: {error_message}")
        
        # Add error message
        self.add_error_message(error_message)
        
        # Hide loading
        self.set_loading(False)
    
    def _on_worker_finished(self):
        """Clean up worker thread"""
        if self.worker:
            self.worker.deleteLater()
            self.worker = None
    
    # Public methods
    
    def add_user_message(self, message: str):
        """Add user message to chat"""
        user_widget = UserMessageWidget(message)
        self.messages_layout.insertWidget(
            self.messages_layout.count() - 1,  # Before stretch
            user_widget
        )
        self._message_widgets.append(user_widget)
        
        # Scroll to bottom
        QTimer.singleShot(50, self._scroll_to_bottom)
    
    def add_assistant_message(self, message: str, citations: list = None):
        """Add assistant message to chat with optional citations"""
        assistant_widget = AssistantMessageWidget(message, citations)
        self.messages_layout.insertWidget(
            self.messages_layout.count() - 1,  # Before stretch
            assistant_widget
        )
        self._message_widgets.append(assistant_widget)
        
        # Re-enable input
        self.input_field.setEnabled(True)
        self.send_btn.setEnabled(False)  # Will be enabled when user types
        
        # Focus input
        self.input_field.setFocus()
        
        # Scroll to bottom
        QTimer.singleShot(50, self._scroll_to_bottom)
    
    def add_error_message(self, error_message: str):
        """Add error message to chat"""
        # Create error widget (similar to assistant message but styled differently)
        error_widget = QLabel(f"❌ Error: {error_message}")
        error_widget.setWordWrap(True)
        error_widget.setFont(QFont("SF Pro Text", 13))
        error_widget.setStyleSheet("""
            QLabel {
                background-color: #FFE5E5;
                color: #D32F2F;
                border: 1px solid #FFCCCC;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        error_widget.setMaximumWidth(600)
        
        self.messages_layout.insertWidget(
            self.messages_layout.count() - 1,  # Before stretch
            error_widget
        )
        self._message_widgets.append(error_widget)
        
        # Re-enable input
        self.input_field.setEnabled(True)
        self.input_field.setFocus()
        
        # Scroll to bottom
        QTimer.singleShot(50, self._scroll_to_bottom)
        
        logger.error(f"Error message displayed: {error_message}")
    
    def set_loading(self, is_loading: bool):
        """Show/hide loading indicator"""
        self._is_loading = is_loading
        
        if is_loading:
            self.loading_widget.setVisible(True)
            self.loading_timer.start(500)  # Update every 500ms
            self._scroll_to_bottom()
        else:
            self.loading_widget.setVisible(False)
            self.loading_timer.stop()
            self.loading_dots = 0
    
    def clear_conversation(self):
        """Clear all messages from chat"""
        # Remove all message widgets
        for widget in self._message_widgets:
            self.messages_layout.removeWidget(widget)
            widget.deleteLater()
        
        self._message_widgets.clear()
        self._conversation_history.clear()
        
        # Show empty state
        self.empty_state_label.setVisible(True)
        
        # Reset input
        self.input_field.clear()
        self.input_field.setEnabled(True)
        self.input_field.setFixedHeight(44)
        
        # Hide loading
        self.set_loading(False)
        
        logger.info("Conversation cleared")
    
    def _scroll_to_bottom(self):
        """Scroll message area to bottom"""
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def get_message_count(self):
        """Get number of messages in chat"""
        return len(self._message_widgets)
    
    def is_empty(self):
        """Check if chat is empty"""
        return len(self._message_widgets) == 0
    
    def get_conversation_history(self):
        """Get conversation history for context"""
        return self._conversation_history.copy()