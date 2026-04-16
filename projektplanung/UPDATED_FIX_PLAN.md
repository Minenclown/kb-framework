# KB Framework - Updated Fix Plan
**Generated:** 2026-04-16 18:59 UTC
**Based on:** MASTER_PLAN.md + Lumen Decisions (DG-1, DG-2, DG-3)
**Status:** PLANNED

---

## Entscheidungen (Lumen)

| Decision Gate | Option | Aufwand |
|---------------|--------|---------|
| DG-1: KB Sync | **Option 1** - Bidirektionaler Sync implementieren | 1-2 Tage |
| DG-2: HybridSearch | **Option A** - Interface-Extraktion für HybridSearch | 2 Tage |
| DG-3: Engines | **Option 2** - Beide Engines als Singletons | 2 Stunden |

---

## Prioritäts-Reihenfolge

```
1. P1.1: Bare except fixes (DG-1 relevant)          → ~30 min
2. P1.3: BackupCommand @register_command            → ~5 min
3. P1.4: SQLite resource management                  → ~30 min
4. P2.2: Engine Singletons (DG-3)                   → ~2 Stunden
5. P2.1: HybridSearch Interface (DG-2) - GRÖSSTES   → ~2 Tage
6. P1.2: KB Sync Implementierung (DG-1) - GRÖSSTES  → ~1-2 Tage
```

---

## Phase 1: Bare except Statements beheben
**Priorität:** 🔴 KRITISCH (P1.1)
**DG-1 relevant:** KB Sync braucht robustes Error-Handling
**Aufwand:** ~30 Min

### Kontext
Bare `except:` fangen alle Exceptions inklusive KeyboardInterrupt und SystemExit.
Dies führt zu silent failures und macht Debugging unmöglich.

### Betroffene Dateien
- `kb/scripts/migrate.py:18`
- `kb/scripts/kb_ghost_scanner.py:80, 102, 133`

### Schritte
1. `kb/scripts/migrate.py` - Zeile 18: `except:` → `except Exception:`
2. `kb/scripts/kb_ghost_scanner.py` - Zeile 80: `except:` → `except Exception:`
3. `kb/scripts/kb_ghost_scanner.py` - Zeile 102: `except:` → `except Exception:`
4. `kb/scripts/kb_ghost_scanner.py` - Zeile 133: `except:` → `except Exception:`
5. Logging hinzufügen wo `silent pass` existiert

### Verifikation
```bash
# Keine bare except mehr in kb/scripts/
rg "^\s+except:" kb/scripts/ --no-ignore
# Sollte nur "except Exception:" oder "except SpecificError:" zeigen
```

### Rollback
```bash
cd ~/projects/kb-framework && git checkout kb/scripts/migrate.py kb/scripts/kb_ghost_scanner.py
```

### Timeout
30 Minuten

---

## Phase 2: BackupCommand @register_command
**Priorität:** 🟠 MAJOR (P1.3)
**Aufwand:** ~5 Min

### Kontext
BackupCommand fehlt der `@register_command` Decorator.
Er wird daher nicht automatisch in der Command-Registry gefunden.

### Betroffene Dateien
- `kb/commands/backup.py`

### Schritte
1. Prüfe ob `@register_command` bereits vorhanden
2. Wenn nicht: `@register_command` vor der Klasse einfügen
3. Verify: `kb --help` zeigt BackupCommand

### Verifikation
```bash
kb --help | grep -i backup
```

### Rollback
```bash
# Zeile entfernen
sed -i '/^@register_command$/d' kb/commands/backup.py
```

### Timeout
5 Minuten

---

## Phase 3: SQLite Resource Management
**Priorität:** 🟠 MAJOR (P1.4)
**Aufwand:** ~30 Min

### Kontext
Mehrere Scripts schließen SQLite Connections nicht korrekt im `finally`-Block.
Dies kann zu Connection Leaks führen.

### Betroffene Dateien
- `kb/scripts/reembed_all.py:55`
- `kb/scripts/kb_ghost_scanner.py:70`
- `kb/scripts/sync_chroma.py:114`

