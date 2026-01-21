# InsightOS 🧠

> **Your Personal AI Knowledge Assistant** - Transform your documents into an intelligent, conversational knowledge base powered by Claude AI and RAG technology.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)
[![Claude AI](https://img.shields.io/badge/AI-Claude-orange.svg)](https://www.anthropic.com/)
[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)

---

## ✨ Features

### 🎯 Core Capabilities

- **💬 AI-Powered Chat**: Converse naturally with your documents using Claude 4.5 Sonnet
- **🔍 Semantic Search**: RAG-based retrieval finds relevant information across all your files
- **📁 Multi-Format Support**: PDF, DOCX, TXT, MD, HTML, CSV, and more
- **💾 Local Vector Database**: Your data stays private with local ChromaDB storage
- **📝 File Generation**: AI creates summaries, reports, and structured extracts
- **🔐 Privacy-First Design**: Explicit consent model with clear data handling

### 🚀 Advanced Features

- **🛠️ MCP Integration**: Model Context Protocol servers for extended capabilities
  - Filesystem server (restricted write access)
  - Memory server (knowledge graph)
  - Brave Search (optional web search)
- **⚡ Async Processing**: Non-blocking UI with background workers
- **📊 Real-Time Indexing**: Automatic document processing and updates
- **🎨 Native Interface**: Beautiful macOS-style UI on all platforms
- **🔄 Context Awareness**: Multi-turn conversations with memory
- **📂 Generated Files Browser**: Dedicated panel for AI-created content

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** 
- **Anthropic API Key** ([Get yours here](https://console.anthropic.com/))

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/insightos.git
cd insightos

# 2. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install node
brew install node
node --version     # Should be 18+

# 5. Launch InsightOS
python main.py
```

### First-Time Setup

The setup wizard will guide you through:

1. **Enter API Key**: Your Claude API key from Anthropic
2. **Add Directories**: Select folders containing your documents
3. **Initial Indexing**: Wait while documents are processed
4. **Start Chatting**: Ask questions about your knowledge base!

---

## 📖 Usage Guide

### Basic Workflow

**1. Add Documents**
- Click **"Add Directory"** in the sidebar
- Select folders with your files
- InsightOS automatically indexes supported formats

**2. Ask Questions**
- Type natural language queries in the chat
- Get AI responses with citations from your documents
- Multi-turn conversations maintain context

**3. Generate Content** (Optional)
- Enable **Agentic Mode** in Settings → Advanced
- Ask AI to create summaries, reports, or extracts
- Files appear in the Generated Files browser

### Example Queries

```
📝 "Summarize all research papers about transformers"
🔍 "What did we decide about the API redesign?"
📊 "Create a quarterly report from my meeting notes"
📋 "Extract action items from documents into CSV"
🎯 "What are the key themes across all project docs?"
```

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Cmd+N` / `Ctrl+N` | New conversation |
| `Cmd+K` / `Ctrl+K` | Clear conversation |
| `Cmd+O` / `Ctrl+O` | Add directory |
| `Cmd+R` / `Ctrl+R` | Re-index all |
| `Cmd+,` / `Ctrl+,` | Settings |
| `Cmd+Enter` | Send message |

---

## ⚙️ Configuration

### Settings Overview

Access via **File → Settings** or **Cmd+,** / **Ctrl+,**

#### 📋 General Tab

- **Top K Results**: Number of chunks to retrieve (1-20, default: 5)
- **File Types**: Select which formats to index
- Configure indexed file extensions

#### 🔑 API Key Tab

- Add/update Claude API key
- Validate key before saving
- Remove key if needed
- Key stored encrypted with AES-256

#### 🔧 Advanced Tab

**Text Chunking**
- Chunk size: 100-5000 characters (default: 300)
- Overlap: 0-1000 characters (default: 60)
- Changing requires re-indexing

**Agentic Mode** ⚠️
- Enables AI tools + MCP servers
- **Privacy Warning**: AI can read files
- Requires explicit consent
- **Do NOT use with HIPAA/GDPR data**

**Cache Management**
- Clear vector database
- Reset index if needed

### MCP Server Configuration

Managed automatically when Agentic Mode is enabled:

| Server | Function | Default State |
|--------|----------|---------------|
| **filesystem** | File read/write in `Generated/` | Disabled* |
| **memory** | Knowledge graph & entities | Enabled |
| **brave-search** | Web search capability | Disabled |

\* Requires Agentic Mode + consent

**Generated Files Location**: `~/InsightOS/Generated/`
- `summaries/` - AI-generated summaries
- `reports/` - Detailed reports  
- `extracts/` - Structured data (CSV, JSON)
- `templates/` - Document templates

---

## 🏗️ Architecture

### System Overview

```
┌───────────────────────────────────────────────────────────────┐
│                        InsightOS                              │
├───────────────────────────────────────────────────────────────┤
│  ┌──────────┐    ┌─────────────────┐    ┌─────────────────┐  │
│  │ Sidebar  │    │  Chat Widget    │    │  Generated      │  │
│  │          │    │                 │    │  Files Browser  │  │
│  │ • Dirs   │    │  User: Query    │    │                 │  │
│  │ • Stats  │    │       ↓         │    │  📁 Summaries  │  │
│  │ • Index  │    │  RAG Search     │    │  📁 Reports    │  │
│  │          │    │  (ChromaDB)     │    │  📁 Extracts   │  │
│  │ 📊 1,234 │    │       ↓         │    │  📁 Templates  │  │
│  │  chunks  │    │  Claude API     │    │                 │  │
│  │          │    │  + Context      │    │  Auto-refresh   │  │
│  │          │    │       ↓         │    │  on file write  │  │
│  │          │    │  AI: Response   │    │                 │  │
│  │          │    │  + Citations    │    │                 │  │
│  └──────────┘    └─────────────────┘    └─────────────────┘  │
│                                                               │
└───────────────────────────────────────────────────────────────┘
│  🟢 API Key | 🟢 Agent | 🟢 MCP | 📁 1,234 chunks indexed   │
└───────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Component | Technology |
|-----------|-----------|
| **UI Framework** | PyQt6 |
| **AI Model** | Claude 4.5 Sonnet (Anthropic) |
| **Vector Database** | ChromaDB |
| **Embeddings** | Sentence Transformers (all-MiniLM-L6-v2) |
| **Document Parsing** | PyPDF2, python-docx, BeautifulSoup |
| **Protocol** | Model Context Protocol (MCP) |
| **Security** | AES-256 encryption (cryptography) |

### Data Flow

```
User Query
    ↓
┌─────────────────┐
│ RAG Retriever   │ → Searches ChromaDB vector store
└────────┬────────┘
         ↓
┌─────────────────┐
│ Context Builder │ → Formats top-K chunks + metadata
└────────┬────────┘
         ↓
┌─────────────────┐
│ Claude Client   │ → API call with context
└────────┬────────┘
         ↓
┌─────────────────┐
│ Response        │ → Display with citations
└─────────────────┘
```

---

## 📁 Project Structure

```
InsightOS/
├── main.py                          # Application entry point
├── requirements.txt                 # Python dependencies
├── README.md                        # This file
│
├── agent/                          # AI Agent Layer
│   ├── __init__.py
│   ├── claude_client.py           # Claude API wrapper
│   ├── prompts.py                 # System prompts & templates
│   └── file_generator.py          # File creation utilities
│
├── config/                         # Configuration
│   └── settings.py                # App constants
│
├── core/                           # Core Business Logic
│   └── rag_retriever.py           # RAG retrieval system
│
├── indexing/                       # Document Processing
│   ├── indexer.py                 # Main indexer
│   ├── chromadb_client.py         # Vector DB interface
│   └── file_readers/              # Format-specific parsers
│       ├── pdf_reader.py
│       ├── docx_reader.py
│       └── ...
│
├── mcp_servers/                    # MCP Configuration
│   ├── __init__.py
│   ├── config.py                  # Server management
│   └── README.md                  # MCP documentation
│
├── security/                       # Security & Encryption
│   └── config_manager.py          # Config + key management
│
├── ui/                            # User Interface
│   ├── main_window.py             # Main application window
│   │
│   ├── widgets/                   # Reusable Components
│   │   ├── chat_widget.py        # Chat interface
│   │   ├── sidebar_widget.py     # Directory manager
│   │   └── message_widgets.py    # Message bubbles
│   │
│   ├── dialogs/                   # Dialog Windows
│   │   ├── settings_dialog.py    # Settings UI
│   │   └── setup_wizard.py       # First-run setup
│   │
│   ├── generated_files_browser.py # File browser
│   │
│   └── styles/                    # UI Styling
│       ├── colors.py
│       └── fonts.py
│
└── utils/                         # Utilities
    └── logger.py                  # Logging configuration
```

---

## 🔐 Security & Privacy

### Data Storage Locations

```
~/.insightos/                      # Config directory
├── config.json                    # Application settings
├── .api_key.enc                   # Encrypted API key (AES-256)
├── chromadb/                      # Vector database (local)
├── logs/                          # Application logs
└── mcp/
    └── servers.json               # MCP server config

~/InsightOS/                       # User data directory
└── Generated/                     # AI-generated files
    ├── summaries/
    ├── reports/
    ├── extracts/
    └── templates/
```

### Privacy Model

#### 🟢 Standard RAG Mode (Default - Safe)

- ✅ Only document chunks sent to Claude API
- ✅ AI cannot read entire files
- ✅ Context limited to search results
- ✅ No file modification by AI
- ✅ Safe for most use cases

#### ⚠️ Agentic Mode (Optional - Advanced)

- ⚠️ AI can read entire files via tools
- ⚠️ File contents transmitted to Anthropic
- ⚠️ AI can write files to `Generated/` directory
- ⚠️ Requires explicit user consent
- ⚠️ Shows privacy warnings

### ⛔ When NOT to Use Agentic Mode

**DO NOT ENABLE if you work with:**
- 🏥 Protected Health Information (HIPAA)
- 🔒 Personal data subject to GDPR/CCPA
- 💼 Confidential business documents
- 🎓 Sensitive research data
- ⚖️ Legally privileged information
- 🔐 Any regulated or classified data

### Security Features

- 🔒 **API Key Encryption**: AES-256-GCM encryption at rest
- 🔒 **Filesystem Restrictions**: AI write access limited to `Generated/` only
- 🔒 **Explicit Consent**: Clear warnings before enabling file access
- 🔒 **Security Validation**: Filesystem permissions checked on startup
- 🔒 **Local Processing**: Vector database stays on your machine

---

## 🛠️ Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/yourusername/insightos.git
cd insightos

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Run with debug logging
python main.py
```

### Development Tools

```bash
# Format code
black .

# Lint
flake8 insightos/
pylint insightos/

# Type checking
mypy .

# Run tests
pytest

# Coverage report
pytest --cov=. --cov-report=html
```

### Reset Configuration (Development)

```bash
# Clear all config and start fresh
python main.py --reset
```

This removes:
- `~/.insightos/config.json`
- `~/.insightos/.api_key.enc`
- `~/.insightos/mcp/servers.json`

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_rag_retriever.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=core --cov=agent --cov-report=html
```

---

## 🐛 Troubleshooting

### Common Issues

#### ❌ "No API key configured"

**Symptom**: Red API status in status bar  
**Solution**: 
1. Open Settings → API Key
2. Enter your Claude API key
3. Click "Validate Key" then "Save"

#### ❌ "Failed to initialize Claude client"

**Symptom**: Red Agent status in status bar  
**Solution**:
1. Verify API key at [console.anthropic.com](https://console.anthropic.com/)
2. Check internet connectivity
3. View logs: `~/.insightos/logs/insightos.log`
4. Try re-entering API key in Settings

#### ❌ "No results found for query"

**Symptom**: Empty search results  
**Solution**:
1. Check that directories are indexed (sidebar shows count)
2. Re-index: File → Re-index All (Ctrl+R)
3. Verify file types enabled in Settings → General
4. Ensure files contain searchable text (not scanned images)

#### ⚠️ "MCP filesystem validation failed"

**Symptom**: Yellow/Red MCP status  
**Solution**:
1. Check `~/InsightOS/Generated/` exists
2. Verify directory is writable
3. Restart application
4. If persists: `python main.py --reset`

#### 🐌 Indexing is slow

**Symptom**: Long indexing times  
**Solution**:
1. Reduce chunk size in Settings → Advanced
2. Disable unneeded file types in Settings → General
3. Index smaller directories incrementally
4. Check disk I/O performance

#### 💥 Application crashes on startup

**Symptom**: Window closes immediately  
**Solution**:
1. Check Python version: `python --version` (need 3.10+)
2. Reinstall dependencies: `pip install -r requirements.txt`
3. View logs: `cat ~/.insightos/logs/insightos.log`
4. Reset config: `python main.py --reset`

### Logs & Debugging

**Log Location**: `~/.insightos/logs/insightos.log`

```bash
# View real-time logs (macOS/Linux)
tail -f ~/.insightos/logs/insightos.log

# View last 50 lines
tail -n 50 ~/.insightos/logs/insightos.log

# Search for errors
grep ERROR ~/.insightos/logs/insightos.log
```

**Enable Debug Logging**:
Edit `utils/logger.py` and change log level:
```python
logging.DEBUG  # Instead of logging.INFO
```

---

## 📚 Documentation

- **[User Guide](docs/user-guide.md)**: Detailed usage instructions
- **[MCP Integration](mcp_servers/README.md)**: MCP server documentation
- **[API Reference](docs/api-reference.md)**: Code documentation
- **[Architecture](docs/architecture.md)**: System design details
- **[Contributing](CONTRIBUTING.md)**: Development guidelines

---

## 🗺️ Roadmap

### ✅ Version 1.0 (Current)

- RAG-based document chat
- MCP server integration
- File generation capabilities
- Unified privacy model
- Multi-format document support

### 🚧 Version 1.1 (In Progress)

- [ ] Export conversations to Markdown
- [ ] Custom MCP server support
- [ ] Advanced search filters
- [ ] Document annotations
- [ ] Conversation history browser

### 🔮 Version 2.0 (Future)

- [ ] Multi-language support (i18n)
- [ ] Team collaboration features
- [ ] Cloud sync (optional, encrypted)
- [ ] Mobile companion app
- [ ] Browser extension
- [ ] Voice input/output
- [ ] Custom embedding models

---

## 🤝 Contributing

**InsightOS is proprietary software** and the source code is not open for public contributions at this time.

However, we value feedback from our users:

### How You Can Help

- **🐛 Bug Reports**: Report issues via GitHub Issues or email support
- **💡 Feature Requests**: Share your ideas for improvements
- **📝 Documentation**: Help us improve documentation and tutorials
- **🌐 Translations**: Contact us about localization opportunities
- **⭐ Spread the Word**: Share InsightOS with colleagues who might benefit

### Beta Testing Program

Interested in early access to new features? Join our beta testing program:
- Email: beta@insightos.example.com
- Subject: "Beta Tester Application"

Beta testers receive free access to pre-release versions and help shape the product roadmap.

---

## 📄 License

**InsightOS is proprietary software.** All rights reserved.

### Copyright

© 2026 [Raja Said/RequestSoftware]. All Rights Reserved.

### License Terms

This software is licensed on a per-user basis. By purchasing a license, you agree to the following terms:

#### ✅ Permitted Uses (with valid license):
- Personal or commercial use within your organization
- Installation on up to 2 devices per license (Personal tier)
- Access to software updates during your license period
- Technical support as specified in your license tier

#### ❌ Prohibited Without License:
- Copying, modifying, or distributing the software
- Reverse engineering, decompiling, or disassembling
- Removing or altering copyright notices
- Sublicensing or transferring to third parties
- Using the software for service bureau purposes

### Pricing & License Tiers

| License Tier | Price | Use Case |
|-------------|-------|----------|
| **Personal** | $49 (one-time) | Individual users, up to 2 devices |
| **Professional** | $79 (one-time) | Power users, macOS + Windows, priority support |
| **Business** | $149/user (one-time) | Teams, unlimited devices, priority support |
| **Enterprise** | Contact Sales | Custom deployment, dedicated support, SLA |

### Purchase License

To purchase a license or for more information:
- **Website**: [https://insightos.example.com](https://insightos.example.com)
- **Email**: sales@insightos.example.com
- **Support**: support@insightos.example.com

### Educational & Non-Profit Discounts

Educational institutions and registered non-profit organizations may qualify for discounted licensing. Contact sales for details.

### Refund Policy

30-day money-back guarantee. If you're not satisfied, contact support@insightos.example.com for a full refund within 30 days of purchase.

---

**Full License Agreement**: See [LICENSE](LICENSE) file for complete legal terms.

---

## 🙏 Acknowledgments

### Built With

- **[Anthropic Claude](https://www.anthropic.com/)** - Advanced language model
- **[PyQt6](https://www.riverbankcomputing.com/software/pyqt/)** - Cross-platform GUI framework
- **[ChromaDB](https://www.trychroma.com/)** - Vector database for embeddings
- **[Sentence Transformers](https://www.sbert.net/)** - State-of-the-art embeddings
- **[Model Context Protocol](https://modelcontextprotocol.io/)** - Tool use standard

### Inspired By

- Personal knowledge management systems
- Second brain methodology
- RAG research and best practices
- Open source AI tools community

---

## ⚖️ Legal & Compliance

### Software License

InsightOS is **proprietary software** protected by copyright law. Use of this software requires a valid license. Unauthorized use, copying, or distribution is prohibited and may result in legal action.

### Data Processing

InsightOS processes documents locally and makes API calls to Anthropic's servers. When you use the application:

- **Local Processing**: Document indexing and vector storage happen on your machine
- **API Calls**: Queries and responses are transmitted to/from Anthropic
- **Agentic Mode**: File contents may be sent to Anthropic when enabled
- **No Data Collection**: We do not collect or transmit user data to InsightOS servers

### Third-Party Services

This software integrates with:
- **Anthropic Claude API**: Subject to [Anthropic's Terms of Service](https://www.anthropic.com/legal/consumer-terms)
- **Brave Search** (optional): Subject to [Brave's Terms of Service](https://brave.com/terms-of-use/)

Users are responsible for complying with all third-party terms of service.

### Warranties & Disclaimers

- ⚠️ This software is provided "as is" with a 30-day money-back guarantee
- ⚠️ Users are responsible for ensuring compliance with applicable data regulations (HIPAA, GDPR, CCPA, etc.)
- ⚠️ Not certified for use with regulated data without proper safeguards and risk assessment
- ⚠️ The developer provides the software with reasonable care but makes no warranties about fitness for specific regulated purposes
- ⚠️ Users must obtain appropriate legal counsel for regulated data use cases

### Limitation of Liability

To the maximum extent permitted by law, the developer shall not be liable for any indirect, incidental, special, consequential, or punitive damages arising from use of this software, including but not limited to data loss, privacy violations, or business interruption.

### Export Compliance

This software may be subject to export control laws. Users are responsible for compliance with all applicable export regulations.

---

## 📞 Support & Contact

### Get Help

- **📖 Documentation**: Check the [docs](docs/) folder
- **🐛 Issues**: [Report bugs or request features](https://github.com/yourusername/insightos/issues)
- **💬 Discussions**: [Ask questions or share ideas](https://github.com/yourusername/insightos/discussions)
- **📧 Email**: support@insightos.example.com

### Community

- **Discord**: [Join our server](https://discord.gg/insightos) (coming soon)
- **Twitter**: [@InsightOS](https://twitter.com/insightos) (coming soon)
- **Blog**: [blog.insightos.example.com](https://blog.insightos.example.com) (coming soon)

---

## 🌟 Star History

If you find InsightOS useful, please consider giving it a star! ⭐

Your support helps the project grow and improve.

---

<div align="center">

### Professional Knowledge Management Powered by AI

**[Purchase License](https://insightos.example.com/buy)** • **[Documentation](docs/)** • **[Support](https://insightos.example.com/support)**

---

© 2026 [Raja Said/RequestSoftware]. All Rights Reserved.  
InsightOS is proprietary software. Unauthorized use is prohibited.

</div>