# InsightOS

**Your Intelligent Desktop Knowledge Assistant**

InsightOS is an AI-powered desktop application that helps you understand your documents and create new content through natural conversation. Built with PySide6 and powered by Claude AI, it combines semantic search with agentic file operations to turn your document collection into an intelligent knowledge base.

---

## 🌟 Features

### Core Capabilities

- **🔍 Smart Document Search** - Ask questions about your files in natural language using AI-powered semantic search
- **📝 Agentic File Creation** - Create documents, reports, summaries, and data files through conversation
- **📚 Multi-Format Support** - Works with PDFs, Word documents, spreadsheets, Markdown, code files, and more
- **✅ Citation & Verification** - Get answers with precise citations linking back to source documents
- **🔒 Local & Private** - All processing happens on your machine, your data never leaves your computer

### Advanced Features

- **🎯 RAG (Retrieval-Augmented Generation)** - Combines document search with AI generation for accurate, grounded answers
- **🤖 Agentic Mode** - AI can autonomously search, read, and create files to accomplish your tasks
- **🔧 MCP Integration** - Secure file operations through Model Context Protocol servers
- **🌍 Multi-lingual Support** - Supports English, Hebrew, Arabic, and 100+ languages with RTL support
- **💾 Vector Database** - Fast semantic search using ChromaDB with sentence-transformers embeddings

---

## 📋 Requirements

### System Requirements

- **Operating System**: macOS 10.15+, Windows 10+, or Linux
- **Python**: 3.10 or higher
- **Node.js**: 18+ (for MCP servers)
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 500MB for application + space for document index

### API Requirements

