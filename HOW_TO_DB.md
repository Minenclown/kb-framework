# KB Database Guide

**Understanding and optimizing the Knowledge Base reference system.**

---

## Overview

The KB stores three interconnected data layers for each document:

```
Document (file)
    ├── Sections (file_sections)
    │   ├── Keywords (section_keywords)
    │   └── Embeddings (chroma_db)
    └── Metadata (files table)
```

Search quality depends on the density and accuracy of these references.

---

## CLI Commands

Alle Commands werden über `python3 -m kb <command>` aufgerufen.

### sync
Delta-Synchronisation zwischen SQLite und ChromaDB.
```bash
kb sync --stats        # Statistiken anzeigen
kb sync --dry-run      # Simulation ohne Änderungen
kb sync                # Delta-Sync ausführen
kb sync --full         # Vollständiger Re-Sync
kb sync --file-id 123  # Einzelne Datei syncen
```

### audit
Vollständiger Integritätscheck.
```bash
kb audit               # Alle Checks
kb audit -v            # Mit Details
kb audit --export-csv issues.csv
```

### ghost
Verwaiste Einträge finden.
```bash
kb ghost --scan-dirs ~/docs,~/notes
```

### search
Hybrid Search (semantic + keyword).
```bash
kb search "MTHFR mutation"                    # Hybrid Search
kb search "MTHFR" --semantic-only            # Nur Vektor-Suche
kb search "MTHFR" --keyword-only             # Nur LIKE-Suche
kb search "workflow" --limit 10              # Mehr Results
kb search "notes" --file-type md             # Nach Dateityp filtern
kb search "notes" --file-type md,pdf         # Mehrere Dateitypen
kb search "audit" --date-from 2026-01-01     # Nach Datum filtern
kb search "audit" --format full              # Detailliertes Output
kb search "query" --debug                    # Debug-Info (Scores, Sources)
```

### warmup
ChromaDB Model vorladen.
```bash
kb warmup
```

---

## Search Architecture

### Hybrid Search
Combines two search paradigms:
- **Semantic (ChromaDB)**: Vector similarity via `all-MiniLM-L6-v2` embeddings
- **Keyword (SQLite)**: LIKE-based full-text search

### Scoring Formula
```
combined_score = (semantic_score × 0.6) + (keyword_score × 0.4) × importance_boost
```

### Search Modes
| Mode | Description | Use Case |
|------|-------------|----------|
| Hybrid (default) | Combines semantic + keyword | Most queries |
| `--semantic-only` | Only ChromaDB vector search | Natural language |
| `--keyword-only` | Only SQLite LIKE search | Exact terms, fallback |

### Filtering
- `--file-type`: Filter by extension (md, pdf, txt)
- `--date-from/date-to`: Filter by file last_modified
- Wing/Room/Hall metadata (Phase 3.1)

### Output Format (CLI)
```
📄 filename:line [score] Section Header
```

Without line number:
```
📄 filename.md [score] Section Header
```

### Code Reference
- CLI Command: `kb/commands/search.py`
- Search Engine: `kb/library/knowledge_base/hybrid_search.py`
- ChromaDB Integration: `kb/library/knowledge_base/chroma_integration.py`

### Command Architecture
```
kb/
├── base/
│   └── command.py          # BaseCommand ABC
├── commands/
│   ├── __init__.py         # @register_command decorator
│   ├── sync.py             # Delta sync (ChromaDB ↔ SQLite)
│   ├── audit.py            # Integrity checks
│   ├── ghost.py            # Orphan detection
│   ├── search.py           # Hybrid search CLI
│   └── warmup.py           # ChromaDB pre-warming
└── library/knowledge_base/
    ├── hybrid_search.py    # HybridSearch class
    └── chroma_integration.py
```

---

## Data Structure

### 1. Files Table
Stores document metadata:
- `file_path`: Absolute path to source
- `file_hash`: SHA256 for change detection
- `last_indexed`: Timestamp
- `index_status`: indexed/pending/failed

### 2. File Sections
Splits documents at headers (`#`, `##`, etc.):
- `section_header`: The heading text
- `content_preview`: First 500 characters
- `content_full`: Complete section text
- `parent_section_id`: Hierarchy for nested headers
- `line_start`, `line_end`: Position in source

### 3. Section Keywords
Extracted terms for keyword search:
- Parsed from `content_preview`
- Stopwords filtered (der, die, das, und, etc.)
- Umlaut normalized (ä→ae, ö→oe, ü→ue, ß→ss)
- Cross-referenced with `keywords` table

### 4. Embeddings
Vector representations in ChromaDB:
- Model: `all-MiniLM-L6-v2` (384 dimensions)
- Generated from: `section_header` + `content_preview`
- Enables semantic similarity search

---

## Reference Quality Factors

### Good References
| Factor | Impact |
|--------|--------|
| Clear headers | Sections align with document structure |
| Dense keywords | More terms for keyword matching |
| Relevant embeddings | Better semantic search results |
| Complete metadata | Accurate file tracking |

### Poor References
| Issue | Cause | Fix |
|-------|-------|-----|
| Orphaned sections | `file_id` is NULL | Re-index file |
| Missing keywords | Content too short | Check section length |
| Stale embeddings | File changed, not re-indexed | Run `kb reindex` |
| Duplicate keywords | Same term multiple times | Check `section_keywords` table |

---

## Maintenance Commands

### Check Quality
```bash
# Full audit
python3 kb/scripts/kb_full_audit.py

# Find orphaned entries
python3 kb/scripts/kb_ghost_scanner.py

# Check specific file
python3 -c "
import sqlite3
conn = sqlite3.connect('knowledge.db')
cursor = conn.execute('SELECT COUNT(*) FROM file_sections WHERE file_id IS NULL')
print(f'Orphaned sections: {cursor.fetchone()[0]}')
conn.close()
"
```

### Rebuild References
```bash
# Re-index single file
python3 kb/indexer.py /path/to/file.md

# Re-index directory
python3 kb/indexer.py /path/to/directory/

# Re-generate embeddings (ChromaDB)
python3 kb/scripts/reembed_all.py
```

---

## Best Practices

### For Document Authors
- Use descriptive headers (`## Workflow Analysis` not `## Section 3`)
- Keep sections focused (avoid 5000+ word sections)
- Include relevant terms naturally in text
- Structure documents hierarchically

### For Developers
- Check `index_status` after bulk operations
- Run `kb_full_audit.py` weekly
- Monitor ChromaDB size growth
- Validate embeddings after model updates

### For Agents
- Query both keyword and semantic search
- Weight results by `importance_score`
- Use `content_preview` for context, `content_full` for detail
- Check parent sections for context

---

## Troubleshooting

| Symptom | Likely Cause | Solution |
|---------|--------------|----------|
| Search finds wrong results | Poor keyword extraction | Re-index with fresh extraction |
| Semantic search slow | Cold ChromaDB | Run `kb/scripts/kb_warmup.py` |
| Missing documents | Indexing failed | Check `index_status = 'failed'` |
| Outdated content | File changed, not re-indexed | Re-index changed files |

---

## Schema Details

```sql
-- Key relationships
files.id → file_sections.file_id
file_sections.id → section_keywords.section_id
file_sections.id → embeddings.section_id (via ChromaDB metadata)
```

**Foreign Keys:** Enabled (`PRAGMA foreign_keys = ON`)

**Cascading Deletes:** 
- Deleting file → deletes sections → deletes keywords
- ChromaDB entries cleaned separately (not automatic)

---

*For implementation details, see `kb/indexer.py` and `kb/library/knowledge_base/hybrid_search.py`*
