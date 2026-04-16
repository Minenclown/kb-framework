# KB Framework Master Plan

**Erstellt:** 2026-04-16 18:34 UTC
**Quellen:** ANALYSIS_FULL.md (Round 1), ANALYSIS_ROUND2.md (Round 2), ANALYSIS_ARCHITECTURE.md
**Status:** DRAFT - Pending Lumen Decision

---

## Executive Summary

Drei Analysen wurden kombiniert zu einem unified Master Plan:

| Quelle | Issues | Kategorie |
|--------|--------|-----------|
| Round 1 | 13 | Kritische Fehler (Runtime) |
| Round 2 | 23 | Technische Schulden |
| Architektur | 5+的主题 | Strukturelle Verbesserungen |

**Total Unique Issues:** ~40 (mit Überschneidungen)

---

## Priorisierte Roadmap

### 🔴 P0: CRITICAL - Blocks Everything (DONE)

Siehe Round 1 - Kritische Fixes (bereits implementiert):

- [x] `kb/knowledge_base/` Package erstellt (Redirect zu `src/library/`)
- [x] `engine.py` - `_execute()` statt `execute()` + `@register_command`
- [x] `search.py` - Import Path korrigiert

### 🟠 P1: CRITICAL - Muss bald gefixt werden

**Gruppe:** Runtime-Fehler + Architektur-Breaking Changes

#### P1.1: Bare `except:` Statements beheben
| File | Zeilen | Risk |
|------|--------|------|
| `kb/scripts/migrate.py` | 18 | Silent failures |
| `kb/scripts/kb_ghost_scanner.py` | 80, 102, 133 | Silent failures |

**Template:**
```cody
# Theme: Error-Handling-Bare-Except
## Phase 1: Fix bare except statements
### Files:
- kb/scripts/kb_ghost_scanner.py:80,102,133
- kb/scripts/migrate.py:18

### Pattern:
- BEFORE: `except:`
- AFTER: `except Exception:`

### Deliverable:
- [ ] All bare `except:` → `except Exception:`
- [ ] Add logging where silent pass exists
- [ ] Verify no KeyboardInterrupt/SystemExit caught

### Timeout: 30 min
```

#### P1.2: NotImplementedError - KB Sync
| File | Zeilen | Methode |
|------|--------|---------|
| `kb/obsidian/writer.py` | 496-520 | `sync_to_vault()`, `sync_from_vault()` |

**Decision Gate:** Lumen muss entscheiden:
1. **Implementieren** → KB ↔ Vault Bidirektionale Sync
2. **Abstract Interface** → In Interface verschieben, Stub behalten
3. **Remove** → References suchen und entfernen

#### P1.3: Missing `@register_command` (BackupCommand)
| File | Klasse |
|------|--------|
| `kb/commands/backup.py` | `BackupCommand` |

**Template:**
```cody
# Theme: Command-Registry-Fixes
## Phase 1: Add missing decorators
### Files:
- kb/commands/backup.py

### Pattern:
@register_command
class BackupCommand(BaseCommand):
    ...

### Deliverable:
- [ ] Add @register_command to BackupCommand
- [ ] Verify command appears in --help

### Timeout: 5 min
```

#### P1.4: SQLite Connection Leaks
| File | Issue |
|------|-------|
| `kb/scripts/reembed_all.py` | `conn.close()` nicht im finally |
| `kb/scripts/kb_ghost_scanner.py` | `conn.close()` nicht im finally |
| `kb/scripts/sync_chroma.py` | `conn.close()` nicht im finally |

**Template:**
```cody
# Theme: SQLite-Resource-Management
## Phase 1: Add try-finally for connections
### Files:
- kb/scripts/reembed_all.py:55
- kb/scripts/kb_ghost_scanner.py:70
- kb/scripts/sync_chroma.py:114

### Pattern:
conn = sqlite3.connect(...)
try:
    # work
finally:
    conn.close()

### Deliverable:
- [ ] All scripts use try-finally for SQLite
- [ ] Verify with test_run

### Timeout: 30 min
```

---

