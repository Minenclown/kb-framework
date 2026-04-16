# 🔍 KB-Framework — Umfassender Audit-Plan

**Erstellt:** 2026-04-15  
**Scope:** Alle Python-Dateien in `kb/`, `tests/`, `scripts/`  
**Gesamt:** 75 Python-Dateien, ~24.700 Zeilen  
**Bekannte Vorfunde:** Import-Deadlock (ANALYSIS_DEADLOCK_DETAILED.md), sync sqlite3 in async Context

---

## 1. Priorisierungsmatrix

Dateien werden nach **Risiko × Aufwand** priorisiert. Kriterien:
- **Risiko:** Bekannte Bugs, externe Inputs, kritische Pfade, Sicherheitsrelevanz
- **Komplexität:** LOC, Funktionstiefe, Abhängigkeitsgrad
- **Tier-1:** Core + LLM (höchstes Risiko, bekannter Deadlock)  
- **Tier-2:** Search + Indexing (Daten-Pfade, SQL-Injection-Risiko)  
- **Tier-3:** CLI + Integration (Commands, Obsidian)  
- **Tier-4:** Scripts + Tests (Utility-Code, niedrigstes Risiko)

---

## 2. Tier-1: Core + LLM 🔴 Critical

### `kb/base/config.py` — 228 Zeilen, 21 Functions/Classes

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| Thread-Safety von `KBConfig.get_instance()` Double-Checked Locking | B-Arch | 🔴 | Manuell | 30min |
| Module-Level Side Effects (Singleton-Initialisierung bei Import) | B-Arch | 🔴 | Manuell | 20min |
| `threading.Lock` Usage — Deadlock-Potential mit anderen Locks | A-Code | 🔴 | Manuell | 25min |
| Hardcoded Pfade / Default-Werte | E-Sec | 🟠 | Semi-automatisch (grep) | 10min |
| Unbenutzte Config-Keys | C-Dead | 🟡 | Automatisch (AST) | 15min |

**Geschätzte Zeit:** 1h 40min

### `kb/base/db.py` — 305 Zeilen, 27 Functions/Classes

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| SQL Injection via `execute(f"PRAGMA {pragma}={value}")` (Zeile 92) | E-Sec | 🔴 | Manuell | 15min |
| Fehlender Lock auf `KBConnection` — nicht Thread-Safe | B-Arch | 🟠 | Manuell | 20min |
| Context Manager-Leck: `__exit__` bei Exception | A-Code | 🟠 | Manuell | 15min |
| Schema-Validierung: Vollständigkeit & Edge Cases | A-Code | 🟡 | Manuell | 20min |
| Connection-Pool vs. Einzel-Connection | D-Perf | 🟡 | Manuell | 15min |

**Geschätzte Zeit:** 1h 25min

### `kb/base/logger.py` — 189 Zeilen, 9 Functions/Classes

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| `_lock` + `_cache_lock` — Lock-Ordering vs. KBConfig._lock | B-Arch | 🟠 | Manuell | 15min |
| Logger-Cache Memory Leak (unbounded dict?) | D-Perf | 🟡 | Manuell | 10min |
| Unbenutzte Methoden | C-Dead | 🟢 | Automatisch (AST) | 5min |

**Geschätzte Zeit:** 30min

### `kb/base/command.py` — 285 Zeilen, 25 Functions/Classes

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| Error-Handling in `_execute()` — werden alle Exceptions gefangen? | A-Code | 🟠 | Manuell | 15min |
| DRY: `get_config()`/`get_logger()`/`get_connection()` in jeder Command | A-Code | 🟡 | Semi-automatisch | 10min |
| BaseCommand als ABC — abstrakte Methoden vollständig? | B-Arch | 🟡 | Automatisch | 5min |

**Geschätzte Zeit:** 30min

