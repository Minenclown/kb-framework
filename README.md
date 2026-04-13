# KB Framework

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

**Knowledge Base Framework with ChromaDB, Hybrid Search and Obsidian Vault Support.**

## Quick Start (CLI)

```bash
# Install
pip install -r requirements.txt
./install.sh

# Use the CLI
kb index /path/to/docs          # Index documents
kb search "your query"          # Search knowledge base
kb stats                        # Show statistics
kb update                       # Check for updates
```

---

## Features

### Knowledge Base
- **ChromaDB Integration** - Vector search for semantic similarity
- **Hybrid Search** - Combined keyword + vector search
- **PDF Indexing** - Automatic PDF document indexing
- **Embedding Pipeline** - Flexible embedding generation
- **Auto-Update** - Built-in updater like `openclaw update`

### Obsidian Integration
- **Parser** - WikiLinks, Tags, Frontmatter, Embeds
- **Resolver** - Path resolution with shortest-match algorithm
- **Indexer** - Inverted backlink index
- **Vault** - High-level API for all Obsidian operations
- **Writer** - Write functions (Create, Update, Delete)

---

## CLI Usage

The `kb` command provides easy access to all features:

```bash
# Indexing
kb index /path/to/file.md           # Index single file
kb index /path/to/directory         # Index entire directory

# Search
kb search "machine learning"       # Search knowledge base
kb search "query" -l 20             # Limit to 20 results

# Maintenance
kb stats                            # Show database statistics
kb audit                            # Run full audit
kb ghost                            # Find orphaned entries
kb warmup                           # Preload ChromaDB model

# Updates
kb update                           # Check and install updates
kb update --check                   # Only check, don't install
kb update --force                   # Force reinstall
```

---

## Installation

```bash
# Clone to OpenClaw workspace
git clone https://github.com/Minenclown/kb-framework.git ~/.openclaw/kb

# Or manually:
cp -r kb-framework ~/.openclaw/kb

# Install dependencies
pip install -r requirements.txt
./install.sh
```

For global CLI access, add to your `.bashrc`:
```bash
alias kb="~/.openclaw/kb/kb.sh"
```

---

## Quick Start (Python API)

### Knowledge Base

```python
from kb.indexer import KBIndexer

kb = KBIndexer()
kb.index_directory("/path/to/docs")
results = kb.search("query text")
```

### Obsidian Vault

```python
from kb.obsidian import ObsidianVault

vault = ObsidianVault("/path/to/vault")
vault.index()

# Find backlinks
backlinks = vault.find_backlinks("Notes/Meeting.md")

# Full-text search
results = vault.search("Project X")
```

---

## Tests

```bash
python -m pytest tests/ -v
```

**153 Tests** - All passing.

---

## Structure

```
~/.openclaw/kb/                    # Installation path
├── kb/                            # Core Python modules
│   ├── indexer.py                 # KB Core (MarkdownIndexer)
│   ├── __main__.py               # CLI entry point
│   ├── update.py                 # Auto-updater
│   ├── version.py                # Current version
│   ├── obsidian/                 # Obsidian Integration
│   │   ├── parser.py
│   │   ├── resolver.py
│   │   ├── indexer.py
│   │   ├── vault.py
│   │   └── writer.py
│   └── scripts/                  # Utility scripts
│       ├── index_pdfs.py
│       ├── kb_ghost_scanner.py
│       ├── kb_full_audit.py
│       └── kb_warmup.py
├── library/                       # Your content lives here
│   ├── content/                  # Raw files (PDFs, docs, logs)
│   │   ├── Gesundheit/
│   │   ├── Projekte/
│   │   └── (your folders)
│   └── agent/                    # Markdown files for agents
│       ├── projektplanung/
│       ├── memory/
│       ├── Workflow_Referenzen/
│       └── (your folders)
├── chroma_db/                     # ChromaDB vector database
├── knowledge.db                   # Main SQLite database
├── kb.sh                         # CLI wrapper script
├── tests/                        # Test suite
├── README.md
├── LICENSE
└── requirements.txt
```

**Important:** The `library/` directory contains your actual content. This is separate from the framework code and is not pushed to GitHub.

---

## License

MIT License - see [LICENSE](LICENSE)

## Known Issues

### Database
- **NULL file_path**: Historically there were sections without file_path. Fixed in recent commits.
- **ChromaDB Sync**: Re-indexing can cause discrepancies. Use `kb_full_audit.py` to check.

### Performance
- **Embedding Generation**: First run is slow (downloads sentence-transformers model).
- **OCR**: Tesseract (Standard, CPU-optimiert), EasyOCR (optional, GPU-recommended).

### Development
- See `UPDATE_GOALS.md` for planned improvements.