### Schritte
1. **reembed_all.py**: `conn.close()` in `finally:` verschieben
2. **kb_ghost_scanner.py**: `conn.close()` in `finally:` verschieben
3. **sync_chroma.py**: `conn.close()` in `finally:` verschieben

### Pattern
```python
# VORHER (fehleranfällig)
conn = sqlite3.connect(db_path)
# ... work ...
conn.close()

# NACHHER (korrekt)
conn = sqlite3.connect(db_path)
try:
    # ... work ...
finally:
    conn.close()
```

### Verifikation
```bash
# Test mit aktivem Connection-Tracking
python -c "
import sqlite3
import sys
sys.path.insert(0, 'kb/scripts')
# Check if all scripts use proper finally
"
```

### Rollback
```bash
cd ~/projects/kb-framework && git checkout kb/scripts/reembed_all.py kb/scripts/kb_ghost_scanner.py kb/scripts/sync_chroma.py
```

### Timeout
30 Minuten

---

## Phase 4: Engine Singletons (DG-3 Option 2)
**Priorität:** 🟡 IMPORTANT (P2.2)
**Aufwand:** ~2 Stunden

### Kontext
OllamaEngine ist Singleton, TransformersEngine nicht.
DG-3 Entscheidung: **Beide als Singletons**.

### Betroffene Dateien
- `src/llm/transformers_engine.py`
- `src/llm/ollama_engine.py` (bereits Singleton, prüfen)
- `src/llm/engine_factory.py` (falls vorhanden)

### Schritte
1. **TransformersEngine**: Singleton Pattern implementieren
   ```python
   class TransformersEngine(BaseLLMEngine):
       _instance = None
       
       def __new__(cls):
           if cls._instance is None:
               cls._instance = super().__new__(cls)
           return cls._instance
       
       @classmethod
       def get_instance(cls):
           if cls._instance is None:
               cls._instance = cls()
           return cls._instance
   ```

2. **OllamaEngine**: Verifizieren dass Singleton korrekt
   - `_instance = None` class variable
   - `get_instance()` classmethod
   - Thread-safe initialization (optional für Phase 1)

3. **Factory anpassen** falls vorhanden:
   ```python
   def create_engine(config: LLMConfig) -> BaseLLMEngine:
       if config.model_source == "ollama":
           return OllamaEngine.get_instance()
       elif config.model_source == "transformers":
           return TransformersEngine.get_instance()
   ```

### Verifikation
```python
# Test Singleton behavior
from src.llm.transformers_engine import TransformersEngine
e1 = TransformersEngine.get_instance()
e2 = TransformersEngine.get_instance()
assert e1 is e2, "Should be same instance"
```

### Rollback
```bash
cd ~/projects/kb-framework && git checkout src/llm/transformers_engine.py
```

### Timeout
2 Stunden

---

## Phase 5: HybridSearch Interface (DG-2 Option A) - GRÖSSTES PROJEKT
**Priorität:** 🔴 KRITISCH (P2.1)
**Aufwand:** ~2 Tage

### Kontext
HybridSearch ist eng gekoppelt mit ChromaDB und SQLite FTS5.
DG-2 Entscheidung: **Interface-Extraktion** für Cluster-Analyse ohne ChromaDB.

### Ziel-Architektur
```
                    ┌─────────────────────┐
                    │   SearchProvider    │
                    │     (Protocol)      │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                                 │
    ┌─────────▼─────────┐           ┌─────────▼─────────┐
    │ SemanticSearch     │           │ KeywordSearch     │
    │   Provider         │           │   Provider        │
    │   (ABC)            │           │   (ABC)           │
    └─────────┬─────────┘           └─────────┬─────────┘
              │                                 │
     ┌────────▼────────┐              ┌────────▼────────┐
     │ChromaSemantic   │              │SQLiteFTS5       │
     │  Provider       │              │  Provider       │
     └─────────────────┘              └─────────────────┘

              ┌──────────────────────────┐
              │      HybridSearch        │
              │  (uses injected providers)│
              └──────────────────────────┘
```

### Betroffene Dateien
- `src/library/hybrid_search.py` (997 Zeilen - Target für Refactor)
- `src/library/chroma_integration.py`
- `src/library/embedding_pipeline.py`
- `src/library/search_providers.py` (NEU)