### `kb/llm/config.py` — 278 Zeilen, 27 Functions/Classes

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| `LLMConfig._lock` — Double-Checked Locking Race (wie KBConfig) | B-Arch | 🔴 | Manuell | 20min |
| Hardcoded API-Endpunkte / Modellnamen | E-Sec | 🟠 | Semi-automatisch (grep) | 10min |
| Config-Validation: Fehlende Felder → Runtime-Crash | A-Code | 🟠 | Manuell | 15min |
| `get_llm_config()` — Globale State-Mutation | B-Arch | 🟡 | Manuell | 10min |

**Geschätzte Zeit:** 55min

### `kb/llm/scheduler/task_scheduler.py` — 1.159 Zeilen, 38 Functions/Classes 🔥

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| **10× direkte `sqlite3.connect()` in async-Methoden** — Blockiert Event Loop | D-Perf | 🔴 | Semi-automatisch | 30min |
| Race Conditions in async Job-Queue | A-Code | 🔴 | Manuell | 40min |
| Signal-Handling (`_handle_signal`) — Graceful Shutdown | A-Code | 🟠 | Manuell | 20min |
| Funktionstiefe > 50 LOC (mehrere Methoden prüfen) | A-Code | 🟠 | Automatisch (lizard) | 15min |
| Unbenutzte Job-Types / Dead Code in Scheduler | C-Dead | 🟡 | Automatisch (AST) | 15min |
| Fehlende Error-Recovery bei DB-Fehlern | A-Code | 🟠 | Manuell | 20min |
| Cyclomatic Complexity pro Methode > 15 | A-Code | 🟡 | Automatisch (lizard) | 10min |

**Geschätzte Zeit:** 2h 30min

### `kb/llm/engine/ollama_engine.py` — 455 Zeilen, 18 Functions/Classes

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| `OllamaEngine._lock` — Lock-Ordering mit `KBConfig._lock` | B-Arch | 🟠 | Manuell | 15min |
| `urllib.request` ohne Timeout-Konfiguration (Zeile 153) | D-Perf | 🟠 | Manuell | 10min |
| Fehlende Retry-Logic bei HTTP 429/503 | A-Code | 🟠 | Manuell | 15min |
| Streaming: `response.read()` — Unbounded Memory | D-Perf | 🟡 | Manuell | 10min |
| Error-Klassenhierarchie (`OllamaEngineError`, `OllamaConnectionError`) | B-Arch | 🟢 | Manuell | 5min |

**Geschätzte Zeit:** 55min

### `kb/llm/content_manager.py` — 677 Zeilen, 20 Functions/Classes

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| DB-Zugriff über `KBConnection` vs. direkte `sqlite3` | B-Arch | 🟠 | Manuell | 15min |
| YAML-Parsing ohne `safe_load` (PyYAML Deserialization) | E-Sec | 🔴 | Semi-automatisch | 10min |
| Lange Methoden > 50 LOC | A-Code | 🟡 | Automatisch | 10min |
| Fehlende Transaktions-Isolation bei Concurrent Writes | A-Code | 🟠 | Manuell | 20min |

**Geschätzte Zeit:** 55min

### `kb/llm/generator/report_generator.py` — 1.242 Zeilen, 25 Functions/Classes 🔥

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| Größte Datei im Projekt — Architectural Review nötig | B-Arch | 🟠 | Manuell | 30min |
| Funktionen > 100 LOC (muss aufgespalten werden?) | A-Code | 🟠 | Automatisch (lizard) | 15min |
| DRY: Gemeinsame Patterns mit `essence_generator.py` | A-Code | 🟡 | Semi-automatisch | 20min |
| Unbenutzte Report-Typen | C-Dead | 🟡 | Automatisch | 10min |
| Template-Strings — Injection über User-Content? | E-Sec | 🟡 | Manuell | 15min |

**Geschätzte Zeit:** 1h 30min

### `kb/llm/generator/essence_generator.py` — 906 Zeilen, 19 Functions/Classes

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| DRY mit `report_generator.py` (ähnliche Retry/Prompt-Logik) | A-Code | 🟠 | Semi-automatisch | 20min |
| `_generate_with_retry` — Endlosschleife bei permanentem Fehler? | A-Code | 🔴 | Manuell | 15min |
| `_compute_hotspot_score` — Algorithmen-Komplexität | D-Perf | 🟡 | Manuell | 15min |
| Unbenutzte Score-Funktionen | C-Dead | 🟡 | Automatisch | 10min |

