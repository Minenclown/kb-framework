# ✅ KB-Framework — Audit-Checkliste

**Erstellt:** 2026-04-15  
**Scope:** Alle Python-Dateien in `kb/`, `tests/`, `scripts/`  
**Legende:** 🔴 Critical 🟠 High 🟡 Medium 🟢 Low | 🤖 Automatisch 👤 Manuell 🔄 Semi-automatisch

---

## 0. Automatisierte Vor-Scans (Vorab ausführen)

- [ ] 🤖 `bandit -r kb/ -f markdown -o bandit_report.md` — Security-Scan 🔴
- [ ] 🤖 `lizard kb/ --markdown > complexity_report.md` — Cyclomatic Complexity 🟡
- [ ] 🤖 `vulture kb/ --min-confidence 80 > deadcode_report.txt` — Dead Code 🟡
- [ ] 🤖 `autoflake --check --remove-all-unused-imports -r kb/` — Unused Imports 🟢
- [ ] 🤖 `pydeps kb --max-bacon=2 -o imports.svg` — Import-Diagramm 🔴
- [ ] 🤖 `grep -rn "sqlite3.connect" kb/ --include="*.py" | wc -l` — sqlite3-Inventar 🟠
- [ ] 🤖 `grep -rn "threading.Lock\|_lock" kb/ --include="*.py"` — Lock-Inventar 🟠
- [ ] 🤖 `grep -rn "yaml.load\b" kb/ --include="*.py"` — Unsafe YAML 🟠
- [ ] 🤖 `grep -rn "execute(f" kb/ --include="*.py"` — f-string SQL 🟠
- [ ] 🤖 `pytest --cov=kb --cov-report=term-missing tests/ 2>/dev/null || echo "pytest-cov not available"` — Test-Abdeckung 🟠

---

## 1. Tier-1: Core + LLM 🔴 Critical

### `kb/base/config.py` — 228 LOC

- [ ] 👤 Double-Checked Locking in `KBConfig.get_instance()` — Race Condition prüfen 🔴
- [ ] 👤 Module-Level Side Effects — Singleton-Initialisierung bei Import 🔴
- [ ] 👤 `threading.Lock` Usage — Deadlock-Potential mit `KBLogger._lock` 🟠
- [ ] 🔄 Hardcoded Pfade/Defaults — `grep -n "Path\|str(" kb/base/config.py` 🟠
- [ ] 🤖 Unbenutzte Config-Keys — `vulture` oder AST-Scan 🟡

### `kb/base/db.py` — 305 LOC

- [ ] 👤 SQL Injection: `conn.execute(f"PRAGMA {pragma}={value}")` Zeile 92 🔴
- [ ] 👤 Fehlender Lock auf `KBConnection` — Thread-Safety 🟠
- [ ] 👤 Context Manager: `__exit__` Exception-Safety 🟠
- [ ] 👤 Schema-Validierung — Edge Cases & Vollständigkeit 🟡
- [ ] 👤 Connection-Pool vs. Einzel-Connection Performance 🟡

### `kb/base/logger.py` — 189 LOC

- [ ] 👤 Lock-Ordering: `_lock` + `_cache_lock` vs. `KBConfig._lock` 🟠
- [ ] 👤 Logger-Cache — Memory Leak (unbounded dict?) 🟡
- [ ] 🤖 Unbenutzte Logger-Methoden — `vulture` 🟢

### `kb/base/command.py` — 285 LOC

- [ ] 👤 Error-Handling in `_execute()` — vollständige Exception-Abdeckung? 🟠
- [ ] 🔄 DRY: `get_config()`/`get_logger()`/`get_connection()` Pattern-Wiederholung 🟡
- [ ] 🤖 ABC-Abstrakte Methoden vollständig? — `python -c "import kb.base.command"` 🟡

### `kb/llm/config.py` — 278 LOC

