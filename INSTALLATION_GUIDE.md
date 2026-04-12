# KB Framework Installation Guide

**KB Framework** - Knowledge Base Framework mit SQLite + ChromaDB Vector Search.

---

## Voraussetzungen

- Python 3.10+
- pip
- Tesseract OCR (optional, für bildbasierte PDFs)
- SQLite3

---

## Installation

### 1. Python Dependencies installieren

```bash
cd ~/projects/kb-framework
pip install -r requirements.txt
```

### 2. System Dependencies (optional)

Für PDF-Indexierung mit OCR:

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-deu tesseract-ocr-eng

# Optional: Tesseract Languages für weitere Sprachen
# tesseract-ocr-fra, tesseract-ocr-spa, etc.
```

### 3. Verzeichnisse erstellen

```bash
mkdir -p ~/.knowledge/chroma_db/
mkdir -p ~/.knowledge/backup/
mkdir -p ~/.knowledge/embeddings/cache/
```

### 4. Quick Install Script

```bash
cd ~/projects/kb-framework
bash install.sh
```

---

## Konfiguration

### Datenbank initialisieren

```bash
cd ~/projects/kb-framework
python3 -c "
from kb.indexer import BiblioIndexer
idx = BiblioIndexer('~/.knowledge/knowledge.db')
idx.close()
print('Datenbank initialisiert')
"
```

### Embeddings generieren

```bash
# Statistiken anzeigen
python3 kb/library/knowledge_base/embedding_pipeline.py --stats

# Inkrementelles Update (nur neue/geänderte Dateien)
python3 kb/library/knowledge_base/embedding_pipeline.py

# Vollständiger Reload aller Embeddings
python3 kb/library/knowledge_base/embedding_pipeline.py --reload
```

---

## Nutzung

### Python API

```python
from pathlib import Path
from kb.indexer import BiblioIndexer
from kb.library.knowledge_base.chroma_plugin import ChromaDBPlugin

# Mit ChromaDB Plugin (automatische Embeddings)
with BiblioIndexer(
    "~/.knowledge/knowledge.db",
    plugins=[ChromaDBPlugin()]
) as indexer:
    indexer.index_file(Path("projektplanung/test.md"))
    indexer.index_directory("learnings")

# Hybrid Search
from kb.library.knowledge_base.hybrid_search import hybrid_search
results = hybrid_search("MTHFR Genmutation", limit=5)
```

### CLI Nutzung

```bash
# Vollständige Indizierung
python3 kb/indexer.py ~/.knowledge/knowledge.db projektplanung learnings

# Backup erstellen
bash kb/scripts/kb_backup.sh
```

---

## Projektstruktur

```
kb-framework/
├── kb/
│   ├── indexer.py              # Haupt-Indexer (SQLite)
│   ├── config.py.template      # Konfigurations-Template
│   └── library/
│       └── knowledge_base/
│           ├── chroma_integration.py   # ChromaDB Wrapper
│           ├── chroma_plugin.py       # Plugin für Indexer
│           ├── embedding_pipeline.py   # Batch-Embedding
│           └── hybrid_search.py        # Hybrid Suche
├── docs/
│   └── CHROMA_INTEGRATION_PLAN.md
├── tests/
├── install.sh                  # Quick Install Script
└── requirements.txt
```

---

## Troubleshooting

### ChromaDB funktioniert nicht

```bash
# Prüfe ChromaDB Version
python3 -c "import chromadb; print(chromadb.__version__)"

# ChromaDB neu initialisieren
rm -rf ~/.knowledge/chroma_db/
python3 kb/library/knowledge_base/embedding_pipeline.py --reload
```

### Embeddings werden nicht generiert

1. Prüfe Queue: `indexer.plugins[0].get_queue_size()`
2. Manuell flushen: `indexer.plugins[0].flush()`
3. Logs prüfen auf Fehler

### Performance-Probleme

- Batch-Size in `ChromaDBPlugin` reduzieren (Standard: 32)
- Background-Thread nutzen: `plugin.flush_async()`

---

## Weiterführende Links

- [CHANGELOG.md](./CHANGELOG.md) - Änderungsprotokoll
- [README.md](./README.md) - Projektübersicht
- [SKILL.md](./SKILL.md) - OpenClaw Skill Dokumentation
