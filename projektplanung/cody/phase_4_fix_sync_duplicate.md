# Phase 4 Fix: sync.py Duplicate embed_texts() entfernen

**Problem:** `kb/commands/sync.py` hat eine lokale `embed_texts()` Funktion die dupliziert was in `EmbeddingPipeline` aus `src.library` bereits existiert.

## Schritte

### 1. Backup erstellen
```bash
cp ~/projects/kb-framework/kb/commands/sync.py ~/projects/kb-framework/kb/commands/sync.py.bak
```

### 2. Import hinzufügen

Am Anfang der Datei (nach existing imports):
```python
from src.library.embedding_pipeline import EmbeddingPipeline
```

### 3. embed_texts() Funktion ersetzen

Die lokale Funktion:
```python
def embed_texts(texts: list, model_name: str = "all-MiniLM-L6-v2") -> List[List[float]]:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(model_name)
    embeddings = model.encode(texts)
    return embeddings.tolist()
```

Ersetzen mit Usage von EmbeddingPipeline:
```python
# embed_texts() wird nicht mehr definiert
# Stattdessen: pipeline = EmbeddingPipeline() im Methoden-Kontext
```

### 4. _cmd_full() und _cmd_incremental() refaktorieren

Suche nach Stellen wo `embed_texts()` aufgerufen wird:
```bash
grep -n "embed_texts" ~/projects/kb-framework/kb/commands/sync.py
```

Ersetze Aufrufe wie:
```python
embeddings = embed_texts(section_texts, model_name)
```

Mit:
```python
pipeline = EmbeddingPipeline(model_name=model_name)
embeddings = pipeline.embed_documents(section_texts)
```

## Verification

```bash
cd ~/projects/kb-framework

python3 -c "
from kb.commands.sync import SyncCommand
print('✓ SyncCommand imports without embed_texts duplication')

# Test die Klasse hat keine lokale embed_texts mehr
import inspect
source = inspect.getsource(SyncCommand)
if 'def embed_texts' in source:
    print('⚠ Still has local embed_texts - check refactor')
else:
    print('✓ No local embed_texts function')

# Test EmbeddingPipeline import works
from src.library.embedding_pipeline import EmbeddingPipeline
print('✓ EmbeddingPipeline import works')
"
```

## Rollback

```bash
cp ~/projects/kb-framework/kb/commands/sync.py.bak \
   ~/projects/kb-framework/kb/commands/sync.py
```

## Checkliste

- [ ] Backup erstellt
- [ ] EmbeddingPipeline Import hinzugefügt
- [ ] Lokale embed_texts() Funktion entfernt
- [ ] Alle embed_texts() Aufrufe durch pipeline.embed_documents() ersetzt
- [ ] Keine Duplicate mehr