### Schritte

#### Phase 5a: Interface definieren (4 Stunden)
1. **Neue Datei: `src/library/search_providers.py`**
   ```python
   from abc import ABC, abstractmethod
   from typing import Protocol, runtime_checkable
   from dataclasses import dataclass
   
   @dataclass
   class SearchResult:
       content: str
       score: float
       metadata: dict
   
   @runtime_checkable
   class SemanticSearchProvider(Protocol):
       @abstractmethod
       async def search(self, query: str, limit: int) -> list[SearchResult]: ...
   
   @runtime_checkable
   class KeywordSearchProvider(Protocol):
       @abstractmethod
       async def search(self, query: str, limit: int) -> list[SearchResult]: ...
   ```

#### Phase 5b: ChromaDB Provider implementieren (4 Stunden)
2. **`src/library/providers/chroma_provider.py`** (NEU)
   - Implementiert `SemanticSearchProvider`
   - Wrapped ChromaIntegration

3. **`src/library/providers/fts5_provider.py`** (NEU)
   - Implementiert `KeywordSearchProvider`
   - Nutzt SQLite FTS5

#### Phase 5c: HybridSearch refaktorieren (4 Stunden)
4. **Refactor `hybrid_search.py`**:
   - Constructor mit Provider-Injection
   - `search_semantic()` delegiert an `SemanticSearchProvider`
   - `search_keyword()` delegiert an `KeywordSearchProvider`
   - Alte ChromaDB/SQLite Direct-Calls entfernen

#### Phase 5d: Cluster-Modus ohne ChromaDB (4 Stunden)
5. **Falls ChromaDB nicht verfügbar**:
   - Nur `SQLiteFTS5Provider` nutzen
   - Semantic Search via TF-IDF oder einfache Embedding-Vergleiche

### Verifikation
```bash
# Interface-Tests
python -c "
from src.library.search_providers import SearchResult, SemanticSearchProvider, KeywordSearchProvider
from src.library.providers.chroma_provider import ChromaProvider
from src.library.providers.fts5_provider import FTS5Provider

# Verify providers implement protocols
assert isinstance(chroma_provider, SemanticSearchProvider)
assert isinstance(fts5_provider, KeywordSearchProvider)
"

# Cluster mode test
python -c "
from src.library.hybrid_search import HybridSearch
# Without ChromaDB - should still work with FTS5
hs = HybridSearch(semantic_provider=None, keyword_provider=FTS5Provider())
results = await hs.search('test query', limit=10)
"
```

### Rollback
```bash
cd ~/projects/kb-framework && git checkout src/library/hybrid_search.py
# Remove new provider files if they break things
rm -f src/library/providers/chroma_provider.py src/library/providers/fts5_provider.py src/library/search_providers.py
```

### Timeout
2 Tage (8 Stunden)

---

## Phase 6: KB Sync Implementierung (DG-1 Option 1) - GRÖSSTES PROJEKT
**Priorität:** 🔴 KRITISCH (P1.2)
**Aufwand:** ~1-2 Tage

### Kontext
`sync_to_vault()` und `sync_from_vault()` in `kb/obsidian/writer.py` haben `NotImplementedError`.
DG-1 Entscheidung: **Bidirektionaler Sync implementieren**.

### Ziel
```
┌─────────────┐         ┌─────────────┐
│  KB CLI     │◄───────►│  Obsidian   │
│  (source)   │   Sync  │  Vault      │
└─────────────┘         └─────────────┘
     │                       │
     ▼                       ▼
┌─────────────┐         ┌─────────────┐
│ biblio.db   │         │ .md files   │
│ (SQLite)    │         │ (markdown)  │
└─────────────┘         └─────────────┘
```

### Betroffene Dateien
- `kb/obsidian/writer.py:496-520`
- `kb/obsidian/reader.py` (neu oder existente)
- `kb/obsidian/sync_manager.py` (NEU)

### Schritte

#### Phase 6a: Datenmodell definieren (2 Stunden)
1. **Mapping zwischen DB und Markdown**:
   ```python
   # biblio entry → frontmatter
   entry = {
       'title': '...',
       'authors': [...],
       'year': 2024,
       'tags': [...],
       'abstract': '...',
   }
   # → frontmatter in .md
   ```

