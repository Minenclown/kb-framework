# KB Framework — Domain-basierte Struktur für Kontextfenster-Management

> Erstellt: 2026-04-15 | Gesamt: 57 Python-Dateien, 19.806 Zeilen

---

## 1. Domain-Übersicht

| Domain | Beschreibung | Dateien | Zeilen | Prozent |
|--------|-------------|---------|--------|---------|
| **CORE** | Base, Config, DB, Logger — Fundament | 6 | 1.048 | 5,3% |
| **INDEXING** | Indexer, Chunker, Embeddings, PDF-Processing | 6 | 3.145 | 15,9% |
| **SEARCH** | Hybrid Search, FTS5, Chroma, Reranker | 8 | 2.936 | 14,8% |
| **LLM** | Engine, Generator, Watcher, Scheduler | 12 | 4.983 | 25,2% |
| **CLI** | Commands, __main__, Interface | 9 | 3.084 | 15,6% |
| **INTEGRATION** | Obsidian, Scripts, Update | 18 | 4.610 | 23,3% |

---

## 2. Datei → Domain Zuordnung

### CORE (6 Dateien, 1.048 Zeilen) 🔴 Immer laden

| Datei | Zeilen | Rolle |
|-------|--------|-------|
| `kb/base/__init__.py` | 21 | Re-Export: KBConfig, KBLogger, KBConnection, BaseCommand |
| `kb/base/config.py` | 228 | Zentrale Konfiguration, Pfade, DB-Settings |
| `kb/base/db.py` | 305 | SQLite-Verbindung, Schema-Validierung, Transaktionsmanagement |
| `kb/base/logger.py` | 189 | Strukturiertes Logging |
| `kb/base/command.py` | 285 | BaseCommand + CommandError für CLI |
| `kb/version.py` | 1 | Versionsnummer |

### INDEXING (6 Dateien, 3.145 Zeilen)

| Datei | Zeilen | Rolle |
|-------|--------|-------|
| `kb/indexer.py` | 719 | BiblioIndexer — Haupt-Indexierungspipeline |
| `kb/library/knowledge_base/chunker.py` | 421 | Text-Chunking (Sätze, Absätze, Overlap) |
| `kb/library/knowledge_base/embedding_pipeline.py` | 523 | Embedding-Erstellung, Batch-Verarbeitung |
| `kb/library/knowledge_base/chroma_integration.py` | 481 | ChromaDB High-Level API (Sync, Query) |
| `kb/library/knowledge_base/chroma_plugin.py` | 433 | ChromaDB Plugin-System, Hook-Integration |
| `kb/library/knowledge_base/utils.py` | 47 | Hilfsfunktionen (build_embedding_text) |

### SEARCH (8 Dateien, 2.936 Zeilen)

| Datei | Zeilen | Rolle |
|-------|--------|-------|
| `kb/library/knowledge_base/hybrid_search.py` | 997 | Kern: HybridSearch (Vector + FTS5 + RRF) |
| `kb/library/knowledge_base/fts5_setup.py` | 274 | FTS5 Tabellen-Erstellung und -Management |
| `kb/library/knowledge_base/reranker.py` | 281 | Cross-Encoder Reranking |
| `kb/library/knowledge_base/stopwords.py` | 289 | Stopword-Listen für FTS5 |
| `kb/library/knowledge_base/synonyms.py` | 352 | Synonym-Expansion für FTS5 |
| `kb/library/knowledge_base/__init__.py` | 143 | Re-Export der SEARCH/INDEXING Module |
| `kb/library/__init__.py` | 47 | Re-Export der Library |
| `kb/library/llm/__init__.py` | 11 | (Leer, Platzhalter) |

### LLM (12 Dateien, 4.983 Zeilen) 🔥 Heißester Domain

