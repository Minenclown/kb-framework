# KB Framework - OpenClaw Skill

**Version:** 1.0.0  
**Category:** Knowledge Base / Search  
**Requires:** Python 3.9+, SQLite, ChromaDB  

---

## Was ist das KB Framework?

Eine vollständige Knowledge Base mit:
- **Hybrid Search** (semantic + keyword)
- **Automatische Indexierung** (Markdown, PDF, OCR)
- **SQLite + ChromaDB** Integration
- **Daily Audits** für Datenqualität

---

## Installation (1 Minute)

### 1. Skill installieren
```bash
# Clone oder entpacke in dein OpenClaw workspace
cp -r kb_framework ~/.openclaw/workspace/

# Oder nur den Skill:
cp kb_framework/SKILL.md ~/.npm-global/lib/node_modules/openclaw/skills/kb/
```

### 2. Abhängigkeiten installieren
```bash
pip install chromadb sqlite3
```

### 3. Datenbank initialisieren
```bash
python3 ~/.openclaw/workspace/kb_framework/kb/indexer.py --init
```

---

## Konfiguration

### Pfade anpassen (in `kb/indexer.py`)
```python
# Zeile ~15
DB_PATH = "/home/user/knowledge/knowledge.db"
CHROMA_PATH = "/home/user/.knowledge/chroma_db/"
LIBRARY_PATH = "/home/user/knowledge/library/"
```

---

## Nutzung

### Python API

```python
# Import
import sys
sys.path.insert(0, "/path/to/kb_framework")
from kb.indexer import BiblioIndexer

# Datei indexieren
with BiblioIndexer("/path/to/knowledge.db") as idx:
    idx.index_file("/path/to/file.md")

# Suchen
from kb.library.knowledge_base.hybrid_search import HybridSearch
hs = HybridSearch()
results = hs.search("Dein Suchbegriff", limit=10)
```

### CLI

```bash
# Neue Datei indexieren
python3 kb/indexer.py /path/to/file.md

# Ghost-Scanner (findet verwaiste DB-Einträge)
python3 kb/scripts/kb_ghost_scanner.py

# Vollständiger Audit
python3 kb/scripts/kb_full_audit.py

# ChromaDB warmup (bei Boot)
python3 kb/scripts/kb_warmup.py
```

---

## Architektur

```
kb_framework/
├── SKILL.md                    # Diese Datei
├── README.md                   # Detaillierte Doku
├── kb/
│   ├── indexer.py             # Core Indexer (BiblioIndexer)
│   └── library/
│       └── knowledge_base/
│           ├── hybrid_search.py       # Hybrid Suche
│           ├── chroma_integration.py  # ChromaDB Wrapper
│           └── embedding_pipeline.py # Batch Embeddings
└── scripts/
    ├── index_pdfs.py          # PDF + OCR Indexierung
    ├── kb_ghost_scanner.py    # Ghost-Dateien finden
    ├── kb_full_audit.py       # Audit + Cleanup
    └── kb_warmup.py           # Model vorladen
```

---

## Datenbank-Schema

### `files` Tabelle
| Feld | Typ | Beschreibung |
|------|-----|--------------|
| id | TEXT | UUID |
| file_path | TEXT | Absoluter Pfad |
| file_name | TEXT | Dateiname |
| file_category | TEXT | Kategorie |
| file_type | TEXT | pdf/md/txt |
| file_size | INTEGER | Bytes |
| line_count | INTEGER | Zeilen |
| file_hash | TEXT | SHA256 |
| last_indexed | TIMESTAMP | Letzte Indexierung |
| index_status | TEXT | indexed/pending/failed |
| source_path | TEXT | Original-Pfad |
| indexed_path | TEXT | MD-Extrakt-Pfad |
| is_indexed | INTEGER | 0/1 |

### `file_sections` Tabelle
| Feld | Typ | Beschreibung |
|------|-----|--------------|
| id | TEXT | UUID |
| file_id | TEXT | FK → files |
| section_header | TEXT | Überschrift |
| section_level | INTEGER | 1-6 |
| content_preview | TEXT | Erste 500 Zeichen |
| content_full | TEXT | Voller Inhalt |
| keywords | TEXT | JSON Array |
| importance_score | REAL | 0.0-1.0 |

### `keywords` Tabelle
| Feld | Typ | Beschreibung |
|------|-----|--------------|
| id | INTEGER | AUTOINCREMENT |
| keyword | TEXT | Wort |
| weight | REAL | Häufigkeit |

---

## Troubleshooting

### "ChromaDB langsam beim ersten Start"
```bash
python3 kb/scripts/kb_warmup.py
```

### "Suche findet nichts"
```bash
# Audit starten
python3 kb/scripts/kb_full_audit.py

# Ghost-Scanner
python3 kb/scripts/kb_ghost_scanner.py
```

### "OCR zu langsam"
```python
# In index_pdfs.py GPU aktivieren:
GPU_ENABLED = True  # Standard: False
```

---

## Lizenz

MIT License - frei nutzbar.