- [ ] 👤 `LLMConfig._lock` — Double-Checked Locking Race (wie KBConfig) 🔴
- [ ] 🔄 Hardcoded API-Endpunkte/Modellnamen — `grep -n "http\|model" kb/llm/config.py` 🟠
- [ ] 👤 Config-Validation — Fehlende Felder → Runtime-Crash? 🟠
- [ ] 👤 `get_llm_config()` — Globale State-Mutation 🟡

### `kb/llm/scheduler/task_scheduler.py` — 1.159 LOC 🔥

- [ ] 👤 10× `sqlite3.connect()` in async-Methoden — Blockiert Event Loop 🔴
- [ ] 👤 Race Conditions in async Job-Queue 🔴
- [ ] 👤 Signal-Handling `_handle_signal` — Graceful Shutdown 🟠
- [ ] 🤖 Funktionstiefe > 50 LOC — `lizard` Report prüfen 🟠
- [ ] 🤖 Unbenutzte Job-Types — `vulture` + manuelle Verifikation 🟡
- [ ] 👤 Error-Recovery bei DB-Fehlern fehlt? 🟠
- [ ] 🤖 Cyclomatic Complexity > 15 — `lizard` Report 🟡

### `kb/llm/engine/ollama_engine.py` — 455 LOC

- [ ] 👤 `OllamaEngine._lock` — Lock-Ordering mit `KBConfig._lock` 🟠
- [ ] 👤 `urllib.request` ohne konfigurierbares Timeout 🟠
- [ ] 👤 Fehlende Retry-Logic bei HTTP 429/503 🟠
- [ ] 👤 `response.read()` — Unbounded Memory bei Streaming 🟡
- [ ] 👤 Error-Klassenhierarchie — korrekt implementiert? 🟢

### `kb/llm/content_manager.py` — 677 LOC

- [ ] 👤 YAML-Parsing: `yaml.load` vs. `yaml.safe_load` 🔴
- [ ] 👤 DB-Zugriff über `KBConnection` vs. direkte `sqlite3` 🟠
- [ ] 🤖 Lange Methoden > 50 LOC — `lizard` 🟡
- [ ] 👤 Transaktions-Isolation bei Concurrent Writes 🟠

### `kb/llm/generator/report_generator.py` — 1.242 LOC 🔥

- [ ] 👤 Architectural Review — Größte Datei, muss aufgespalten werden? 🟠
- [ ] 🤖 Funktionen > 100 LOC — `lizard` Report 🟠
- [ ] 🔄 DRY: Gemeinsame Patterns mit `essence_generator.py` 🟡
- [ ] 🤖 Unbenutzte Report-Typen — `vulture` 🟡
- [ ] 👤 Template-Strings — Injection über User-Content möglich? 🟡

### `kb/llm/generator/essence_generator.py` — 906 LOC

- [ ] 🔄 DRY mit `report_generator.py` — duplizierte Retry/Prompt-Logik 🟠
- [ ] 👤 `_generate_with_retry` — Endlosschleife bei permanentem Fehler? 🔴
- [ ] 👤 `_compute_hotspot_score` — Algorithmen-Komplexität 🟡
- [ ] 🤖 Unbenutzte Score-Funktionen — `vulture` 🟡

### `kb/llm/watcher/file_watcher.py` — 716 LOC

- [ ] 👤 11× `sqlite3.connect()` in async-Methoden — Blockiert Event Loop 🔴
- [ ] 👤 File-Hashing: `hashlib` Memory bei großen Dateien 🟡
- [ ] 👤 Watcher-Loop: fehlende Backpressure bei Events 🟠
- [ ] 🔄 DRY: Wiederholte `sqlite3.connect` Pattern 🟡

---

## 2. Tier-2: Search + Indexing 🟠 High

### `kb/library/knowledge_base/hybrid_search.py` — 997 LOC

- [ ] 👤 Direkte `sqlite3.connect()` — umgeht `KBConnection` 🟠
- [ ] 👤 FTS5-Query-Konstruktion — SQL Injection über Suchterme? 🔴
- [ ] 👤 RRF-Scoring — numerische Stabilität (Division durch 0?) 🟠
- [ ] 👤 Architectural Review — Größte Search-Datei 🟡
- [ ] 🤖 Cyclomatic Complexity in `search()` — `lizard` 🟡