**Geschätzte Zeit:** 1h

### `kb/llm/watcher/file_watcher.py` — 716 Zeilen, 34 Functions/Classes

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| **11× direkte `sqlite3.connect()` in async-Methoden** — Blockiert Event Loop | D-Perf | 🔴 | Semi-automatisch | 25min |
| File-Hashing: `hashlib` bei großen Dateien — Memory | D-Perf | 🟡 | Manuell | 10min |
| Watcher-Loop: fehlende Backpressure bei Events | A-Code | 🟠 | Manuell | 20min |
| DRY: Wiederholte `sqlite3.connect` Pattern | A-Code | 🟡 | Semi-automatisch | 15min |

**Geschätzte Zeit:** 1h 10min

**Tier-1 Gesamt:** ~11h 40min

---

## 3. Tier-2: Search + Indexing 🟠 High

### `kb/library/knowledge_base/hybrid_search.py` — 997 Zeilen, 27 Functions/Classes

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| Direkte `sqlite3.connect()` — umgeht `KBConnection` | B-Arch | 🟠 | Manuell | 15min |
| FTS5-Query-Konstruktion — SQL Injection über Suchterme? | E-Sec | 🔴 | Manuell | 25min |
| RRF-Scoring: numerische Stabilität (Division durch 0?) | A-Code | 🟠 | Manuell | 15min |
| Größte Search-Datei — Architectural Review | B-Arch | 🟡 | Manuell | 20min |
| Cyclomatic Complexity in `search()` | A-Code | 🟡 | Automatisch | 10min |

**Geschätzte Zeit:** 1h 25min

### `kb/library/knowledge_base/chroma_integration.py` — 481 Zeilen, 26 Functions/Classes

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| Module-Level `KBConfig.get_instance()` — Import-Deadlock | B-Arch | 🔴 | Manuell | 15min |
| ChromaDB `Settings` — hardcoded Pfade | E-Sec | 🟡 | Semi-automatisch | 10min |
| Error-Handling bei ChromaDB-Verbindungsverlust | A-Code | 🟠 | Manuell | 15min |
| `@contextmanager` — Exception-Safety | A-Code | 🟡 | Manuell | 10min |

**Geschätzte Zeit:** 50min

### `kb/library/knowledge_base/chroma_plugin.py` — 433 Zeilen, 15 Functions/Classes

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| Module-Level `KBConfig.get_instance()` — Import-Deadlock | B-Arch | 🔴 | Manuell | 10min |
| `self._lock` — Lock-Ordering mit `KBConfig._lock` | B-Arch | 🟠 | Manuell | 15min |
| `Queue`-Pattern — Deadlock bei vollem Queue? | A-Code | 🟠 | Manuell | 15min |
| 3× direkte `sqlite3.connect()` umgeht `KBConnection` | B-Arch | 🟡 | Semi-automatisch | 10min |
| Thread-Safety des Plugin-Hook-Systems | B-Arch | 🟠 | Manuell | 15min |

**Geschätzte Zeit:** 1h 05min

### `kb/library/knowledge_base/embedding_pipeline.py` — 523 Zeilen, 17 Functions/Classes

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| Module-Level `KBConfig.get_instance()` — Import-Deadlock | B-Arch | 🔴 | Manuell | 10min |
| `ThreadPoolExecutor` — fehlende `shutdown()` | D-Perf | 🟠 | Manuell | 10min |
| 2× direkte `sqlite3.connect()` — umgeht `KBConnection` | B-Arch | 🟡 | Semi-automatisch | 10min |
| Batch-Processing: unbounded list in Memory | D-Perf | 🟡 | Manuell | 10min |

**Geschätzte Zeit:** 40min