### 🟡 P2: IMPORTANT - Tech Debt + Architecture Improvements

**Gruppe:** Medium Priority Issues + Architectural Refactoring

#### P2.1: HybridSearch Refactor (THEMEN-CLUSTER)

**Enthält Issues aus:**
- Round 1: Duplicate `embed_texts()` in sync.py
- Round 2: API-Inkonsistenzen
- Architektur: Enge Kopplung, Such-Layer Kopplung

**Decision Gate:** Lumen muss wählen:

**Option A: Interface-Extraktion (empfohlen)**
```python
class SearchProvider(Protocol):
    async def search_semantic(query: str, limit: int) -> list[SearchResult]: ...
    async def search_keyword(query: str, limit: int) -> list[SearchResult]: ...
```

**Aufwand:** ~2 Tage
**Benefit:** Ermöglicht Cluster-Analyse ohne ChromaDB

**Option B: Strategy-Pattern (einfacher)**
```python
class HybridSearch:
    def __init__(self, semantic_provider, keyword_provider): ...
```

**Aufwand:** ~1 Tag
**Benefit:** Weniger Änderung, entkoppelt杂交Suche

**Option C: Quick Fix (keine architektur-Änderung)**
- Nur die Import-Probleme fixen
- Kein Refactor der Suchlogik

**Template:**
```cody
# Theme: HybridSearch-Refactor
## Phase 1: Extract interfaces
### New File: src/library/search_providers.py
```python
from abc import ABC, abstractmethod

class SemanticSearchProvider(ABC):
    @abstractmethod
    async def search(self, query: str, limit: int) -> list[SearchResult]: ...

class KeywordSearchProvider(ABC):
    @abstractmethod
    async def search(self, query: str, limit: int) -> list[SearchResult]: ...
```

## Phase 2: Implement providers
### ChromaSemanticProvider
### SQLiteFTS5Provider (für Cluster ohne ChromaDB)

## Phase 3: Refactor HybridSearch
### Replace direct ChromaIntegration/SQLite calls with provider injection

### Deliverable:
- [ ] SearchProvider interface exists
- [ ] HybridSearch uses injected providers
- [ ] Cluster mode works without ChromaDB

### Timeout: 2 days (Option A) / 1 day (Option B)
```

#### P2.2: Engine API Unification

**Enthält Issues aus:**
- Round 1: Singleton Pattern Duplication, Config Key Mismatch
- Round 2: OllamaEngine vs TransformersEngine API differences

**Decision Gate:**

**Option A: Factory Pattern konsistent machen**
```python
# engine/factory.py erweitern
def create_engine(config: LLMConfig) -> BaseLLMEngine:
    if config.model_source == "ollama":
        return OllamaEngine.get_instance()
    elif config.model_source == "transformers":
        return TransformersEngine()  # oder auch Singleton
    ...
```

**Option B: Beide Singletons**
```python
class TransformersEngine:
    _instance = None
    def get_instance(cls): ...
```

**Template:**
```cody
# Theme: LLM-Engine-Unification
## Phase 1: Standardize interface
### BaseLLMEngine.generate() signature:
- prompt: str
- temperature: float | None = None
- max_tokens: int | None = None
- stream: bool = False

## Phase 2: Make TransformersEngine singleton
### Timeout: 4 hours
```

#### P2.3: TaskScheduler + FileWatcher Tests

**Enthält Issues aus:**
- Round 2: Ungetestete Kernkomponenten

**Template:**
```cody
# Theme: Scheduler-Watcher-Tests
## Phase 1: TaskScheduler tests
### Test cases:
- [ ] register_job() / unregister_job()
- [ ] Cron parsing: _parse_cron()
- [ ] should_run() evaluation
- [ ] Manual trigger
- [ ] Retry on failure
- [ ] State persistence

### Mock strategy:
- Mock LLMEngine
- Mock KBConnection
- Use tmp_path for scheduler DB

## Phase 2: FileWatcher tests
### Test cases:
- [ ] File event detection
- [ ] Debouncing logic
- [ ] State management

### Deliverable:
- [ ] >80% coverage on task_scheduler.py
- [ ] >80% coverage on file_watcher.py

### Timeout: 2 days
```

