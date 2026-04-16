# KB Framework - OpenClaw Skill

**Version:** 1.1.1  
**Category:** Knowledge Base / Search  
**Requires:** Python 3.9+, SQLite, ChromaDB  

---

## What is the KB Framework?

A complete Knowledge Base with:
- **Hybrid Search** (semantic + keyword)
- **Automatic Indexing** (Markdown, PDF, OCR)
- **SQLite + ChromaDB** Integration
- **Daily Audits** for data quality
- **LLM Integration** (Ollama/Gemma4, HuggingFace Transformers) for essence generation, reports, file watching, and scheduled jobs *(Neu in 1.1.1)*
- **EngineRegistry** – Central singleton for multi-engine support *(Neu in 1.1.1)*
- **Generator Parallel Support** – primary_first, aggregate, compare *(Neu in 1.1.1)*

---

## Installation (1 Minute)

### 1. Install the Skill
```bash
# Clone or extract into your OpenClaw workspace
cp -r kb-framework ~/.openclaw/workspace/

# Or just the skill:
cp kb-framework/SKILL.md ~/.npm-global/lib/node_modules/openclaw/skills/kb/
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Initialize Database
```bash
python3 ~/.openclaw/workspace/kb-framework/kb/indexer.py --init
```

---

## Configuration

Set environment variable KB_DB_PATH or edit kb/config.py

---

## Usage

### Python API

```python
# Import
import sys
sys.path.insert(0, "/path/to/kb-framework")
from kb.indexer import BiblioIndexer

# Index a file
with BiblioIndexer("/path/to/knowledge.db") as idx:
    idx.index_file("/path/to/file.md")

# Search
from kb.library.knowledge_base.hybrid_search import HybridSearch
hs = HybridSearch()
results = hs.search("Your search term", limit=10)

# LLM Engine API (Neu in 1.1.1)
from kb.biblio import LLMConfig, EngineRegistry, create_engine

config = LLMConfig.get_instance()
print(f"Source: {config.model_source}")

# Create engine (auto mode mit HF primary + Ollama fallback)
engine = create_engine(config)

# Registry für Multi-Engine Zugriff
registry = EngineRegistry.get_instance(config)
primary, secondary = registry.get_both()

# Generator Parallel Support
from kb.biblio.generator import EssenzGenerator
generator = EssenzGenerator()
result = await generator.generate_essence(
    topic="Topic",
    parallel_strategy="primary_first"  # primary_first, aggregate, compare
)
```

### CLI (Recommended)

The built-in `kb` command provides easy access:

```bash
# Add to .bashrc for global access:
alias kb="/path/to/kb-framework/kb.sh"

# Commands:
kb index /path/to/file.md        # Index a file
kb search "machine learning"     # Search knowledge base
kb audit                         # Run full audit
kb ghost                         # Find orphaned entries
kb warmup                        # Preload ChromaDB model
kb llm status                    # LLM system status
kb llm generate essence "topic" # Generate an essence
kb llm generate report daily     # Generate a daily report
kb llm watch start               # Start file watcher
kb llm scheduler list            # List scheduled jobs
kb llm config show               # Show LLM config
kb llm engine status              # Show all engine status (Neu in 1.1.1)
kb llm engine switch huggingface # Switch to HuggingFace (Neu in 1.1.1)
kb llm engine test               # Test both engines (Neu in 1.1.1)
```

### Legacy Python Scripts

```bash
# Index a new file
python3 kb/indexer.py /path/to/file.md

# Ghost Scanner (finds orphaned DB entries)
python3 kb/scripts/kb_ghost_scanner.py

# Full Audit
python3 kb/scripts/kb_full_audit.py

