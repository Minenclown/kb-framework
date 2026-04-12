# KB Framework - Knowledge Base für OpenClaw

**Hybrid Search** mit SQLite + ChromaDB. Installiert in 2 Minuten.

---

## Quick Start

```bash
# 1. In OpenClaw workspace kopieren
cp -r kb_framework/ ~/.openclaw/workspace/

# 2. Abhängigkeiten
pip install chromadb

# 3. Fertig!
```

---

## Konfiguration

In `kb/indexer.py` anpassen:

```python
DB_PATH = "/home/user/knowledge/knowledge.db"
CHROMA_PATH = "/home/user/.knowledge/chroma_db/"
LIBRARY_PATH = "/home/user/knowledge/library/"
```

---

## Nutzung

### Python

```python
import sys
sys.path.insert(0, "/path/to/kb_framework")

from kb.indexer import BiblioIndexer
from kb.library.knowledge_base.hybrid_search import HybridSearch

# Indexieren
with BiblioIndexer("knowledge.db") as idx:
    idx.index_file("document.md")

# Suchen
hs = HybridSearch()
results = hs.search("Suchbegriff", limit=10)
```

### CLI

```bash
# Datei indexieren
python3 kb/indexer.py dokument.md

# Audit
python3 kb/scripts/kb_full_audit.py

# Ghost-Scanner
python3 kb/scripts/kb_ghost_scanner.py
```

---

## Struktur

```
kb_framework/
├── SKILL.md                    # OpenClaw Skill Doku
├── README.md                   # Diese Datei
└── kb/
    ├── indexer.py             # Core Indexer
    └── library/
        └── knowledge_base/
            ├── hybrid_search.py       # Suche
            ├── chroma_integration.py  # ChromaDB
            └── embedding_pipeline.py  # Embeddings
    └── scripts/
        ├── index_pdfs.py       # PDF + OCR
        ├── kb_ghost_scanner.py # Verwaiste Einträge
        ├── kb_full_audit.py   # Audit + Cleanup
        └── kb_warmup.py       # Model vorladen
```

---

## Datenbank

- **SQLite** für strukturierte Daten
- **ChromaDB** für semantische Suche
- Automatische Foreign Key Prüfung
- Tägliche Audit-Jobs möglich

---

## Migration Guide (0 → KB Framework)

### 1. System-Dependencies installieren
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-deu tesseract-ocr-eng
```

### 2. Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Verzeichnisse erstellen
```bash
mkdir -p ~/.knowledge/library/
mkdir -p ~/.knowledge/backup/
mkdir -p ~/.knowledge/chroma_db/
mkdir -p ~/.knowledge/embeddings/
```

### 4. Framework in OpenClaw workspace kopieren
```bash
cp -r kb_framework/ ~/.openclaw/workspace/
```

### 5. Datenbank initialisieren (Schema wird automatisch erstellt)
```bash
cd ~/.openclaw/workspace/kb_framework
python3 kb/indexer.py ~/.knowledge/library/
```

### 6. Backup erstellen (nach erster Indexierung)
```bash
bash kb/scripts/kb_backup.sh
```

### 7. Modell vorladen (optional, vermeidet 12s Cold Start)
```bash
python3 kb/scripts/kb_warmup.py
```

### 8. Restore durchführen (nach Datenverlust)
```bash
# Backup-Name herausfinden
ls ~/.knowledge/backup/

# Restore
bash kb/scripts/kb_restore.sh kb_backup_20260412_113032

# Oder vom latest Backup:
bash kb/scripts/kb_restore.sh latest
```

---

## Troubleshooting

**ChromaDB langsam?**
```bash
python3 kb/scripts/kb_warmup.py
```

**Suche findet nichts?**
```bash
python3 kb/scripts/kb_full_audit.py
```

**OCR zu langsam?**
```python
# In kb/scripts/index_pdfs.py:
GPU_ENABLED = True
```

---

MIT License