### `kb/indexer.py` — 719 Zeilen, 28 Functions/Classes

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| Direkte `sqlite3.connect()` auf `self.conn` — kein `KBConnection` | B-Arch | 🟠 | Manuell | 15min |
| `readlines()` bei großen Dateien — Memory | D-Perf | 🟠 | Manuell | 10min |
| Fehlende Exception-Behandlung bei Datei-I/O | A-Code | 🟡 | Manuell | 15min |
| ABC-Implementation: `MarkdownIndexer`, `BiblioIndexer` | B-Arch | 🟡 | Manuell | 10min |
| Unbenutzte Methoden | C-Dead | 🟡 | Automatisch | 10min |

**Geschätzte Zeit:** 1h

### `kb/library/knowledge_base/chunker.py` — 421 Zeilen, 14 Functions/Classes

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| Edge Cases: Leerer Text, sehr kurze Chunks | A-Code | 🟡 | Manuell | 15min |
| Overlap-Berechnung: Off-by-One | A-Code | 🟡 | Manuell | 10min |
| Performance bei sehr langen Dokumenten | D-Perf | 🟢 | Manuell | 10min |

**Geschätzte Zeit:** 35min

### `kb/library/knowledge_base/fts5_setup.py` — 274 Zeilen, 4 Functions/Classes

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| Direkte `sqlite3.connect()` | B-Arch | 🟡 | Semi-automatisch | 5min |
| FTS5-Tokenizer-Konfiguration — korrekt? | A-Code | 🟡 | Manuell | 15min |
| Migrations-Idempotenz | A-Code | 🟡 | Manuell | 10min |

**Geschätzte Zeit:** 30min

### `kb/library/knowledge_base/reranker.py` — 281 Zeilen, 9 Functions/Classes

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| Cross-Encoder Model Loading — Memory | D-Perf | 🟡 | Manuell | 10min |
| Fallback bei fehlendem Model | A-Code | 🟠 | Manuell | 10min |
| Unbenutzte Scoring-Methoden | C-Dead | 🟢 | Automatisch | 5min |

**Geschätzte Zeit:** 25min

### `kb/library/knowledge_base/synonyms.py` — 352 Zeilen, 11 Functions/Classes

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| Synonym-Lookup: O(n²) bei Expansion? | D-Perf | 🟡 | Manuell | 10min |
| Fehlende Normalisierung | A-Code | 🟢 | Manuell | 5min |

**Geschätzte Zeit:** 15min

### `kb/library/knowledge_base/stopwords.py` — 289 Zeilen, 11 Functions/Classes

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| Stopword-Listen: Vollständigkeit, Duplikate | C-Dead | 🟢 | Automatisch | 5min |
| Set vs. List Performance | D-Perf | 🟢 | Automatisch | 5min |

**Geschätzte Zeit:** 10min

### `kb/library/knowledge_base/utils.py` — 47 Zeilen, 1 Function

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| `build_embedding_text` — einzige Funktion, ausreichend? | B-Arch | 🟢 | Manuell | 5min |

**Geschätzte Zeit:** 5min

**Tier-2 Gesamt:** ~5h 35min

---

## 4. Tier-3: CLI + Integration 🟡 Medium

### `kb/commands/llm.py` — 867 Zeilen, 36 Functions/Classes

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| Größte Command-Datei — sollte aufgespalten werden? | B-Arch | 🟠 | Manuell | 15min |
| `asyncio.run()` in `_execute()` — Thread-Safety | A-Code | 🟠 | Manuell | 15min |
| Inline-`async def` — schwer testbar | A-Code | 🟡 | Manuell | 10min |
| Unbenutzte Command-Optionen | C-Dead | 🟡 | Automatisch | 10min |

**Geschätzte Zeit:** 50min

### `kb/commands/sync.py` — 524 Zeilen, 15 Functions/Classes

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| **`execute(f"""...""")` (Zeile 423)** — SQL Injection über `file_path`? | E-Sec | 🔴 | Manuell | 20min |
| Direkte `KBConnection` vs. BaseCommand-Pattern | B-Arch | 🟡 | Manuell | 10min |
| Lange Methoden > 50 LOC | A-Code | 🟡 | Automatisch | 10min |