| Datei | Zeilen | Rolle |
|-------|--------|-------|
| `kb/llm/__init__.py` | 80 | Re-Export LLM-Öffentlichkeiten |
| `kb/llm/config.py` | 278 | LLMConfig, Modell-Settings, Provider |
| `kb/llm/content_manager.py` | 677 | DB-Verwaltung für LLM-Generierungen |
| `kb/llm/engine/__init__.py` | 15 | Re-Export Engines |
| `kb/llm/engine/base.py` | 256 | BaseLLMEngine, LLMResponse, LLMProvider |
| `kb/llm/engine/ollama_engine.py` | 455 | Ollama-Implementierung |
| `kb/llm/engine/conftest.py` | 145 | Test-Fixtures für Engine |
| `kb/llm/generator/__init__.py` | 28 | Re-Export Generatoren |
| `kb/llm/generator/essence_generator.py` | 906 | Essenz-Generierung (Zusammenfassung) |
| `kb/llm/generator/report_generator.py` | 1.242 | Report-Generierung |
| `kb/llm/watcher/__init__.py` | 19 | Re-Export Watcher |
| `kb/llm/watcher/file_watcher.py` | 716 | File-Watcher + Auto-Trigger |
| `kb/llm/scheduler/__init__.py` | 21 | Re-Export Scheduler |
| `kb/llm/scheduler/task_scheduler.py` | 1.159 | Task-Scheduler, Queue, Prioritäten |
| `kb/llm/templates/__init__.py` | 7 | (Platzhalter) |

### CLI (9 Dateien, 3.084 Zeilen)

| Datei | Zeilen | Rolle |
|-------|--------|-------|
| `kb/__init__.py` | 39 | Package-Setup |
| `kb/__main__.py` | 184 | Entry-Point, CLI-Dispatcher |
| `kb/commands/__init__.py` | 154 | Command-Registry, Lazy-Loading |
| `kb/commands/llm.py` | 867 | LLM-Commands (größte Command-Datei) |
| `kb/commands/sync.py` | 524 | Sync-Command |
| `kb/commands/audit.py` | 424 | Audit-Command |
| `kb/commands/search.py` | 269 | Search-Command |
| `kb/commands/ghost.py` | 262 | Ghost-Scanner-Command |
| `kb/commands/warmup.py` | 195 | Warmup-Command |

### INTEGRATION (18 Dateien, 4.610 Zeilen)

| Datei | Zeilen | Rolle |
|-------|--------|-------|
| `kb/obsidian/__init__.py` | 51 | Obsidian-Package |
| `kb/obsidian/indexer.py` | 439 | Obsidian Vault → KB Indexierung |
| `kb/obsidian/parser.py` | 219 | Markdown/Frontmatter Parser |
| `kb/obsidian/resolver.py` | 315 | WikiLink-Resolver |
| `kb/obsidian/vault.py` | 640 | Vault-Management |
| `kb/obsidian/writer.py` | 746 | Obsidian Markdown-Writer |
| `kb/scripts/__init__.py` | 35 | Scripts-Package |
| `kb/scripts/index_pdfs.py` | 750 | PDF-Massenindexierung |
| `kb/scripts/kb_full_audit.py` | 306 | Vollständiger DB-Audit |
| `kb/scripts/kb_ghost_scanner.py` | 206 | Ghost-Entry Scanner |
| `kb/scripts/kb_warmup.py` | 30 | Embedding-Warmup |
| `kb/scripts/migrate.py` | 128 | DB-Migration |
| `kb/scripts/migrate_fts5.py` | 248 | FTS5-Migration |
| `kb/scripts/reembed_all.py` | 153 | Re-Embedding aller Einträge |
| `kb/scripts/sanitize.py` | 202 | DB-Sanitization |
| `kb/scripts/sync_chroma.py` | 117 | ChromaDB-Sync Script |
| `kb/update.py` | 252 | Auto-Update System |

---

