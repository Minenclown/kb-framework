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
