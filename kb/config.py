# KB Framework Konfiguration
from pathlib import Path

# Datenbank
DB_PATH = "library/biblio.db"  # SQLite DB
CHROMA_PATH = "library/chroma_db/"  # ChromaDB Vektoren (neben DB) (jetzt neben DB im library/ Verzeichnis)

# Bibliothek
LIBRARY_PATH = "library/"  # Wo die Dokumente liegen

# Such-Parameter
DEFAULT_LIMIT = 20
SEMANTIC_WEIGHT = 0.6
KEYWORD_WEIGHT = 0.4

# OCR (für bildbasierte PDFs)
OCR_LANGUAGES = ["de", "en"]
OCR_GPU = False  # True wenn GPU verfügbar