### `kb/library/knowledge_base/chroma_integration.py` — 481 LOC

- [ ] 👤 Module-Level `KBConfig.get_instance()` — Import-Deadlock 🔴
- [ ] 🔄 ChromaDB `Settings` — hardcoded Pfade 🟡
- [ ] 👤 Error-Handling bei ChromaDB-Verbindungsverlust 🟠
- [ ] 👤 `@contextmanager` — Exception-Safety 🟡

### `kb/library/knowledge_base/chroma_plugin.py` — 433 LOC

- [ ] 👤 Module-Level `KBConfig.get_instance()` — Import-Deadlock 🔴
- [ ] 👤 `self._lock` — Lock-Ordering mit `KBConfig._lock` 🟠
- [ ] 👤 `Queue`-Pattern — Deadlock bei vollem Queue? 🟠
- [ ] 🔄 3× direkte `sqlite3.connect()` umgeht `KBConnection` 🟡
- [ ] 👤 Thread-Safety des Plugin-Hook-Systems 🟠

### `kb/library/knowledge_base/embedding_pipeline.py` — 523 LOC

- [ ] 👤 Module-Level `KBConfig.get_instance()` — Import-Deadlock 🔴
- [ ] 👤 `ThreadPoolExecutor` — fehlende `shutdown()` 🟠
- [ ] 🔄 2× direkte `sqlite3.connect()` umgeht `KBConnection` 🟡
- [ ] 👤 Batch-Processing: unbounded list in Memory 🟡

### `kb/indexer.py` — 719 LOC

- [ ] 👤 Direkte `sqlite3.connect()` auf `self.conn` — kein `KBConnection` 🟠
- [ ] 👤 `readlines()` bei großen Dateien — Memory 🟠
- [ ] 👤 Fehlende Exception-Behandlung bei Datei-I/O 🟡
- [ ] 👤 ABC-Implementation: `MarkdownIndexer`/`BiblioIndexer` 🟡
- [ ] 🤖 Unbenutzte Methoden — `vulture` 🟡

### `kb/library/knowledge_base/chunker.py` — 421 LOC

- [ ] 👤 Edge Cases: Leerer Text, sehr kurze Chunks 🟡
- [ ] 👤 Overlap-Berechnung: Off-by-One Fehler 🟡
- [ ] 👤 Performance bei sehr langen Dokumenten 🟢

### `kb/library/knowledge_base/fts5_setup.py` — 274 LOC

- [ ] 🔄 Direkte `sqlite3.connect()` 🟡
- [ ] 👤 FTS5-Tokenizer-Konfiguration korrekt? 🟡
- [ ] 👤 Migrations-Idempotenz 🟡

### `kb/library/knowledge_base/reranker.py` — 281 LOC

- [ ] 👤 Cross-Encoder Model Loading — Memory 🟡
- [ ] 👤 Fallback bei fehlendem Model 🟠
- [ ] 🤖 Unbenutzte Scoring-Methoden — `vulture` 🟢

### `kb/library/knowledge_base/synonyms.py` — 352 LOC

- [ ] 👤 Synonym-Lookup: O(n²) bei Expansion? 🟡
- [ ] 👤 Fehlende Text-Normalisierung 🟢

### `kb/library/knowledge_base/stopwords.py` — 289 LOC

- [ ] 🤖 Stopword-Listen: Duplikate prüfen 🟢
- [ ] 🤖 Set vs. List Performance 🟢

### `kb/library/knowledge_base/utils.py` — 47 LOC

- [ ] 👤 `build_embedding_text` — einzige Funktion, ausreichend? 🟢

---

## 3. Tier-3: CLI + Integration 🟡 Medium

### `kb/commands/llm.py` — 867 LOC