- **Claude API Key** (required) - Get one from [Anthropic Console](https://console.anthropic.com/)

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/insightos.git
cd insightos
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Required packages:**
- `anthropic>=0.18.0` - Claude API client
- `chromadb>=0.4.24` - Vector database
- `sentence-transformers>=2.3.0` - Text embeddings
- `PySide6==6.10.1` - UI framework
- `cryptography>=41.0.0` - Secure key storage
- `python-docx>=1.1.0` - Word document processing
- `PyPDF2>=3.0.0` - PDF processing
- `openpyxl>=3.1.0` - Excel processing
- `python-pptx>=0.6.23` - PowerPoint processing
- `markdown>=3.5.0` - Markdown processing
- `beautifulsoup4>=4.12.0` - HTML processing
- `python-dotenv>=1.0.0` - Environment configuration

### 3. Install Node.js (for MCP Servers)

**macOS:**
```bash
brew install node
```

**Ubuntu/Debian:**
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

**Windows:**
Download from [nodejs.org](https://nodejs.org/)

**Verify installation:**
```bash
node --version  # Should be 18+
npx --version   # Should work
```

### 4. Run the Application

```bash
python main.py
```

On first launch, the setup wizard will guide you through:
1. Entering your Claude API key
2. Selecting directories to index
3. Initial document indexing

---

## 📖 Usage

### Quick Start

1. **Launch InsightOS**
   ```bash
   python main.py
   ```

2. **Add Directories**
   - Click "Add Directory" in the sidebar
   - Select folders containing your documents
   - Wait for indexing to complete

3. **Ask Questions**
   - Type your question in the chat input
   - Press Enter or Cmd+Enter to send
   - Get answers with citations to source files

4. **Create Files (Agentic Mode)**
   - Enable "Agentic Mode" in Settings → Advanced
   - Ask Claude to create files: "Create a summary of my meeting notes"
   - Files appear in the Generated Files browser

### Basic Queries

```
"What are the main points in my Q4 report?"
"Summarize the meeting notes from last week"
"Find information about budget allocation in 2024"
"What did the contract say about payment terms?"
```

### Agentic Queries (File Creation)

```
"Create a summary of my project documentation"
"Extract all action items from my meeting notes into a CSV"
"Write a report comparing Q3 and Q4 sales data"
"Create a markdown file with key points from my research"
```

### Keyboard Shortcuts

- **Cmd+N** (Ctrl+N) - New conversation
- **Cmd+Enter** (Ctrl+Enter) - Send message
- **Cmd+K** (Ctrl+K) - Clear conversation
- **Cmd+O** (Ctrl+O) - Add directory
- **Cmd+R** (Ctrl+R) - Re-index all
- **Cmd+,** (Ctrl+,) - Settings
- **Cmd+Q** (Ctrl+Q) - Quit

---

## 🎯 Key Concepts

### RAG (Retrieval-Augmented Generation)

InsightOS uses RAG to provide accurate, grounded answers:

1. **Indexing**: Documents are split into chunks and converted to vector embeddings
2. **Retrieval**: When you ask a question, the most relevant chunks are retrieved
3. **Generation**: Claude uses the retrieved context to generate an accurate answer
4. **Citation**: References to source documents are included

### Agentic Mode

When enabled, Claude can autonomously:
- Search through your indexed documents
- Read files from your directories
- Create new files (documents, reports, data files)
- Execute multi-step workflows

**Security**: File operations are restricted to the Generated folder (`~/InsightOS/Generated/`)

### MCP (Model Context Protocol)

InsightOS uses official MCP servers for file operations:
- **Filesystem Server**: Handles file read/write operations
- **Memory Server**: (Optional) Provides conversation memory
- **Brave Search**: (Optional) Web search capabilities

MCP servers run as separate processes with restricted permissions.

---

## ⚙️ Configuration

### Settings Dialog

Access via **Cmd+,** or **Settings** menu.

#### General Tab
- **Top K Results**: Number of document chunks to retrieve (default: 5)
- **File Types**: Enable/disable specific file types for indexing

#### API Key Tab
- **Claude API Key**: Your Anthropic API key
- **Test Connection**: Verify API key is valid

#### Advanced Tab
- **Agentic Mode**: Enable/disable autonomous file operations
- **MCP Servers**: Configure Model Context Protocol servers
- **Chunk Size**: Size of document chunks (default: 500 characters)
- **Chunk Overlap**: Overlap between chunks (default: 50 characters)
- **Clear Vector Database**: Reset the entire index

### Configuration Files

- **Config**: `~/.insightos/config.json`
- **API Key**: `~/.insightos/api_key.enc` (encrypted)
- **Vector Database**: `~/.insightos/chromadb/`
- **Logs**: `~/.insightos/logs/insightos.log`
- **Generated Files**: `~/InsightOS/Generated/`

---

## 📁 Supported File Formats

### Documents
- `.pdf` - PDF documents
- `.docx`, `.doc` - Microsoft Word
- `.pptx` - PowerPoint presentations
- `.xlsx`, `.xls` - Excel spreadsheets

### Text Files
- `.txt` - Plain text
- `.md` - Markdown
- `.rtf` - Rich Text Format

### Code Files
- `.py` - Python
- `.java` - Java
- `.js` - JavaScript
- `.html`, `.htm` - HTML
- `.css` - CSS

### Data Files
- `.csv` - CSV files
- `.log` - Log files
- `.json` - JSON (via code reader)

### Other
- `.asc` - ASCII text files

---

## 🔧 Architecture

### Components

```
InsightOS/
├── main.py                 # Application entry point
├── ui/                     # User interface
│   ├── main_window.py     # Main application window
│   ├── widgets/           # Reusable UI widgets
│   └── dialogs/           # Settings, setup wizard
├── core/                   # Core logic
│   ├── rag_retriever.py   # RAG retrieval
│   └── prompt_templates.py # System prompts
├── agent/                  # Agent layer
│   └── claude_client.py   # Claude API integration
├── indexing/              # Document indexing
│   ├── indexer.py         # Main indexer
│   ├── chromadb_client.py # Vector database
│   ├── readers/           # File readers
│   └── text_chunker.py    # Text chunking
├── mcp_servers/           # MCP integration
│   ├── client.py          # MCP client
│   └── config.py          # MCP configuration
├── security/              # Security & config
│   └── config_manager.py  # Configuration management
└── utils/                 # Utilities
    └── logger.py          # Logging

```

### Data Flow

```
User Query
    ↓
RAG Retriever
    ↓
ChromaDB Vector Search → Retrieve relevant chunks
    ↓
Claude API (with context)
    ↓
Response + Citations
    ↓
UI Display
```

### Agentic Mode Flow

```
User Request
    ↓
Claude Client (with tools)
    ↓
Tool Selection (search_documents, write_file, etc.)
    ↓
Tool Execution (Traditional or MCP)
    ↓
Tool Result → Claude
    ↓
Continue or Final Response
    ↓
UI Display + Generated Files Browser
```

---

## 🛡️ Security & Privacy

### Data Privacy

- ✅ **All data stays local** - Documents never leave your machine
- ✅ **Encrypted API key** - Stored securely using system keychain
- ✅ **No telemetry** - No usage data is collected or sent
- ✅ **Open architecture** - All data flows are transparent

### File System Security

- ✅ **Restricted write access** - File creation limited to `Generated/` folder
- ✅ **Read-only document access** - Indexed documents are never modified
- ✅ **MCP sandboxing** - File servers run in isolated processes
- ✅ **User consent required** - Agentic mode requires explicit opt-in

### API Security

- ✅ **Secure key storage** - API keys encrypted with system credentials
- ✅ **HTTPS only** - All API communication over secure channels
- ✅ **No key logging** - API keys never written to logs

---

## 🐛 Troubleshooting

### Common Issues

#### "No API key configured"
**Solution**: Go to Settings → API Key and enter your Claude API key from console.anthropic.com

#### "npx not found" error
**Solution**: Install Node.js (version 18+)
```bash
# macOS
brew install node

# Ubuntu/Debian
sudo apt install nodejs npm
```

#### "Import error: sentence-transformers"
**Solution**: Install the package
```bash
pip install sentence-transformers --break-system-packages
```

#### Search returns no results
**Solutions**:
1. Make sure directories are indexed (check sidebar)
2. Try different keywords
3. Lower the similarity threshold in Settings
4. Re-index directories (Cmd+R)

#### MCP server failed to start
**Solution**: Check Node.js installation
```bash
npx --version  # Should work
npx -y @modelcontextprotocol/server-filesystem .  # Test manually
```

#### Indexing fails for certain files
**Solution**: Check logs at `~/.insightos/logs/insightos.log` for details

### Logs

View detailed logs:
```bash
tail -f ~/.insightos/logs/insightos.log
```

Enable debug logging:
```python
# In config/settings.py
LOG_LEVEL = "DEBUG"
```

---

## 🔄 Updating

### Update Python Dependencies

```bash
pip install -r requirements.txt --upgrade
```

### Update MCP Servers

MCP servers auto-update via npx. To force update:
```bash
npx clear-npx-cache
```

### Update the Application

```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

---

## 💡 Tips & Best Practices

### Indexing

- **Start small**: Index one directory first to test
- **Organize files**: Keep related documents in the same folder
- **Regular updates**: Re-index when you add new documents
- **File naming**: Use descriptive filenames for better search results

### Querying

- **Be specific**: "Q4 sales numbers" is better than "sales"
- **Use keywords**: Include specific terms from your documents
- **Ask follow-ups**: Build on previous answers in the conversation
- **Check citations**: Verify information in source documents

### Agentic Mode

- **Clear requests**: "Create a summary document" vs "help me with files"
- **Specify format**: "Create a CSV" vs "create a file"
- **Review outputs**: Check generated files before using them
- **Iterate**: Ask Claude to refine or modify generated content

### Performance

- **Chunk size**: Larger chunks (500-800) for technical docs, smaller (300-500) for general text
- **Top K**: Start with 5, increase to 10 for complex queries
- **GPU acceleration**: Not required, but sentence-transformers can use it if available

---

## 🤝 Contributing

This is proprietary software. Contributions are not accepted at this time.

---

## 📄 License

**Proprietary License**

This software is proprietary and confidential. All rights reserved.

Unauthorized copying, distribution, modification, or use of this software is strictly prohibited.

---

## 🙏 Acknowledgments

### Technologies Used

- **[Claude AI](https://www.anthropic.com/)** - Advanced language model by Anthropic
- **[ChromaDB](https://www.trychroma.com/)** - Open-source vector database
- **[Sentence-Transformers](https://www.sbert.net/)** - State-of-the-art text embeddings
- **[PySide6](https://wiki.qt.io/Qt_for_Python)** - Official Python Qt bindings
- **[Model Context Protocol](https://modelcontextprotocol.io/)** - Standardized AI-app integration

### Inspiration

InsightOS was built to solve the problem of knowledge retrieval across large document collections, combining the power of semantic search with agentic AI capabilities.

---

## 📞 Support

For issues, questions, or feedback:

- **Email**: support@insightos.app
- **GitHub Issues**: github.com/yourusername/insightos/issues
- **Documentation**: docs.insightos.app

---

## 🗺️ Roadmap

### Planned Features

- [ ] Hybrid search (BM25 + semantic)
- [ ] Cross-encoder reranking
- [ ] Conversation history export
- [ ] Custom embedding models
- [ ] Cloud sync (optional)
- [ ] Plugin system
- [ ] Web interface
- [ ] Mobile app

### Recent Updates

**v1.0.0** (Current)
- ✅ Initial release
- ✅ RAG with Claude Sonnet 4.5
- ✅ MCP integration
- ✅ Agentic file creation
- ✅ Multi-lingual support
- ✅ Generated files browser
- ✅ Text normalization

---

## 📊 System Information

**Version**: 1.0.0  
**Release Date**: January 2026  
**Python Version**: 3.10+  
**Supported Platforms**: macOS, Windows, Linux  
**Claude Model**: Claude Sonnet 4.5  
**Embedding Model**: all-MiniLM-L6-v2  

---

<p align="center">
  <b>Built with ❤️ for knowledge workers</b><br>
  InsightOS - Your Intelligent Desktop Knowledge Assistant
</p>