## 3. Dependency-Graph

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLI (Entry Point)                        │
│  __main__.py → commands/*                                        │
│  Imports: CORE, SEARCH, LLM                                      │
└──────────┬───────────────┬──────────────────┬────────────────────┘
           │               │                  │
           ▼               ▼                  ▼
    ┌──────────┐    ┌───────────┐      ┌──────────┐
    │   CORE   │◄───│   SEARCH  │      │    LLM   │
    │ (0 deps) │    │ → CORE    │      │ → CORE   │
    │          │    │           │      │ → INDEX* │
    └────┬─────┘    └─────┬─────┘      └────┬─────┘
         │                │                  │
         │    ┌───────────┘                  │
         │    ▼                              │
         │  ┌──────────┐                    │
         │  │ INDEXING  │                    │
         │  │ → CORE    │                    │
         │  │ (via      │                    │
         │  │  chroma_  │◄───────────────────┘
         │  │  plugin)  │
         │  └──────────┘
         │
         ▼
    ┌──────────────┐
    │ INTEGRATION  │
    │ Obsidian → (standalone, 0 kb imports)
    │ Scripts → INDEXING, SEARCH
    │ Update → (standalone)
    └──────────────┘
```

### Detaillierte Domain-Dependencies

```
CORE ← (keine kb-Imports, Fundament)
  ↑
  ├── INDEXING ← CORE (chroma_integration → KBConfig)
  │                (chroma_plugin → KBConfig, indexer, utils)
  │                (embedding_pipeline → KBConfig)
  │   ↑
  │   └── SEARCH ← CORE (hybrid_search → KBConfig)
  │                  (INDEXING via chroma_plugin lazy-load)
  │
  ├── LLM ← CORE (config, db, logger)
  │          ↑
  │          └── LLM-intern:
  │              config → CORE
  │              engine/ollama → config, base, CORE/logger
  │              content_manager → config, CORE/db, CORE/logger
  │              generator/* → config, engine, content_manager, CORE/logger
  │              watcher → config, CORE/config, CORE/logger
  │                        → generator (lazy, für Auto-Trigger!)
  │              scheduler → config, CORE/config, CORE/logger
  │                        → watcher (lazy)
  │
  ├── CLI ← CORE (base/command, base/db, base/logger)
  │         ← SEARCH (commands/search → hybrid_search)
  │         ← LLM (commands/llm → lazy-imports aller LLM-Submodule)
  │
  └── INTEGRATION
      Obsidian → (keine kb-Imports! Vollständig standalone)
      Scripts → INDEXING (chroma_integration, embedding_pipeline)
             → CORE (via INDEXING-Imports)
      Update → (keine kb-Imports, standalone)
```

### Zyklen-Erkennung ⚠️

**Keine direkten Zyklen** zwischen Domains. Aber:

1. **LLM Watcher ↔ Generator (lazy):** `file_watcher.py` importiert `EssenzGenerator` lazy (Zeile 593). Kein harter Zyklus, aber eine Rückreferenz.

2. **INDEXING chroma_plugin → indexer:** `chroma_plugin.py` importiert `BiblioIndexer` lazy (Zeile 10). INDEXING referenziert seinen eigenen Indexer — interner Kreis, kein Domain-Zyklus.

3. **SEARCH ↔ INDEXING:** `chroma_plugin.py` importiert `ChromaIntegration` lazy. INDEXING und SEARCH sind eng gekoppelt, aber kein Zyklus — SEARCH importiert INDEXING (nicht umgekehrt, abgesehen vom gemeinsamen `__init__.py`).

---

## 4. Hot-File Analyse

### 🔥 Häufig geändert (Top 10, nach Git-Commits)

| Datei | Commits | Domain | Zeilen |
|-------|---------|--------|--------|
| `chroma_integration.py` | 7 | INDEXING | 481 |
| `config.py` | 6 | CORE | 228 |
| `hybrid_search.py` | 5 | SEARCH | 997 |
| `embedding_pipeline.py` | 5 | INDEXING | 523 |
| `chroma_plugin.py` | 5 | INDEXING | 433 |
| `indexer.py` | 5 | INDEXING | 719 |
| `reembed_all.py` | 4 | INTEGRATION | 153 |
| `kb_warmup.py` | 4 | INTEGRATION | 30 |
| `kb_full_audit.py` | 4 | INTEGRATION | 306 |
| `version.py` | 3 | CORE | 1 |

### 🧊 Selten geändert (stabil)

| Datei | Commits | Domain | Zeilen |
|-------|---------|--------|--------|
| `base/db.py` | 0* | CORE | 305 |
| `base/logger.py` | 0* | CORE | 189 |
| `base/command.py` | 0* | CORE | 285 |
| `chunker.py` | 0* | INDEXING | 421 |
| `stopwords.py` | 0* | SEARCH | 289 |
| `synonyms.py` | 0* | SEARCH | 352 |
| `fts5_setup.py` | 0* | SEARCH | 274 |
| `utils.py` | 0* | SEARCH | 47 |
| `obsidian/*` | 1-2 | INTEGRATION | - |
| `reranker.py` | 0* | SEARCH | 281 |

*\*0 Commits = nicht einzeln in Git-Historie, kam mit Bulk-Commits rein*

### LLM-Dateien 🔥🔥

Die gesamte LLM-Domain kam in einem Feature-Branch (v1.1.0) und hatte noch keine Einzel-Commits. Erwartbar: **hohes Änderungsrisiko**, da:
- `task_scheduler.py` (1.159 Zeilen) — komplexeste Datei
- `report_generator.py` (1.242 Zeilen) — größte Datei
- `essence_generator.py` (906 Zeilen) — Kern-Feature
- `content_manager.py` (677 Zeilen) — DB-Integration

---

## 5. Kontextfenster-Optimierung

### Problem

19.806 Zeilen Python-Code können nicht gleichzeitig ins Kontextfenster. Agent muss selektiv laden.

### Empfohlene Ladestrategie

#### Stufe 1: Immer laden (CORE) — ~1.048 Zeilen

```
kb/base/config.py     → 228 Zeilen (Pfade, Einstellungen)
kb/base/db.py         → 305 Zeilen (DB-Schema verstehen)
kb/base/logger.py     → 189 Zeilen (Logging-API)
kb/base/command.py    → 285 Zeilen (CLI-Interface)
kb/version.py         →   1 Zeile
```

**Warum:** Jede andere Domain importiert CORE. Ohne CORE-Verständnis kann kein Agent den Code verstehen.

#### Stufe 2: Task-abhängig laden

| Task | Domains laden | Zeilen | Dateien |
|------|---------------|--------|---------|
| **Suche/Query** | CORE + SEARCH | ~3.984 | 14 |
| **Indexierung** | CORE + INDEXING | ~4.193 | 12 |
| **LLM-Feature** | CORE + LLM | ~6.031 | 18 |
| **CLI-Befehl** | CORE + CLI | ~4.132 | 15 |
| **Obsidian** | CORE + INTEGRATION (Obsidian) | ~3.838 | 11 |
| **Vollständiges LLM** | CORE + LLM + SEARCH | ~8.967 | 26 |
| **Alles** | Alle | ~19.806 | 57 |

#### Stufe 3: Never load (außer bei Bedarf)

| Datei | Zeilen | Warum skippen |
|-------|--------|---------------|
| `scripts/migrate.py` | 128 | Einmalig, abgeschlossen |
| `scripts/migrate_fts5.py` | 248 | Einmalig, abgeschlossen |
| `scripts/sanitize.py` | 202 | Admin-Tool |
| `scripts/sync_chroma.py` | 117 | Admin-Tool |
| `llm/engine/conftest.py` | 145 | Nur für Tests |
| `llm/templates/__init__.py` | 7 | Leer |

### Domain-Prioritäten für Agent-Kontext

```
Priorität 1 (IMMER):     CORE                    ~1.048 Zeilen
Priorität 2 (BEI BEDARF): SEARCH / INDEXING / LLM ~2.900-5.000 Zeilen
Priorität 3 (SELDOM):    CLI / INTEGRATION        ~3.000-4.600 Zeilen
Priorität 4 (NIE):        scripts/migrate*        ~376 Zeilen
```

### Empfohlene Chunk-Größen pro Domain

| Domain | Optimaler Chunk | Begründung |
|--------|----------------|------------|
| CORE | **1 Chunk (alle Dateien)** | Klein, eng gekoppelt, immer benötigt |
| INDEXING | **2 Chunks**: (indexer + chunker) / (embedding + chroma) | Zwei Sub-Flows: Text-Verarbeitung vs. Embedding |
| SEARCH | **2 Chunks**: (hybrid_search + fts5) / (reranker + stopwords + synonyms) | Kern-Suche vs. NLP-Erweiterungen |
| LLM | **4 Chunks**: config+engine / generator / watcher / scheduler | 4 eigenständige Subsysteme |
| CLI | **2 Chunks**: (__main__ + registry) / commands/* | Dispatcher vs. Implementierungen |
| INTEGRATION | **3 Chunks**: obsidian / scripts-active / scripts-archived | Isolierte Systeme |

---

## 6. Empfehlungen für Agent-Kontext-Management

### 6.1 Domain-Awareness in Prompts

Wenn ein Agent an KB arbeitet, sollte er immer angeben:
- **Welche Domain** er gerade bearbeitet (z.B. "Arbeite an LLM/Scheduler")
- **Welche anderen Domains** er sehen muss (Dependencies)

### 6.2 Lazy-Loading Strategie

```
1. Lade CORE (immer)
2. Lade Ziel-Domain
3. Lade Dependency-Domains nur bei Bedarf
4. Lade niemals INTEGRATION/scripts, außer für Migrations-Aufgaben
```

### 6.3 Kontextfenster-Budget (Beispiel: 128K Token)

| Schicht | Zeilen | ~Tokens | % Budget |
|---------|--------|---------|----------|
| CORE | 1.048 | ~3.000 | 2,3% |
| Ziel-Domain (z.B. LLM) | 4.983 | ~15.000 | 11,7% |
| Dependency (z.B. SEARCH) | 2.936 | ~9.000 | 7,0% |
| **Verfügbar für Chat/Task** | — | ~100.000 | 78% |
| **Puffer** | — | — | 1% |

✅ Selbst bei "Voll-LLM + SEARCH + CORE" bleiben >75% des Kontextfensters frei.

### 6.4 Kritische Erkenntnisse

1. **Obsidian ist vollständig entkoppelt** — 0 kb-Imports! Kann als separates Projekt behandelt werden.

2. **LLM ist die komplexeste Domain** — 4 Subsysteme mit internen lazy Zyklen. Bei LLM-Arbeit: `llm/config.py` + `engine/base.py` laden, dann je nach Task Generator/Watcher/Scheduler.

3. **SEARCH und INDEXING sind eng gekoppelt** — `chroma_plugin` bridge zwischen beiden. Bei Search-Arbeit oft auch INDEXING-Verständnis nötig.

4. **CLI-Commands sind thin Wrapper** — `commands/llm.py` (867 Zeilen) ist die Ausnahme. Andere Commands delegieren an Library-Code.

5. **Größte Einzelrisiken:**
   - `task_scheduler.py` (1.159 Zeilen) — komplexeste Logik
   - `report_generator.py` (1.242 Zeilen) — größte Datei
   - `hybrid_search.py` (997 Zeilen) — komplexer Algorithmus

### 6.5 Vorgeschlagene .context-Datei

Für Agent-Kontext-Management empfiehlt sich eine `.context`-Datei im Projekt-Root:

```yaml
# .context — Domain-aware context loading for AI agents
domains:
  core:
    always_load: true
    files: [kb/base/*.py, kb/version.py]
    
  indexing:
    load_when: ["indexing", "embedding", "chromadb", "chunking"]
    files: [kb/indexer.py, kb/library/knowledge_base/chunker.py, ...]
    deps: [core]
    
  search:
    load_when: ["search", "query", "fts5", "rerank"]
    files: [kb/library/knowledge_base/hybrid_search.py, ...]
    deps: [core, indexing]
    
  llm:
    load_when: ["llm", "generation", "essence", "report", "watcher", "scheduler"]
    chunks:
      config_engine: [kb/llm/config.py, kb/llm/engine/*]
      generator: [kb/llm/generator/*]
      watcher: [kb/llm/watcher/*]
      scheduler: [kb/llm/scheduler/*]
    deps: [core]
    
  cli:
    load_when: ["cli", "command", "interface"]
    files: [kb/__main__.py, kb/commands/*]
    deps: [core]
    
  integration:
    load_when: ["obsidian", "migration", "scripts"]
    chunks:
      obsidian: [kb/obsidian/*]
      scripts: [kb/scripts/*]
      update: [kb/update.py]
    deps: [core]
```

---

## 7. Datei-Übersicht (Alphabetisch, mit Domain-Tag)

| Datei | Zeilen | Domain | Hot? |
|-------|--------|--------|------|
| `kb/__init__.py` | 39 | CLI | |
| `kb/__main__.py` | 184 | CLI | 🟡 |
| `kb/base/__init__.py` | 21 | CORE | |
| `kb/base/command.py` | 285 | CORE | 🧊 |
| `kb/base/config.py` | 228 | CORE | 🔥 |
| `kb/base/db.py` | 305 | CORE | 🧊 |
| `kb/base/logger.py` | 189 | CORE | 🧊 |
| `kb/commands/__init__.py` | 154 | CLI | |
| `kb/commands/audit.py` | 424 | CLI | |
| `kb/commands/ghost.py` | 262 | CLI | |
| `kb/commands/llm.py` | 867 | CLI | 🔥 |
| `kb/commands/search.py` | 269 | CLI | |
| `kb/commands/sync.py` | 524 | CLI | |
| `kb/commands/warmup.py` | 195 | CLI | |
| `kb/indexer.py` | 719 | INDEXING | 🔥 |
| `kb/library/__init__.py` | 47 | SEARCH | |
| `kb/library/knowledge_base/__init__.py` | 143 | SEARCH | |
| `kb/library/knowledge_base/chroma_integration.py` | 481 | INDEXING | 🔥🔥 |
| `kb/library/knowledge_base/chroma_plugin.py` | 433 | INDEXING | 🔥 |
| `kb/library/knowledge_base/chunker.py` | 421 | INDEXING | 🧊 |
| `kb/library/knowledge_base/embedding_pipeline.py` | 523 | INDEXING | 🔥 |
| `kb/library/knowledge_base/fts5_setup.py` | 274 | SEARCH | 🧊 |
| `kb/library/knowledge_base/hybrid_search.py` | 997 | SEARCH | 🔥 |
| `kb/library/knowledge_base/reranker.py` | 281 | SEARCH | 🧊 |
| `kb/library/knowledge_base/stopwords.py` | 289 | SEARCH | 🧊 |
| `kb/library/knowledge_base/synonyms.py` | 352 | SEARCH | 🧊 |
| `kb/library/knowledge_base/utils.py` | 47 | SEARCH | 🧊 |
| `kb/library/llm/__init__.py` | 11 | SEARCH | |
| `kb/llm/__init__.py` | 80 | LLM | |
| `kb/llm/config.py` | 278 | LLM | |
| `kb/llm/content_manager.py` | 677 | LLM | |
| `kb/llm/engine/__init__.py` | 15 | LLM | |
| `kb/llm/engine/base.py` | 256 | LLM | |
| `kb/llm/engine/conftest.py` | 145 | LLM | |
| `kb/llm/engine/ollama_engine.py` | 455 | LLM | |
| `kb/llm/generator/__init__.py` | 28 | LLM | |
| `kb/llm/generator/essence_generator.py` | 906 | LLM | 🔥 |
| `kb/llm/generator/report_generator.py` | 1.242 | LLM | 🔥 |
| `kb/llm/scheduler/__init__.py` | 21 | LLM | |
| `kb/llm/scheduler/task_scheduler.py` | 1.159 | LLM | 🔥 |
| `kb/llm/templates/__init__.py` | 7 | LLM | |
| `kb/llm/watcher/__init__.py` | 19 | LLM | |
| `kb/llm/watcher/file_watcher.py` | 716 | LLM | |
| `kb/obsidian/__init__.py` | 51 | INTEGRATION | |
| `kb/obsidian/indexer.py` | 439 | INTEGRATION | |
| `kb/obsidian/parser.py` | 219 | INTEGRATION | 🧊 |
| `kb/obsidian/resolver.py` | 315 | INTEGRATION | |
| `kb/obsidian/vault.py` | 640 | INTEGRATION | |
| `kb/obsidian/writer.py` | 746 | INTEGRATION | |
| `kb/scripts/__init__.py` | 35 | INTEGRATION | |
| `kb/scripts/index_pdfs.py` | 750 | INTEGRATION | |
| `kb/scripts/kb_full_audit.py` | 306 | INTEGRATION | |
| `kb/scripts/kb_ghost_scanner.py` | 206 | INTEGRATION | |
| `kb/scripts/kb_warmup.py` | 30 | INTEGRATION | |
| `kb/scripts/migrate.py` | 128 | INTEGRATION | 🗄️ |
| `kb/scripts/migrate_fts5.py` | 248 | INTEGRATION | 🗄️ |
| `kb/scripts/reembed_all.py` | 153 | INTEGRATION | |
| `kb/scripts/sanitize.py` | 202 | INTEGRATION | |
| `kb/scripts/sync_chroma.py` | 117 | INTEGRATION | |
| `kb/update.py` | 252 | INTEGRATION | |
| `kb/version.py` | 1 | CORE | |

---

*Ende der Analyse — DOMAIN_STRUCTURE.md v1.0*