- [ ] 👤 Aufspaltung nötig? — Größte Command-Datei 🟠
- [ ] 👤 `asyncio.run()` in `_execute()` — Thread-Safety 🟠
- [ ] 👤 Inline-`async def` — schwer testbar 🟡
- [ ] 🤖 Unbenutzte Command-Optionen — `vulture` 🟡

### `kb/commands/sync.py` — 524 LOC

- [ ] 👤 **`execute(f"""...""")` Zeile 423 — SQL Injection über `file_path`** 🔴
- [ ] 👤 Direkte `KBConnection` vs. BaseCommand-Pattern 🟡
- [ ] 🤖 Lange Methoden > 50 LOC — `lizard` 🟡

### `kb/commands/audit.py` — 424 LOC

- [ ] 👤 Pfad-Traversal in Output-Dateipfaden? 🟠
- [ ] 🔄 DRY: Wiederholtes `self.get_logger()` Pattern 🟢

### `kb/commands/ghost.py` — 262 LOC

- [ ] 👤 Pfad-Traversal bei Ghost-Scan? 🟡
- [ ] 👤 CSV-Injection in Output 🟡

### `kb/commands/search.py` — 269 LOC

- [ ] 👤 User-Input → Suchanfrage: SQL Injection 🟠
- [ ] 🤖 Unbenutzte Imports (`Path` 2× importiert) 🟢

### `kb/commands/warmup.py` — 195 LOC

- [ ] 👤 `/proc/meminfo` — Linux-only, kein Fallback 🟡
- [ ] 👤 Model-Warmup: Fehler bei fehlendem Model 🟡

### `kb/obsidian/writer.py` — 746 LOC

- [ ] 👤 YAML `dump` vs. `safe_dump` — Deserialization 🟠
- [ ] 👤 Pfad-Traversal bei Vault-Write-Operationen 🟠
- [ ] 👤 `shutil`-Operationen ohne Atomic Write 🟡
- [ ] 🤖 Lange Methoden — `lizard` 🟡

### `kb/obsidian/vault.py` — 640 LOC

- [ ] 👤 Pfad-Traversal bei Vault-Operationen 🟠
- [ ] 👤 Fehlerbehandlung bei fehlendem Vault-Verzeichnis 🟡
- [ ] 🤖 Unbenutzte Vault-Methoden — `vulture` 🟡

### `kb/obsidian/indexer.py` — 439 LOC

- [ ] 👤 DB-Zugriffsmuster — direkte `sqlite3` oder `KBConnection`? 🟡
- [ ] 👤 Backlink-Resolution: Endlosschleife bei zirkulären Links 🟠
- [ ] 🤖 Unbenutzte Indexer-Methoden — `vulture` 🟡

### `kb/obsidian/resolver.py` — 315 LOC

- [ ] 👤 WikiLink-Resolution: Pfad-Traversal 🟠
- [ ] 👤 Case-Sensitivity: Obsidian vs. Linux 🟡

### `kb/obsidian/parser.py` — 219 LOC

- [ ] 🔄 Regex-DoS (ReDoS) bei WikiLink-Patterns 🟡
- [ ] 🔄 YAML `safe_load` vs. `load` 🟠

### `kb/update.py` — 252 LOC

- [ ] 👤 `urllib.request.urlopen` — Zertifikats-Validierung? 🟠
- [ ] 👤 **`subprocess.run` mit User-Input — Command Injection?** 🔴
- [ ] 👤 `VERSION_FILE.write_text` — Race Condition 🟡

### `kb/__main__.py` — 184 LOC

- [ ] 👤 Command-Dispatch: unvollständiges Error-Handling 🟡
- [ ] 👤 `sys.path`-Manipulation 🟠

---

## 4. Tier-4: Scripts + Tests 🟢 Low

### `kb/scripts/index_pdfs.py` — 750 LOC

- [ ] 👤 **`from indexer import BiblioIndexer` — Relativer Import bricht bei Package-Usage** 🔴
- [ ] 👤 `subprocess.run` für PDF-Extraction — Command Injection 🟠
- [ ] 👤 `ThreadPoolExecutor` — fehlende `shutdown()` 🟡
- [ ] 👤 Temp-Dateien: Cleanup bei Crash? 🟡

