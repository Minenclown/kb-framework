# Phase 3: Importe aktualisieren

## Ziel
Alle Python-Imports im gesamten Projekt anpassen.

## Alte Import-Pfade
```python
from kb.library.chroma_integration import ChromaManager
from kb.library.embedding_pipeline import EmbeddingPipeline
from kb.library.hybrid_search import HybridSearcher
```

## Neue Import-Pfade
```python
from src.library.chroma_integration import ChromaManager
from src.library.embedding_pipeline import EmbeddingPipeline
from src.library.hybrid_search import HybridSearcher
```

## Schritte

1. **Suche alle Referenzen:**
   ```bash
   grep -r "from kb.library" ~/projects/kb-framework --include="*.py" | grep -v __pycache__
   grep -r "import kb.library" ~/projects/kb-framework --include="*.py" | grep -v __pycache__
   ```

2. **Erstelle Liste aller betroffenen Dateien:**
   ```bash
   grep -rl "from kb.library\|import kb.library" \
       ~/projects/kb-framework --include="*.py" | grep -v __pycache__ > /tmp/files_to_update.txt
   ```

3. **Batch-Update mit sed:**
   ```bash
   # Ersetze "from kb.library" mit "from src.library"
   find ~/projects/kb-framework -name "*.py" -type f ! -path "*/__pycache__/*" \
       -exec sed -i 's/from kb\.library/from src.library/g' {} \;
   
   # Ersetze "import kb.library" mit "import src.library"
   find ~/projects/kb-framework -name "*.py" -type f ! -path "*/__pycache__/*" \
       -exec sed -i 's/import kb\.library/import src.library/g' {} \;
   ```

4. **Verifikation:**
   ```bash
   # Sollte KEINE Ergebnisse mehr haben
   grep -r "from kb.library" ~/projects/kb-framework --include="*.py" | grep -v __pycache__
   ```

## Mögliche Import-Varianten zu prüfen

| Variante | Beispiel |
|----------|----------|
| from kb.library.X import Y | `from kb.library.chroma_integration import ChromaManager` |
| import kb.library.X | `import kb.library.chroma_integration` |
| from kb.library import X | `from kb.library import ChromaManager` |

## Checkliste
- [ ] Alle `from kb.library` → `from src.library` geändert
- [ ] Alle `import kb.library` → `import src.library` geändert
- [ ] Keine alten Referenzen mehr vorhanden
- [ ] Python kann Module laden (Test: `python -c "from src.library.chroma_integration import ChromaManager"`)

## Verifikation komplett
```bash
# Final check
python3 -c "
from src.library.chroma_integration import ChromaManager
from src.library.embedding_pipeline import EmbeddingPipeline
from src.library.hybrid_search import HybridSearcher
print('✓ Alle Imports funktionieren')
"
```
