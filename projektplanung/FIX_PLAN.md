# KB Framework Fix Plan
**Generated:** 2026-04-16 17:58 UTC  
**Based on:** ANALYSIS_FULL.md (13 problems found)  
**Status:** PLANNED

---

## Abhängigkeits-Graph

```
Phase 1 (CRITICAL - Import-Umleitung)
├── Phase 2 (CRITICAL - engine.py Fixes)
│   └── Phase 3 (MAJOR - @register_command fehlt)
│       └── Phase 4 (MAJOR - sync.py Duplicate)
│           └── Phase 5 (MAJOR - llm.py Async Bridge)
│               └── Phase 6 (MINOR - Hardcoded Paths)
│                   └── Phase 7 (DESIGN - Consistency)
```

**Kritischer Pfad:** Phase 1 → 2 → 3 → 4 → 5 → 6 → 7

---

## Phase 1: kb/knowledge_base/ Redirect erstellen
**Priorität:** 🔴 CRITICAL  
**Blockiert:** Alle Imports von `kb.knowledge_base.*`  
**Aufwand:** ~2 Min

### Ziel
Alle fehlgeschlagenen Imports auf `src/library/` umlenken.

### Betroffene Dateien
- `kb/commands/search.py:22`
- `kb/scripts/reembed_all.py:25-26`
- `kb/scripts/kb_warmup.py:13`
- `kb/scripts/migrate_fts5.py:23`
- `tests/test_kb.py:13`
- `test_parallel_imports.py:107-318`
- `src/library/__init__.py:27`

### Lösung
Erstelle `kb/knowledge_base/__init__.py` das via `sys.modules` auf `src.library` umleitet.

### Schritte
1. Erstelle Verzeichnis `kb/knowledge_base/`
2. Erstelle `kb/knowledge_base/__init__.py` mit Redirect-Logic
3. Erstelle `kb/knowledge_base/chroma_integration.py` (redirect)
4. Erstelle `kb/knowledge_base/hybrid_search.py` (redirect)
5. Erstelle `kb/knowledge_base/fts5_setup.py` (redirect)
6. Erstelle `kb/knowledge_base/embedding_pipeline.py` (redirect)

### Deliverable
```python
# kb/knowledge_base/__init__.py
import sys
from pathlib import Path

# Redirect kb.knowledge_base → src.library
_kb_path = Path(__file__).parent.parent.parent / "src" / "library"
sys.modules.append(str(_kb_path))
# Real: from src.library.chroma_integration import ...
```

### Erwartetes Ergebnis
Alle Imports `from kb.knowledge_base.X import Y` funktionieren wieder.

### Rollback
```bash
rm -rf ~/projects/kb-framework/kb/knowledge_base/
```

---

## Phase 2: engine.py Methoden und Decorator fixen
**Priorität:** 🔴 CRITICAL  
**Blockiert:** EngineListCommand und EngineInfoCommand funktionieren nicht  
**Aufwand:** ~3 Min

### Ziel
Basis-Klasse korrekt nutzen (execute → _execute, add_arguments Signatur, @register_command)

### Betroffene Dateien
- `kb/commands/engine.py`

### Probleme zu fixen
1. `execute()` → `_execute()`
2. `add_arguments(self, parser)` → `add_arguments(self, parser: argparse.ArgumentParser)`
3. `@register_command` Decorator hinzufügen
4. `args` Parameter in `_execute()` entfernen (BaseCommand._execute() hat keine args)

### Deliverable
```python
@register_command
class EngineListCommand(BaseCommand):
    name = "engine-list"
    help = "List available LLM engines"
    
    def add_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument("--verbose", "-v", action="store_true")
    
    def _execute(self) -> int:
        # ... ohne args Parameter
```

### Rollback
```bash
# Alte engine.py aus Git wiederherstellen
cd ~/projects/kb-framework && git checkout kb/commands/engine.py
```

---

## Phase 3: BackupCommand @register_command hinzufügen
**Priorität:** 🟠 MAJOR  
**Blockiert:** BackupCommand wird nicht automatisch gefunden  
**Aufwand:** ~1 Min

### Ziel
BackupCommand in der Command-Registry sichtbar machen.

### Betroffene Dateien
- `kb/commands/backup.py`

### Schritte
```python
# Vor der Klasse:
@register_command
class BackupCommand(BaseCommand):
```

### Rollback
```bash
# Zeile entfernen
sed -i '/^@register_command$/d' kb/commands/backup.py
```

---

## Phase 4: sync.py Duplicate embed_texts() entfernen
**Priorität:** 🟠 MAJOR  
**Blockiert:** Inkonsistenz, doppelter Code  
**Aufwand:** ~3 Min

