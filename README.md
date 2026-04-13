# KB Framework

![Tests](https://img.shields.io/badge/tests-153%20passed-brightgreen)
![Python](https://img.shields.io/badge/python-3.8+-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![ChromaDB](https://img.shields.io/badge/chromadb-0.4+-red)
![Obsidian](https://img.shields.io/badge/obsidian-ready-purple)

**Knowledge Base Framework with ChromaDB, Hybrid Search and Obsidian Vault Support.**

---

## Features

### Knowledge Base
- **ChromaDB Integration** - Vector search for semantic similarity
- **Hybrid Search** - Combined keyword + vector search
- **PDF Indexing** - Automatic PDF document indexing
- **Embedding Pipeline** - Flexible embedding generation

### Obsidian Integration
- **Parser** - WikiLinks, Tags, Frontmatter, Embeds
- **Resolver** - Path resolution with shortest-match algorithm
- **Indexer** - Inverted backlink index
- **Vault** - High-level API for all Obsidian operations
- **Writer** - Write functions (Create, Update, Delete)

---

## Installation

```bash
pip install -r requirements.txt
./install.sh
```

---

## Quick Start

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
│   ├── obsidian/               # Obsidian Modules
│   │   ├── parser.py
│   │   ├── resolver.py
│   │   ├── indexer.py
│   │   ├── vault.py
│   │   └── writer.py
│   └── scripts/                # Utilities
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
- **NULL file_path**: Historisch gab es Sections ohne file_path. Fixed in recent commits.
- **ChromaDB Sync**: Bei Re-Indexing können Diskrepanzen entstehen. Use `kb_full_audit.py` to check.

### Performance
- **Embedding Generation**: First run is slow (downloads sentence-transformers model).
- **OCR**: EasyOCR is slow on large PDFs (~30s/page).

### Development
- See `FIX_PLAN.md` for planned improvements.
