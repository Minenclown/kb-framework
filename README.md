# KB Framework

![Tests](https://img.shields.io/badge/tests-153%20passed-brightgreen)
![Python](https://img.shields.io/badge/python-3.8+-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![ChromaDB](https://img.shields.io/badge/chromadb-0.4+-red)
![Obsidian](https://img.shields.io/badge/obsidian-ready-purple)

**Knowledge Base Framework mit ChromaDB, Hybrid Search und Obsidian Vault Support.**

---

## Features

### Knowledge Base
- **ChromaDB Integration** - Vector Search für semantische Ähnlichkeitssuche
- **Hybrid Search** - Kombinierte Keyword + Vector Suche
- **PDF Indexing** - Automatisches Indexieren von PDF Dokumenten
- **Embedding Pipeline** - Flexible Embedding-Generierung

### Obsidian Integration
- **Parser** - WikiLinks, Tags, Frontmatter, Embeds
- **Resolver** - Path Resolution mit Shortest-Match Algorithmus
- **Indexer** - Invertierter Backlink-Index
- **Vault** - High-Level API für alle Obsidian-Operationen
- **Writer** - Schreib-Funktionen (Create, Update, Delete)

---

## Installation

```bash
pip install -r requirements.txt
./install.sh
```

---

## Schnellstart

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

# Finde Backlinks
backlinks = vault.find_backlinks("Notes/Meeting.md")

# Volltext-Suche
results = vault.search("Projekt X")
```

---

## Tests

```bash
python -m pytest tests/ -v
```

**153 Tests** - Alle bestanden.

---

## Struktur

```
kb_framework/
├── kb/
│   ├── indexer.py              # KB Core
│   ├── obsidian/               # Obsidian Module
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

MIT License - siehe [LICENSE](LICENSE)
