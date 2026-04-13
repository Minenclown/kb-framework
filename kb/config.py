# KB Framework Konfiguration
import os
from pathlib import Path

# Datenbank
DB_PATH = os.getenv("KB_DB_PATH", "library/biblio.db")  # SQLite DB
CHROMA_PATH = os.getenv("KB_CHROMA_PATH", "library/chroma_db/")  # ChromaDB Vektoren

# Bibliothek
LIBRARY_PATH = os.getenv("KB_LIBRARY_PATH", "library/")  # Wo die Dokumente liegen

# Such-Parameter
DEFAULT_LIMIT = 20
SEMANTIC_WEIGHT = 0.6
KEYWORD_WEIGHT = 0.4

# OCR (für bildbasierte PDFs)
OCR_LANGUAGES = ["de", "en"]
OCR_GPU = False  # True wenn GPU verfügbar


# Registry metadata for ClawHub and tooling
__version__ = "0.2.0"

__registry__ = {
    "name": "kb-framework",
    "version": __version__,
    "description": "Hybrid Knowledge Base with Markdown/PDF/OCR, SQLite + ChromaDB, Obsidian integration",
    "requirements": [
        "chromadb>=0.4.0",
        "sentence-transformers>=2.0.0",
        "PyMuPDF>=1.23.0",
        "easyocr>=1.7.0",
        "torch>=2.0.0",
        "numpy",
        "tqdm",
    ],
    "optional": [
        "obsidian-api",  # For Obsidian integration
    ],
    "env": {
        "KB_CHROMA_PATH": {
            "description": "Path to ChromaDB directory",
            "default": "library/chroma_db/",
            "required": False,
        },
        "KB_DB_PATH": {
            "description": "Path to SQLite database",
            "default": "library/biblio.db",
            "required": False,
        },
        "KB_LIBRARY_PATH": {
            "description": "Path to library directory",
            "default": "library/",
            "required": False,
        },
    },
    "config_paths": {
        "config": "kb/config.py",
        "db": "library/biblio.db",
        "chroma": "library/chroma_db/",
        "library": "library/",
    },
}