#### P2.4: Large Module Refactors

**Enthält Issues aus:**
- Architektur: 5 Module >500 Zeilen

| File | Lines | Refactor Into |
|------|-------|--------------|
| `report_generator.py` | 1242 | data_collector.py + prompt_builder.py + graph_generator.py |
| `task_scheduler.py` | 1222 | cron_parser.py + job_registry.py + job_executor.py |
| `hybrid_search.py` | 997 | (siehe P2.1) |
| `essence_generator.py` | 906 | template_loader.py + hotspot_scorer.py |
| `transformers_engine.py` | 1162 | (akzeptabel als engine wrapper) |

**Template:**
```cody
# Theme: Module-Size-Reduction
## Example: report_generator.py

### Phase 1: Extract data collection
New file: kb/biblio/generator/report_data_collector.py
- _collect_essences_for_period()
- _compute_hotspots()
- _save_graph_data()

### Phase 2: Extract prompt building
New file: kb/biblio/generator/report_prompt_builder.py
- _build_daily_prompt()
- _build_weekly_prompt()
- _build_monthly_prompt()

### Phase 3: Thin orchestration layer
report_generator.py wird zum facade:
- generate_report() → delegiert an andere Klassen
- ~100 Zeilen final

### Deliverable:
- [ ] report_generator.py < 150 lines
- [ ] New modules have tests
- [ ] No functionality change

### Timeout: 2-3 days per module
```

---

### ⚪ P3: NICE-TO-HAVE

#### P3.1: Redundancy Elimination
- File Hashing: Zusammenführen zu einer Utils-Funktion
- essences_path: Cache statt mehrfaches Lesen
- Query Cache: TTL hinzufügen

#### P3.2: Documentation
- Cron weekday convention dokumentieren
- Kommentare für kryptische Variablen (`chroma`, `_fts5_checked`, `hs`)
- CHROMA_PATH auflösen

#### P3.3: Common Error Handler Utility
```python
def handle_module_error(module_name: str, error: Exception, default: Any = None):
    logger.warning(f"{module_name} unavailable: {error}")
    return default
```

#### P3.4: Empty Test Directories
- `tests/llm/` aufräumen oder löschen

---

## Themen-Cluster (Grouped by Theme)

### Cluster 1: Import/Module Structure
| Source | Issue |
|--------|-------|
| Round 1 | Broken import path `kb/knowledge_base/` |
| Round 1 | `search.py` wrong import |
| Architektur | Two locations for KB code |

**Resolved:** P0 DONE

### Cluster 2: Command Registry
| Source | Issue |
|--------|-------|
| Round 1 | EngineListCommand/EngineInfoCommand wrong method name |
| Round 1 | BackupCommand missing `@register_command` |

**Resolved:** P0 DONE (engine.py fixes)
**Pending:** P1.3 (BackupCommand)

### Cluster 3: Error Handling Patterns
| Source | Issue |
|--------|-------|
| Round 2 | 12x `except Exception:` unterschiedlich |
| Round 2 | Bare `except:` in scripts |
| Architektur | Silent failures |

**Pending:** P1.1 + P3.3

### Cluster 4: Resource Management
| Source | Issue |
|--------|-------|
| Round 1 | Hardcoded paths in scripts |
| Round 2 | SQLite connection leaks |
| Round 2 | ThreadPoolExecutor nicht heruntergefahren |

**Pending:** P1.4 + P1.1 (partial)

### Cluster 5: Search/Knowledge Base
| Source | Issue |
|--------|-------|
| Round 1 | Duplicate embed_texts() in sync.py |
| Round 1 | sync.py should use EmbeddingPipeline |
| Architektur | HybridSearch tightly coupled |
| Architektur | SearchProvider interface missing |

**Pending:** P2.1

### Cluster 6: LLM Engine Architecture
| Source | Issue |
|--------|-------|
| Round 1 | Singleton pattern duplication |
| Round 1 | Config key mismatch (llm.py vs config.py) |
| Round 2 | OllamaEngine singleton, TransformersEngine not |
| Round 2 | API parameter inconsistencies |
| Architektur | Singleton vs Factory |