**Geschätzte Zeit:** 40min

### `kb/commands/audit.py` — 424 Zeilen, 16 Functions/Classes

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| Pfad-Traversal in Output-Dateipfaden? | E-Sec | 🟠 | Manuell | 10min |
| DRY: Wiederholtes `self.get_logger()` Pattern | A-Code | 🟢 | Semi-automatisch | 5min |

**Geschätzte Zeit:** 15min

### `kb/commands/ghost.py` — 262 Zeilen, 11 Functions/Classes

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| Pfad-Traversal bei Ghost-Scan? | E-Sec | 🟡 | Manuell | 10min |
| CSV-Injection in Output | E-Sec | 🟡 | Manuell | 5min |

**Geschätzte Zeit:** 15min

### `kb/commands/search.py` — 269 Zeilen, 11 Functions/Classes

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| User-Input → Suchanfrage: SQL Injection | E-Sec | 🟠 | Manuell | 10min |
| Unbenutzte Imports (`Path` 2×) | C-Dead | 🟢 | Automatisch | 3min |

**Geschätzte Zeit:** 13min

### `kb/commands/warmup.py` — 195 Zeilen, 7 Functions/Classes

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| `/proc/meminfo` — Linux-only, kein Fallback | A-Code | 🟡 | Manuell | 5min |
| Model-Warmup: Fehler bei fehlendem Model | A-Code | 🟡 | Manuell | 5min |

**Geschätzte Zeit:** 10min

### `kb/obsidian/writer.py` — 746 Zeilen, 22 Functions/Classes

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| YAML `dump` vs. `safe_dump` — Deserialization | E-Sec | 🟠 | Semi-automatisch | 10min |
| Pfad-Traversal bei Vault-Write-Operationen | E-Sec | 🟠 | Manuell | 15min |
| `shutil`-Operationen ohne Atomic Write | A-Code | 🟡 | Manuell | 10min |
| Lange Methoden | A-Code | 🟡 | Automatisch | 10min |

**Geschätzte Zeit:** 45min

### `kb/obsidian/vault.py` — 640 Zeilen, 23 Functions/Classes

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| Pfad-Traversal bei Vault-Operationen | E-Sec | 🟠 | Manuell | 15min |
| Fehlerbehandlung bei fehlendem Vault-Verzeichnis | A-Code | 🟡 | Manuell | 10min |
| Unbenutzte Vault-Methoden | C-Dead | 🟡 | Automatisch | 5min |

**Geschätzte Zeit:** 30min

### `kb/obsidian/indexer.py` — 439 Zeilen, 16 Functions/Classes

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| DB-Zugriffsmuster — direkte `sqlite3` oder `KBConnection`? | B-Arch | 🟡 | Manuell | 10min |
| Backlink-Resolution: Endlosschleife bei zirkulären Links | A-Code | 🟠 | Manuell | 15min |
| Unbenutzte Indexer-Methoden | C-Dead | 🟡 | Automatisch | 5min |

**Geschätzte Zeit:** 30min

### `kb/obsidian/resolver.py` — 315 Zeilen, 11 Functions/Classes

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| WikiLink-Resolution: Pfad-Traversal | E-Sec | 🟠 | Manuell | 10min |
| Case-Sensitivity: Obsidian vs. Linux | A-Code | 🟡 | Manuell | 10min |

**Geschätzte Zeit:** 20min

### `kb/obsidian/parser.py` — 219 Zeilen, 5 Functions/Classes

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| Regex-DoS (ReDoS) bei komplexen WikiLink-Patterns | E-Sec | 🟡 | Automatisch (regex101) | 10min |
| YAML `safe_load` vs. `load` | E-Sec | 🟠 | Semi-automatisch | 5min |

**Geschätzte Zeit:** 15min