### Ziel
Lokale `embed_texts()` durch `EmbeddingPipeline` aus `src.library` ersetzen.

### Betroffene Dateien
- `kb/commands/sync.py`

### Schritte
1. Import hinzufügen: `from src.library.embedding_pipeline import EmbeddingPipeline`
2. Lokale `embed_texts()` Funktion entfernen
3. `_cmd_full()` und `_cmd_incremental()` refaktorieren um `EmbeddingPipeline` zu nutzen

### Deliverable
```python
from src.library.embedding_pipeline import EmbeddingPipeline

# Statt embed_texts(texts, model) jetzt:
pipeline = EmbeddingPipeline()
embeddings = pipeline.embed_documents(texts)
```

### Rollback
```bash
cd ~/projects/kb-framework && git checkout kb/commands/sync.py
```

---

## Phase 5: llm.py Async/Sync Bridge fixen
**Priorität:** 🟠 MAJOR  
**Blockiert:** Unzuverlässiges async-Verhalten  
**Aufwand:** ~3 Min

### Betroffene Dateien
- `kb/commands/llm.py`

### Problem
`asyncio.run()` in einem laufenden Event-Loop führt zu RuntimeError.

### Lösung
```python
def _run_async(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    
    if loop and loop.is_running():
        # Use run_until_complete instead of asyncio.run
        future = asyncio.ensure_future(coro)
        return loop.run_until_complete(future)
    else:
        return asyncio.run(coro)
```

### Rollback
```bash
cd ~/projects/kb-framework && git checkout kb/commands/llm.py
```

---

## Phase 6: Hardcoded Paths in Scripts beheben
**Priorität:** 🟡 MINOR  
**Blockiert:** Nichts  
**Aufwand:** ~2 Min

### Betroffene Dateien
- `kb/scripts/reembed_all.py`
- `kb/scripts/sync_chroma.py`

### Lösung
```python
# Statt:
db_path = Path.home() / ".openclaw" / "kb" / "library" / "biblio.db"

# Nutze:
from src.base.config import KBConfig
config = KBConfig.get_instance()
db_path = config.db_path
```

### Rollback
```bash
cd ~/projects/kb-framework && git checkout kb/scripts/reembed_all.py kb/scripts/sync_chroma.py
```

---

## Phase 7: Consistency - Alle Commands mit @register_command
**Priorität:** 🟡 DESIGN  
**Blockiert:** Nichts  
**Aufwand:** ~2 Min

### Ziel
Alle BaseCommand-Subklassen haben `@register_command`.

### Zu prüfen
- `kb/commands/ghost.py`
- `kb/commands/warmup.py`
- `kb/commands/audit.py`

### Deliverable
```bash
# Test ob alle Commands registriert sind
kb --help  # Sollte alle Commands zeigen
```

### Rollback
```bash
cd ~/projects/kb-framework && git checkout kb/commands/
```

---

## Zusammenfassung

| Phase | Problem | Priorität | Aufwand | Rollback |
|-------|---------|-----------|---------|----------|
| 1 | kb/knowledge_base/ Redirect | 🔴 CRITICAL | ~2 Min | `rm -rf kb/knowledge_base/` |
| 2 | engine.py execute → _execute | 🔴 CRITICAL | ~3 Min | `git checkout` |
| 3 | BackupCommand @register_command | 🟠 MAJOR | ~1 Min | Zeile entfernen |
| 4 | sync.py Duplicate embed_texts | 🟠 MAJOR | ~3 Min | `git checkout` |
| 5 | llm.py Async Bridge | 🟠 MAJOR | ~3 Min | `git checkout` |
| 6 | Hardcoded Paths | 🟡 MINOR | ~2 Min | `git checkout` |
| 7 | Consistency Check | 🟡 DESIGN | ~2 Min | `git checkout` |

**Total:** ~16 Minuten  
**Kritisch:** 2 Phasen (12 Min)  
**Major:** 3 Phasen (7 Min)  
**Minor/Design:** 2 Phasen (4 Min)

---

## Phase 1 Detail: kb/knowledge_base/ Redirect

Die Redirect-Module müssen die originalen Klassen/Funktionen aus `src.library` importieren und exponieren.

Beispiel `kb/knowledge_base/hybrid_search.py`:
```python
"""Redirect to src.library.hybrid_search"""
import sys
from pathlib import Path

# Add src/ to path for imports
_project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_project_root))

from src.library.hybrid_search import HybridSearch, SearchResult

__all__ = ["HybridSearch", "SearchResult"]
```

---

*End of Fix Plan*