# ChromaDB Warmup (at boot)
python3 kb/scripts/kb_warmup.py
```

---

## Architecture

```
kb-framework/
├── SKILL.md                    # This file
├── README.md                   # Detailed documentation
├── kb/
│   ├── indexer.py              # Core Indexer (BiblioIndexer)
│   ├── commands/               # CLI Commands: index, sync, audit, ghost, warmup, search, llm, engine
│   ├── base/                    # Core: config.py, db.py, logger.py, command.py
│   ├── biblio/                  # LLM Integration (Neu in 1.1.1)
│   │   ├── engine/              # Engine modules
│   │   │   ├── registry.py      # EngineRegistry Singleton (Neu in 1.1.1)
│   │   │   ├── factory.py       # Engine Factory (Neu in 1.1.1)
│   │   │   ├── base.py          # BaseLLMEngine Interface
│   │   │   ├── ollama_engine.py # Ollama Engine
│   │   │   └── transformers_engine.py # HuggingFace Engine (Neu in 1.1.1)
│   │   ├── generator/           # Generators: essence, report
│   │   ├── scheduler/           # Task scheduler
│   │   └── config.py           # LLMConfig Singleton
│   ├── library/
│   │   └── knowledge_base/
│   │       ├── hybrid_search.py       # Hybrid Search (semantic + keyword)
│   │       ├── chroma_integration.py  # ChromaDB Wrapper
│   │       ├── chroma_plugin.py       # ChromaDB Plugin (Collection Management)
│   │       ├── embedding_pipeline.py # Batch Embeddings
│   │       ├── reranker.py           # Search Result Reranker
│   │       ├── fts5_setup.py          # SQLite FTS5 Full-Text Search
│   │       ├── chunker.py            # Text Chunking
│   │       └── synonyms.py            # Query Expansion
│   └── obsidian/                # Obsidian Vault Integration
└── scripts/
    ├── index_pdfs.py          # PDF + OCR Indexing
    ├── kb_ghost_scanner.py    # Legacy ghost scanner
    ├── kb_full_audit.py       # Legacy audit script
    └── kb_warmup.py           # Legacy warmup script
```

---

## Database Schema

### `files` Table
| Field | Type | Description |
|------|------|-------------|
| id | TEXT | UUID |
| file_path | TEXT | Absolute path |
| file_name | TEXT | Filename |
| file_category | TEXT | Category |
| file_type | TEXT | pdf/md/txt |
| file_size | INTEGER | Bytes |
| line_count | INTEGER | Lines |
| file_hash | TEXT | SHA256 |
| last_indexed | TIMESTAMP | Last indexing |
| index_status | TEXT | indexed/pending/failed |
| source_path | TEXT | Original path |
| indexed_path | TEXT | MD extract path |
| is_indexed | INTEGER | 0/1 |

### `file_sections` Table
| Field | Type | Description |
|------|------|-------------|
| id | TEXT | UUID |
| file_id | TEXT | FK → files |
| section_header | TEXT | Heading |
| section_level | INTEGER | 1-6 |
| content_preview | TEXT | First 500 characters |
| content_full | TEXT | Full content |
| keywords | TEXT | JSON Array |
| importance_score | REAL | 0.0-1.0 |

### `keywords` Table
| Field | Type | Description |
|------|------|-------------|
| id | INTEGER | AUTOINCREMENT |
| keyword | TEXT | Word |
| weight | REAL | Frequency |

---

## Troubleshooting

### "ChromaDB slow on first start"
```bash
python3 kb/scripts/kb_warmup.py
```

### "Search finds nothing"
```bash
# Run audit
python3 kb/scripts/kb_full_audit.py

# Ghost Scanner
python3 kb/scripts/kb_ghost_scanner.py
```

### "OCR too slow"
```python
# Enable GPU in index_pdfs.py:
GPU_ENABLED = True  # Default: False
```

---

## Library Structure (IMPORTANT)

### content/ - Raw Files
All non-Markdown files:
```
library/content/
├── Gesundheit/           # PDFs, Studies
├── Medizin_Studien/      # Medical Literature
├── Bücher/              # Books, Guides
├── Sonstiges/           # Uncategorized
└── [category]/           # Custom categories possible
```

### agent/ - Markdown Files
All .md files for agents:
```
library/agent/
├── projektplanung/      # Agent plans
├── memory/              # Daily logs
├── Workflow_Referenzen/ # Reusable workflows
├── agents/             # Agent-specific docs
└── [category]/        # Custom categories possible
```

### Integrating New Files

**Rule:** `library/[content|agent]/[category]/[topic]/[file]`

Examples:
```bash
# New health PDF
library/content/Gesundheit/2026/Chelat-Therapie.pdf

# New agent plan
library/agent/projektplanung/Treechat_Upgrade.md

# New learning
library/agent/learnings/2026-04-12_Git_Workflow.md
```

---

## License

MIT License - free to use.