### `kb/update.py` — 252 Zeilen, 7 Functions/Classes

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| `urllib.request.urlopen` — keine Zertifikats-Validierung? | E-Sec | 🟠 | Manuell | 10min |
| `subprocess.run` mit User-Input — Command Injection? | E-Sec | 🔴 | Manuell | 15min |
| `VERSION_FILE.write_text` — Race Condition | A-Code | 🟡 | Manuell | 5min |

**Geschätzte Zeit:** 30min

### `kb/__main__.py` — 184 Zeilen, 4 Functions/Classes

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| Command-Dispatch: unvollständige Error-Handling | A-Code | 🟡 | Manuell | 10min |
| `sys.path`-Manipulation | B-Arch | 🟠 | Manuell | 10min |

**Geschätzte Zeit:** 20min

**Tier-3 Gesamt:** ~4h 53min

---

## 5. Tier-4: Scripts + Tests 🟢 Low

### `kb/scripts/index_pdfs.py` — 750 Zeilen, 29 Functions/Classes

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| `from indexer import BiblioIndexer` — Relativer Import bricht bei Package-Usage | B-Arch | 🔴 | Manuell | 10min |
| `subprocess.run` für PDF-Extraction — Command Injection | E-Sec | 🟠 | Manuell | 15min |
| `ThreadPoolExecutor` — fehlende `shutdown()` | D-Perf | 🟡 | Manuell | 10min |
| Temp-Dateien: Cleanup bei Crash? | A-Code | 🟡 | Manuell | 10min |

**Geschätzte Zeit:** 45min

### `kb/scripts/kb_full_audit.py` — 306 Zeilen, 15 Functions/Classes

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| 4× `sqlite3.connect(DB_PATH)` — DRY, umgeht `KBConnection` | A-Code | 🟡 | Semi-automatisch | 10min |
| `from config import DB_PATH` — Fehlendes `config`-Modul | B-Arch | 🟠 | Manuell | 5min |

**Geschätzte Zeit:** 15min

### `kb/scripts/sync_chroma.py` — 117 Zeilen, 6 Functions/Classes

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| `from library.knowledge_base.chroma_integration` — Inkonsistenter Import | B-Arch | 🟠 | Manuell | 5min |
| `from config import CHROMA_PATH, DB_PATH` — Fehlendes Modul | B-Arch | 🟠 | Manuell | 5min |

**Geschätzte Zeit:** 10min

### `kb/scripts/migrate_fts5.py` — 248 Zeilen, 4 Functions/Classes

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| `from config import DB_PATH` — Fehlendes Modul | B-Arch | 🟠 | Manuell | 5min |
| Direkte `sqlite3.connect` | B-Arch | 🟡 | Semi-automatisch | 5min |

**Geschätzte Zeit:** 10min

### `kb/scripts/migrate.py` — 128 Zeilen, 6 Functions/Classes

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| `from config import DB_PATH` — Fehlendes Modul | B-Arch | 🟠 | Manuell | 5min |
| Migrations-Idempotenz | A-Code | 🟡 | Manuell | 5min |

**Geschätzte Zeit:** 10min

### `kb/scripts/kb_ghost_scanner.py` — 206 Zeilen, 11 Functions/Classes

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| `from config import DB_PATH` — Fehlendes Modul | B-Arch | 🟠 | Manuell | 5min |
| Hardcoded Pfade | C-Dead | 🟡 | Semi-automatisch | 5min |

**Geschätzte Zeit:** 10min

### `kb/scripts/reembed_all.py` — 153 Zeilen, 3 Functions/Classes

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| Direkte `sqlite3.connect` | B-Arch | 🟡 | Semi-automatisch | 5min |

**Geschätzte Zeit:** 5min

### `kb/scripts/sanitize.py` — 202 Zeilen, 4 Functions/Classes

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| Pfad-Traversal bei Sanitizing-Operationen | E-Sec | 🟡 | Manuell | 5min |

**Geschätzte Zeit:** 5min

### `kb/scripts/kb_warmup.py` — 30 Zeilen, 1 Function

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| Redundant mit `kb/commands/warmup.py`? | C-Dead | 🟡 | Manuell | 5min |