### `kb/scripts/kb_full_audit.py` — 306 LOC

- [ ] 🔄 4× `sqlite3.connect(DB_PATH)` — DRY-Verletzung 🟡
- [ ] 👤 `from config import DB_PATH` — Fehlendes `config`-Modul 🟠

### `kb/scripts/sync_chroma.py` — 117 LOC

- [ ] 👤 `from library.knowledge_base.chroma_integration` — Inkonsistenter Import 🟠
- [ ] 👤 `from config import CHROMA_PATH, DB_PATH` — Fehlendes Modul 🟠

### `kb/scripts/migrate_fts5.py` — 248 LOC

- [ ] 👤 `from config import DB_PATH` — Fehlendes Modul 🟠
- [ ] 🔄 Direkte `sqlite3.connect` 🟡

### `kb/scripts/migrate.py` — 128 LOC

- [ ] 👤 `from config import DB_PATH` — Fehlendes Modul 🟠
- [ ] 👤 Migrations-Idempotenz 🟡

### `kb/scripts/kb_ghost_scanner.py` — 206 LOC

- [ ] 👤 `from config import DB_PATH` — Fehlendes Modul 🟠
- [ ] 🔄 Hardcoded Pfade 🟡

### `kb/scripts/reembed_all.py` — 153 LOC

- [ ] 🔄 Direkte `sqlite3.connect` 🟡

### `kb/scripts/sanitize.py` — 202 LOC

- [ ] 👤 Pfad-Traversal bei Sanitizing-Operationen 🟡

### `kb/scripts/kb_warmup.py` — 30 LOC

- [ ] 👤 Redundant mit `kb/commands/warmup.py`? 🟡

### Test-Dateien

- [ ] 🤖 Test-Abdeckung messen — `pytest --cov=kb` 🟠
- [ ] 👤 Keine Tests für `base/`, `llm/scheduler`, `llm/watcher`, `library/` 🟠
- [ ] 👤 `test_parallel_imports.py` im Projekt-Root → verschieben nach `tests/` 🟢
- [ ] 🤖 `tests/llm/__init__.py` — Leere Datei, wird nicht benötigt 🟢

---

## 5. Querschnitt-Checks

- [ ] 🤖 **Circular Import Map** — `pydeps kb -o imports.svg` 🔴
- [ ] 🤖 **sqlite3.connect-Inventar** — 41 Aufrufe, ~30 umgehen `KBConnection` 🟠
- [ ] 👤 **Lock-Ordering-Analyse** — 6 Locks im Projekt, potentielle Deadlocks 🟠
- [ ] 🤖 **DRY-Audit** — `jscpd kb/ --min-lines 6` 🟡
- [ ] 🤖 **Dead Import Scan** — `autoflake --check -r kb/` 🟢
- [ ] 🤖 **Dead Function Scan** — `vulture kb/ --min-confidence 80` 🟡
- [ ] 🤖 **Security-Pattern-Scan** — `bandit -r kb/` 🟠
- [ ] 🤖 **Cyclomatic Complexity** — `lizard kb/ -C 15` 🟡

---

## 6. __init__.py Audit

