# InsightOS

**AI-Powered Desktop Knowledge Assistant**

Developed by **Raja Said**

---

## Overview

InsightOS is a sophisticated desktop application that transforms how you interact with your local documents. Built with Python and PySide6, it combines advanced AI capabilities with a modern, intuitive interface to provide intelligent document search, analysis, and content generation.

## Key Features

### 🔍 **Intelligent Document Search**
- **RAG (Retrieval-Augmented Generation)**: Advanced semantic search across your document collection
- **Multi-format Support**: PDF, Word, Markdown, text files, code files, and more
- **ChromaDB Integration**: High-performance vector database for fast, accurate retrieval
- **Smart Chunking**: Optimized text segmentation for better search results

### 🤖 **AI-Powered Assistant**
- **Claude Integration**: Powered by Anthropic's Claude AI for natural language understanding
- **Contextual Responses**: Answers grounded in your actual documents with citations
- **Agentic Mode**: Advanced AI capabilities for complex reasoning and task execution
- **MCP (Model Context Protocol)**: Extensible architecture for AI tool integration

### 🛠️ **Content Generation**
- **Document Summaries**: Automatic generation of concise document summaries
- **Report Creation**: Structured reports based on your document collection
- **Template Generation**: Custom templates for various document types
- **Safe File Operations**: All generated content stored in dedicated directories

### 🖥️ **Modern Desktop Interface**
- **PySide6/Qt Framework**: Native, responsive desktop application
- **Intuitive Chat Interface**: Natural conversation with your documents
- **Real-time Citations**: See exactly which documents inform each response
- **Progress Tracking**: Visual feedback during indexing and processing
- **Customizable Settings**: Flexible configuration for different use cases

### 🔒 **Security & Privacy**
- **Local Processing**: All documents remain on your machine
- **Encrypted API Keys**: Secure storage of sensitive credentials
- **Machine-Specific Encryption**: Keys tied to your specific device
- **Read-Only Architecture**: Original documents are never modified

## Architecture

InsightOS is built with a modular, extensible architecture:

### Core Components

- **`main.py`**: Application entry point with MCP support and initialization
- **`config/`**: Application-wide settings and configuration management
- **`security/`**: Encrypted API key management and security utilities
- **`indexing/`**: Document processing, chunking, and ChromaDB integration
- **`core/`**: RAG retrieval, prompt templates, and tool execution
- **`agent/`**: Claude API integration and AI conversation handling
- **`ui/`**: Complete PySide6 interface with widgets and dialogs
- **`mcp_servers/`**: Model Context Protocol server management
- **`utils/`**: Logging, file utilities, and validation helpers

### Supported File Types

**Documents**: PDF, DOC, DOCX, ODT, Pages, RTF  
**Text**: TXT, MD, ASC  
**Code**: PY, JAVA, JS, TS, CPP, C, CS, RB, GO, RS, PHP, Swift, Kotlin  
**Web**: HTML, CSS, XML, JSON, YAML  
**Data**: CSV, TSV, LOG  
**Config**: INI, CFG, CONF, TOML  

### MCP Server Integration

InsightOS implements the Model Context Protocol for extensible AI capabilities:

- **Filesystem Server**: Safe file writing to designated output directories
- **Memory Server**: Persistent knowledge graph for conversation context
- **Brave Search Server**: Web search integration for research tasks

## Installation & Setup

### Prerequisites

- Python 3.10 or higher
- Claude API key from Anthropic
- Supported operating systems: macOS, Windows, Linux

### Dependencies

- **PySide6**: Modern Qt-based GUI framework
- **anthropic**: Official Claude API client
- **chromadb**: Vector database for document embeddings
- **Additional libraries**: See requirements for complete list

### First-Time Setup

1. Launch InsightOS
2. Complete the setup wizard:
   - Enter your Claude API key (encrypted and stored securely)
   - Select directories containing your documents
   - Configure indexing preferences
3. Wait for initial document indexing to complete
4. Start asking questions about your documents!

## Usage

### Basic Workflow

1. **Index Documents**: Add directories containing your documents
2. **Ask Questions**: Use natural language to query your document collection
3. **Get Contextual Answers**: Receive AI-generated responses with source citations
4. **Generate Content**: Create summaries, reports, and other documents
5. **Manage Settings**: Customize behavior, API settings, and file types

### Advanced Features

- **Agentic Mode**: Enable advanced AI reasoning for complex tasks
- **Custom Chunking**: Adjust text segmentation for optimal retrieval
- **Similarity Thresholds**: Fine-tune search sensitivity
- **File Type Filtering**: Control which document types to index
- **Output Management**: Organize generated files in structured directories

## Configuration

InsightOS stores configuration in `~/.insightos/`:

- **`config.json`**: Main application settings
- **`.api_key.enc`**: Encrypted Claude API key
- **`logs/`**: Application logs and debugging information
- **`chroma/`**: ChromaDB vector database files
- **`mcp/`**: MCP server configurations

Generated files are saved to `~/InsightOS/Generated/` with organized subdirectories for different content types.

## Technical Specifications

- **Framework**: PySide6 (Qt6) for cross-platform desktop GUI
- **AI Model**: Claude (Anthropic) with configurable model selection
- **Vector Database**: ChromaDB for semantic search and retrieval
- **Text Processing**: Advanced chunking with overlap for context preservation
- **Security**: Fernet encryption for API key storage with PBKDF2 key derivation
- **Architecture**: Modular design with clear separation of concerns
- **Extensibility**: MCP protocol support for adding new AI capabilities

## Development

InsightOS follows modern Python development practices:

- **Type Hints**: Comprehensive type annotations throughout
- **Logging**: Structured logging with rotation and retention
- **Error Handling**: Robust exception handling and user feedback
- **Configuration Management**: Centralized settings with validation
- **Testing**: Diagnostic tools and validation utilities
- **Documentation**: Inline documentation and clear code structure

## License

This software is proprietary and developed by Raja Said. All rights reserved.

---

**InsightOS** - Transforming how you interact with your knowledge, one document at a time.