# KB Framework

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

**Knowledge Base Framework with ChromaDB, Hybrid Search and Obsidian Vault Support.**

## Quick Start

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
pip install -r requirements.txt
./install.sh
```

For global CLI access, add to your `.bashrc`:
```bash
alias kb="/path/to/kb-framework/kb.sh"
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
kb-framework/
├── kb/
│   ├── indexer.py              # KB Core
│   ├── __main__.py            # CLI entry point
│   ├── update.py              # Auto-updater
│   ├── version.py             # Current version
│   ├── obsidian/              # Obsidian Modules
│   │   ├── parser.py
│   │   ├── resolver.py
│   │   ├── indexer.py
│   │   ├── vault.py
│   │   └── writer.py
│   └── scripts/               # Utilities
├── kb.sh                       # CLI wrapper script
├── tests/                      # 153 Tests
├── README.md
├── LICENSE
└── requirements.txt
```

---

## License

MIT License - see [LICENSE](LICENSE)

## Known Issues

### Database
- **NULL file_path**: Historically there were sections without file_path. Fixed in recent commits.
- **ChromaDB Sync**: Re-indexing can cause discrepancies. Use `kb_full_audit.py` to check.

### Performance
- **Embedding Generation**: First run is slow (downloads sentence-transformers model).
- **OCR**: EasyOCR is slow on large PDFs (~30s/page).

### Development
- See `FIX_PLAN.md` for planned improvements.