**Geschätzte Zeit:** 5min

### Test-Dateien

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| Test-Abdeckung: Keine Tests für `base/`, `llm/scheduler`, `llm/watcher`, `library/` | A-Code | 🟠 | Automatisch (pytest-cov) | 30min |
| `test_parallel_imports.py` im Projekt-Root — nicht in `tests/` | B-Arch | 🟢 | Manuell | 5min |
| `tests/llm/__init__.py` — Leere Datei | C-Dead | 🟢 | Automatisch | 2min |

**Tier-4 Tests Zeit:** 37min

**Tier-4 Gesamt:** ~2h 22min

---

## 6. Architektur-übergreifende Audits

| Checkpoint | Dimension | Priorität | Automatisierbar | Zeit |
|---|---|---|---|---|
| **Circular Import Map** — Vollständiges Import-Dependency-Diagramm | B-Arch | 🔴 | Automatisch (pydeps) | 45min |
| **`sqlite3.connect`-Inventar** — 41 Aufrufe, davon ~30 umgehen `KBConnection` | B-Arch | 🟠 | Automatisch (grep) | 15min |
| **Lock-Inventar** — 6 Locks, Lock-Ordering prüfen | B-Arch | 🟠 | Manuell | 30min |
| **DRY-Audit** — Duplizierte Patterns über alle Dateien | A-Code | 🟡 | Automatisch (jscpd) | 30min |
| **Dead Import Scan** — Unbenutzte Imports projektweit | C-Dead | 🟢 | Automatisch (autoflake) | 15min |
| **Dead Function Scan** — Nie aufgerufene Funktionen | C-Dead | 🟡 | Automatisch (vulture) | 30min |
| **Security-Pattern-Scan** — SQL-Injection, Path-Traversal, Hardcoded Creds | E-Sec | 🟠 | Automatisch (bandit) | 30min |
| **Cyclomatic Complexity** — Alle Dateien | A-Code | 🟡 | Automatisch (lizard) | 15min |

**Gesamt:** ~3h 30min

---

## 7. Zeit-Zusammenfassung

| Tier | Domain | Dateien | Geschätzte Zeit |
|---|---|---|---|
| 🔴 Tier-1 | Core + LLM | 10 | 11h 40min |
| 🟠 Tier-2 | Search + Indexing | 11 | 5h 35min |
| 🟡 Tier-3 | CLI + Integration | 13 | 4h 53min |
| 🟢 Tier-4 | Scripts + Tests | 10 | 2h 22min |
| — | Querschnitt-Audits | — | 3h 30min |
| **Gesamt** | | **44 Dateien** | **~28h** |

---

## 8. Empfohlene Werkzeuge

| Tool | Zweck | Installation |
|---|---|---|
| `bandit` | Security-Pattern-Scan | `pip install bandit` |
| `lizard` | Cyclomatic Complexity | `pip install lizard` |
| `vulture` | Dead Code Detection | `pip install vulture` |
| `autoflake` | Unused Imports | `pip install autoflake` |
| `pydeps` | Import-Dependency-Diagramm | `pip install pydeps` |
| `jscpd` | DRY/Clone-Detection | `npm i -g jscpd` |
| `pytest-cov` | Test-Abdeckung | `pip install pytest-cov` |

---

## 9. Empfohlene Reihenfolge

1. **Automatisierte Scans** (3-4h): bandit, lizard, vulture, autoflake, pydeps auf gesamtes Projekt
2. **Tier-1 Manueller Audit** (12h): Core + LLM mit Fokus auf bekannten Deadlock und async/sqlite-Probleme
3. **Tier-2 Manueller Audit** (6h): Search + Indexing mit Fokus auf SQL-Injection
4. **Querschnitt-Auswertung** (2h): Ergebnisse aus Schritten 1-3 konsolidieren
5. **Tier-3 Manueller Audit** (5h): CLI + Integration
6. **Tier-4 Manueller Audit** (2h): Scripts + Tests
7. **Abschluss-Report** (1-2h): Funde priorisieren, Action-Items erstellen