**Pending:** P2.2

### Cluster 7: Testing Gaps
| Source | Issue |
|--------|-------|
| Round 2 | TaskScheduler untested (1222 lines) |
| Round 2 | FileWatcher untested (733 lines) |
| Round 2 | EssenceGenerator untested |

**Pending:** P2.3

### Cluster 8: Module Size/SRP
| Source | Issue |
|--------|-------|
| Architektur | report_generator.py (1242 lines) |
| Architektur | task_scheduler.py (1222 lines) |
| Architektur | hybrid_search.py (997 lines) |
| Architektur | essence_generator.py (906 lines) |

**Pending:** P2.1 (hybrid_search) + P2.4 (rest)

### Cluster 9: KB Sync
| Source | Issue |
|--------|-------|
| Round 2 | NotImplementedError sync_to/sync_from_vault |

**Pending:** P1.2 - Decision Gate

### Cluster 10: Config/Dependency Injection
| Source | Issue |
|--------|-------|
| Round 1 | Hardcoded paths use KBConfig |
| Architektur | Singleton everywhere, no DI |
| Architektur | Config resolution on every get_instance() |

**Pending:** P2.2 (partial) + P3.1

---

## Decision Gates Summary

### DG-1: KB Sync Implementierung (P1.2)
**Question:** Wie mit `sync_to_vault()` / `sync_from_vault()` umgehen?
- [ ] **Implementieren** - Bidirektionale Sync
- [ ] **Interface** - Abstract machen, Stub behalten
- [ ] **Remove** - Referenzen finden und entfernen

### DG-2: HybridSearch Refactor Ansatz (P2.1)
**Question:** Wie Such-Layer entkoppeln?
- [ ] **Option A:** Interface-Extraktion (2 Tage, Cluster-fähig)
- [ ] **Option B:** Strategy-Pattern (1 Tag, weniger Änderung)
- [ ] **Option C:** Quick Fix nur (kein Refactor)

### DG-3: Engine Singleton (P2.2)
**Question:** Consistency für LLM Engines?
- [ ] **Option A:** Factory Pattern konsistent
- [ ] **Option B:** Beide Singletons

---

## Cody-Template Format

Jeder Theme-Cluster kann als Cody-Task ausgeführt werden:

```cody
# {THEME_NAME}
## Context
{One-paragraph summary of the problem}

## Files
{List of affected files with line numbers}

## Steps
1. {First step}
2. {Second step}
...

## Verification
{How to verify the fix works}

## Rollback
{How to undo if something breaks}

## Timeout
{Time estimate}
```

---

## Timeline Vorschlag

```
Week 1:
├── P1.1: Bare except fixes (30 min)
├── P1.3: BackupCommand decorator (5 min)
├── P1.4: SQLite resource management (30 min)
└── Decision Gate: DG-1 (KB Sync)

Week 2:
├── P2.1: HybridSearch Refactor (1-2 Tage)
├── P2.2: Engine API Unification (4 Stunden)
└── Decision Gate: DG-2 (falls nicht vorher entschieden)

Week 3:
├── P2.3: Scheduler/Watcher Tests (2 Tage)
└── DG-3: Engine Singleton (falls nötig)

Week 4:
└── P2.4: Large Module Refactors (2-3 Tage pro Modul)

Ongoing:
└── P3: Nice-to-have items (backlog)
```

---

## Dependencies Map

```
P0 ─────────────────────────────────────────────► DONE
 │
P1.1 ─► P3.3 (Common Error Handler)
 │
P1.2 ─┼─► DG-1 Decision
 │     │
 │     └► implement / interface / remove
 │
P1.3 ─► P2.3 (Commands testing)
 │
P2.1 ─► P2.4 (HybridSearch size reduction)
 │
P2.2 ─► P2.4 (Engine unification enables module refactor)
 │
P3.1 ─► kann parallel
```

---

*Master Plan erstellt von Specialista (Subagent)*
*Feedback an: Main Agent / Lumen*