| Datei | Zeilen | Status | Checkpoint |
|---|---|---|---|
| `kb/__init__.py` | 39 | ✅ Re-Exports | [ ] 👤 Korrekte Exports? 🟢 |
| `kb/base/__init__.py` | 21 | ✅ Re-Exports | [ ] 👤 Korrekte Exports? 🟢 |
| `kb/commands/__init__.py` | 154 | ✅ Registry | [ ] 👤 Lazy-Import korrekt? 🟡 |
| `kb/scripts/__init__.py` | 35 | ⚠️ Inhalte prüfen | [ ] 👤 Enthält Code? 🟢 |
| `kb/obsidian/__init__.py` | 51 | ✅ Re-Exports | [ ] 👤 Korrekte Exports? 🟢 |
| `kb/llm/__init__.py` | 80 | ✅ Re-Exports | [ ] 👤 Korrekte Exports? 🟢 |
| `kb/llm/engine/__init__.py` | 15 | ✅ Re-Exports | [ ] 👤 Korrekte Exports? 🟢 |
| `kb/llm/generator/__init__.py` | 28 | ✅ Re-Exports | [ ] 👤 Korrekte Exports? 🟢 |
| `kb/llm/scheduler/__init__.py` | 21 | ✅ Re-Exports | [ ] 👤 Korrekte Exports? 🟢 |
| `kb/llm/watcher/__init__.py` | 19 | ✅ Re-Exports | [ ] 👤 Korrekte Exports? 🟢 |
| `kb/llm/templates/__init__.py` | 7 | ⚠️ Platzhalter | [ ] 👤 Leer/Platzhalter — entfernen? 🟢 |
| `kb/library/__init__.py` | 47 | ✅ Re-Exports | [ ] 👤 Korrekte Exports? 🟢 |
| `kb/library/llm/__init__.py` | 11 | ⚠️ Platzhalter | [ ] 👤 Leer/Platzhalter — entfernen? 🟢 |
| `kb/library/knowledge_base/__init__.py` | 143 | ✅ Re-Exports | [ ] 👤 Over-Exporting? 🟡 |
| `tests/llm/__init__.py` | 0 | ❌ Leere Datei | [ ] 🤖 Entfernen 🟢 |
| `tests/test_llm/__init__.py` | 7 | ✅ OK | — |

---

## 7. Statistik

| Kategorie | Checkpoints | 🔴 Critical | 🟠 High | 🟡 Medium | 🟢 Low |
|---|---|---|---|---|---|
| Code-Quality (A) | 28 | 3 | 9 | 12 | 4 |
| Architektur (B) | 32 | 7 | 10 | 12 | 3 |
| Dead Code (C) | 14 | 0 | 0 | 8 | 6 |
| Performance (D) | 13 | 3 | 3 | 6 | 1 |
| Security (E) | 18 | 5 | 7 | 5 | 1 |
| **Gesamt** | **105** | **18** | **29** | **43** | **15** |

**Automatisierbar:** 35 | **Semi-automatisch:** 14 | **Manuell:** 56

---

## 8. Bekannte Vorfunde (aus Vorab-Analyse)

| # | Fund | Datei | Zeile | Dimension | Priorität |
|---|---|---|---|---|---|
| 1 | Import-Deadlock via Module-Level `KBConfig.get_instance()` | `chroma_integration.py`, `chroma_plugin.py`, `embedding_pipeline.py` | je ~30 | B-Arch | 🔴 |
| 2 | 10× sync `sqlite3.connect` in async `task_scheduler.py` | `task_scheduler.py` | divers | D-Perf | 🔴 |
| 3 | 11× sync `sqlite3.connect` in async `file_watcher.py` | `file_watcher.py` | divers | D-Perf | 🔴 |
| 4 | SQL Injection via f-string: `execute(f"""...""")` | `sync.py` | 423 | E-Sec | 🔴 |
| 5 | `execute(f"PRAGMA {pragma}={value}")` | `db.py` | 92 | E-Sec | 🔴 |
| 6 | Double-Checked Locking Race in `KBConfig`/`LLMConfig` | `config.py`, `llm/config.py` | je ~40 | B-Arch | 🔴 |
| 7 | Relative Importe in Scripts brechen bei Package-Usage | `index_pdfs.py` | divers | B-Arch | 🔴 |
| 8 | `subprocess.run` mit User-Input in `update.py` | `update.py` | 177 | E-Sec | 🔴 |
| 9 | ~30 `sqlite3.connect` umgehen `KBConnection` Layer | divers | divers | B-Arch | 🟠 |
| 10 | Keine Tests für `base/`, `llm/scheduler`, `llm/watcher`, `library/` | `tests/` | — | A-Code | 🟠 |