2. **Sync-State-Tracking**:
   ```python
   class SyncState:
       kb_last_sync: datetime
       vault_last_sync: datetime
       conflict_resolution: str  # 'kb_wins' | 'vault_wins' | 'manual'
   ```

#### Phase 6b: Vault Reader implementieren (4 Stunden)
3. **`kb/obsidian/vault_reader.py`** (NEU)
   ```python
   class VaultReader:
       def read_entry(self, path: Path) -> KBEntry:
           """Read .md file, parse frontmatter + content"""
       
       def list_entries(self, vault_path: Path) -> list[Path]:
           """List all .md files in vault"""
       
       def get_modified_since(self, since: datetime) -> list[Path]:
           """Find entries modified since last sync"""
   ```

#### Phase 6c: Sync Manager implementieren (4 Stunden)
4. **`kb/obsidian/sync_manager.py`** (NEU)
   ```python
   class SyncManager:
       def sync_to_vault(self, entry: KBEntry, vault_path: Path):
           """Write KB entry to Obsidian vault as .md"""
       
       def sync_from_vault(self, path: Path, kb_connection) -> KBEntry:
           """Read .md from vault, upsert to KB"""
       
       def bidirectional_sync(self, vault_path: Path, strategy: SyncStrategy):
           """Full bidirectional sync with conflict resolution"""
   ```

#### Phase 6d: Error Handling & Edge Cases (2 Stunden)
5. **Exception Handling**:
   - File permission errors
   - Malformed frontmatter
   - Missing required fields
   - Circular references

6. **Conflict Resolution**:
   ```python
   class ConflictResolution(Enum):
       KB_WINS = auto()
       VAULT_WINS = auto()
       MANUAL = auto()  # Keep both, flag for user
   ```

#### Phase 6e: Integrations-Tests (2 Stunden)
7. **Test Sync**:
   - Create entry in KB → verify .md created
   - Modify .md → verify KB updated
   - Delete from KB → optionally delete .md (config)
   - Conflict detection

### Verifikation
```bash
# End-to-end test
python -c "
from kb.obsidian.sync_manager import SyncManager
sm = SyncManager()
sm.bidirectional_sync('/path/to/vault', strategy='kb_wins')

# Verify
# 1. KB entries exist in vault as .md
# 2. Vault .md entries exist in KB
# 3. No conflicts (or conflicts flagged)
"

# Dry-run mode
kb sync --dry-run --vault /path/to/vault
```

### Rollback
```bash
cd ~/projects/kb-framework && git checkout kb/obsidian/writer.py
# Remove new files if they break things
rm -f kb/obsidian/vault_reader.py kb/obsidian/sync_manager.py
```

### Timeout
1-2 Tage (6-10 Stunden)

---

## Zusammenfassung

| Phase | Priorität | Aufwand | Rollback |
|-------|-----------|---------|----------|
| 1: Bare except | 🔴 KRITISCH | 30 min | `git checkout` |
| 2: @register_command | 🟠 MAJOR | 5 min | Zeile entfernen |
| 3: SQLite resources | 🟠 MAJOR | 30 min | `git checkout` |
| 4: Engine Singletons | 🟡 IMPORTANT | 2 h | `git checkout` |
| 5: HybridSearch IF | 🔴 KRITISCH | 2 Tage | `git checkout` + rm |
| 6: KB Sync | 🔴 KRITISCH | 1-2 Tage | `git checkout` + rm |

**Total geschätzt:** ~4-5 Tage

---

## Abhängigkeiten

```
Phase 1 ──────────────────────────────────────► Phase 6 (KB Sync braucht robustes Error Handling)
Phase 2 ──────────────────────────────────────► (standalone)
Phase 3 ──────────────────────────────────────► (standalone)
Phase 4 ────────────────────► Phase 5 (Engine Singleton unnötig für Interface, aber nützlich)
Phase 5 ──────────────────────────────────────► (standalone)
Phase 6 ──────────────────────────────────────► (standalone)
```

---

*Cody Templates in: projektplanung/cody/*