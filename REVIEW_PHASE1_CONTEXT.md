# REVIEW_PHASE1_CONTEXT.md — KB-Framework Refactor: Kontext-Rahmen

**Erstellt:** 2026-04-26  
**Prüfer:** Sir Stern 🔍  
**Zweck:** Überblick über den aktuellen Zustand der KB nach dem Refactor — was geplant war, was gemacht wurde, was fehlt.

---

## 1. Was wurde geplant?

### 1.1 Ursprünglicher Plan: REFACTOR_WORKFLOW.md (Ordnerstruktur-Refactor)

**Ziel:** Architektur bereinigen durch:
- `kb/knowledge_base/` löschen (nur Redirect-Stubs)
- `src/library/` → `kb/framework/` verschieben
- Semantisch saubere Trennung: `kb/framework/` = Code-Gerüst, `kb/library/` = Nutzdaten

**8 Phasen geplant:**
1. Baseline Tests dokumentieren
2. `kb/knowledge_base/` löschen + Config anpassen
3. `src/library/` → `kb/framework/` verschieben
4. Code-Imports in `kb/scripts/` anpassen
5. Code-Imports in `kb/commands/` + Circular Import fixen
6. Tests fixen
7. Dokumentation anpassen
8. Verifikation

**Zeitbudget:** ~30-35 Min insgesamt

### 1.2 Audit-Pläne: MICRO_FIX_PLAN.md + MASTER_FIX_PLAN.md

Nach dem Struktur-Refactor wurde ein umfassender Code-Audit durchgeführt, der **29 Probleme** identifizierte (3 kritisch, 9 hoch, 13 mittel, 4 niedrig).

**Geplant in 4 Phasen:**

| Phase | Tasks | Zeit | Fokus |
|-------|-------|------|-------|
| Phase 1 (Kritisch) | 4 Tasks | ~15 Min | Deadlock, Pfade, Exceptions |
| Phase 2 (Hoch) | 7 Tasks | ~53 Min | Pfad-Zentralisierung, Logging, Thread-Safety |
| Phase 3 (Mittel) | 8 Tasks | ~45 Min | API-Aufräumen, Modul-Aufteilung |
| Phase 4 (Niedrig) | 4 Tasks | ~12 Min | Deprecation, Utils-Cleanup |

**Total:** 23 atomare Tasks, ~125 Min geschätzt

---

## 2. Was wurde tatsächlich gemacht?

### 2.1 Struktur-Refactor (REFACTOR_WORKFLOW.md) — ✅ ERLEDIGT

Der Git-Commit `359220f` ("Release v1.1.0: Clean Architecture Refactor") zeigt die Umsetzung:
- `kb/knowledge_base/` → gelöscht
- `src/library/` → nach `kb/framework/` verschoben
- Alle Import-Pfade angepasst
- `providers/` Sub-Package erstellt (`chroma_provider.py`, `fts5_provider.py`)
- `search_providers.py` als Protocol/Interface-Datei hinzugefügt

### 2.2 Phase 1 (Kritische Fixes) — ✅ ERLEDIGT

| Task | Status | Beweis |
|------|--------|--------|
| 1.1 Deadlock-Fix: `threading.Lock()` → `threading.RLock()` | ✅ Erledigt | `chroma_integration.py:77` und `:544` beide `RLock`; `stopwords.py:221`, `synonyms.py:213`, `engine.py:607`, `reranker.py:196` alle `RLock` |
| 1.2a Relative Default-Pfade → absolut | ✅ Erledigt | `paths.py` erstellt mit `get_default_db_path()` und `get_default_chroma_path()`; alle Module importieren von dort |
| 1.2b Portable Pfade: `Path.home()` → `KBConfig` | ✅ Erledigt | `embedding_pipeline.py` nutzt `KBConfig.get_instance().db_path` und `.base_path`; `fts5_provider.py` importiert `get_default_db_path` |
| 1.3 Geschluckte Exceptions → Logging | ✅ Erledigt | `except Exception as e: logger.debug(...)` Muster etabliert; keine bare `except:` oder stummen `except Exception:` mehr gefunden |

### 2.3 Phase 2 (Hohe Priorität) — 🟡 TEILWEISE ERLEDIGT

| Task | Status | Details |
|------|--------|---------|
| 2.1 `_get_default_chroma_path()` zentralisieren | ✅ Erledigt | `paths.py` erstellt, 4+ Module importieren von dort |
| 2.2 `kb/config.py` bereinigen | 🟡 Teilweise | `paths.py` existiert, aber alter `CHROMA_PATH` in `kb/config.py` vermutlich noch vorhanden |
| 2.3 `logging.basicConfig()` entfernen | ✅ Erledigt | Keine `logging.basicConfig`-Aufrufe mehr in `kb/framework/` |
| 2.4 Thread-unsafe Lazy Singletons beheben | ✅ Erledigt | Alle 4 Module nutzen jetzt `threading.RLock()` |
| 2.5 SQLite Graceful Degradation | 🟡 Teilweise | FTS5 provider hat Error-Handling, aber genaue Implementation muss geprüft werden |
| 2.6 ChromaDBPlugin duplizierte Logik | ❌ Nicht erledigt | `chroma_plugin.py` hat noch eigene Embedding-Logik |
| 2.7 `__version__` + Backward-Compatibility | ✅ Erledigt | `__version__ = "0.1.0"` und `STABLE_API`-Liste in `__init__.py` |
| 2.8 `except Exception` Breitfang reduzieren | 🟡 Teilweise | Von ~40 auf ~27 reduziert, aber immer noch viele breite catches |
| 2.9 Custom Exception-Hierarchie | ✅ Erledigt | `exceptions.py` mit 8 Custom Exceptions (`KBFrameworkError`, `ChromaConnectionError`, `SearchError`, `EmbeddingError`, `ConfigError`, `DatabaseError`, `PipelineError`, `ProviderError`) — werden auch bereits genutzt |

### 2.4 Phase 3 (Mittlere Priorität) — 🟡 TEILWEISE ERLEDIGT

| Task | Status | Details |
|------|--------|---------|
| 3.1 `__all__` reduzieren | ❌ Nicht erledigt | `__init__.py` exportiert weiterhin viele Symbole (inkl. `STABLE_API`-Liste, aber `__all__` nicht reduziert) |
| 3.2 Submodul-Namespacing | ❌ Nicht erledigt | Keine Sub-Namespaces (`kb.framework.search`, etc.) |
| 3.3 Doppelte `SearchResult`-Klasse bereinigen | ✅ Erledigt | `search_providers.py` nutzt jetzt `ProviderResult`; `hybrid_search/models.py` hat `SearchResult` |
| 3.4 `utils.py` → `text.py` umbenennen | ✅ Erledigt | `text.py` existiert, `utils` ist ein Directory/Verweis |
| 3.5 `hybrid_search.py` als Sub-Package | ✅ Erledigt | `hybrid_search/` mit `__init__.py`, `engine.py`, `models.py`, `keyword.py`, `semantic.py`, `filters.py` |
| 3.6 Stopword-/Synonym-Daten in JSON | ✅ Erledigt | `kb/framework/data/stopwords_de.json`, `synonyms_medical.json`, `synonyms_technical.json` existieren |
| 3.7 KBConfig-Konstruktor-Enforcement | ❌ Unbekannt | Nicht geprüft |
| 3.8 ChromaDB-Fallback-Pfade vereinheitlichen | ✅ Erledigt | `paths.py` zentralisiert alle Pfade |

### 2.5 Phase 4 (Niedrige Priorität) — 🟡 TEILWEISE ERLEDIGT

| Task | Status | Details |
|------|--------|---------|
| 4.1 `build_embedding_text` aus `__all__` | ❌ Nicht erledigt | Noch in `__all__` exportiert |
| 4.2 `ChromaIntegrationV2` deprecaten | 🟡 Teilweise | `@deprecated` Decorator existiert und ist auf `ChromaIntegrationV2` angewendet — aber Klasse + V2-Methoden noch vorhanden |
| 4.3 `_parse_keywords()` zusammenführen | ❌ Nicht geprüft | |
| 4.4 `EmbeddingPipeline` Graceful Degradation | ❌ Nicht erledigt | |

---

## 3. Was wurde übersprungen / vergessen?

### Kritisch / Hoch priorisiert aber nicht gemacht:

1. **`kb/config.py` Bereinigung** (Task 2.2) — Der alte `CHROMA_PATH` in `kb/config.py` wurde vermutlich nicht aufgeräumt. `paths.py` ist die neue zentrale Lösung, aber Altlast könnte bleiben.

2. **`except Exception` Breitfang** (Task 2.8) — Von ~40 auf ~27 reduziert, aber immer noch viele breite Catches. Nur teilweise migriert zu Custom Exceptions.

3. **ChromaDBPlugin duplizierte Logik** (Task 2.6) — `chroma_plugin.py` hat noch eigene Embedding-Logik statt an `EmbeddingPipeline` zu delegieren.

4. **SQLite Graceful Degradation** (Task 2.5) — FTS5 Provider hat Error-Handling, aber `HybridSearch` crasht vermutlich noch bei DB-Fehlern.

### Mittel / Niedrig priorisiert und nicht gemacht:

5. **`__all__` reduzieren** (Task 3.1) — `__init__.py` exportiert weiterhin alles flach.

6. **Submodul-Namespacing** (Task 3.2) — Keine `kb.framework.search` / `kb.framework.embeddings` Namespaces.

7. **KBConfig-Konstruktor-Enforcement** (Task 3.7) — Race-Condition nach `reset()` vermutlich noch offen.

8. **`build_embedding_text` aus `__all__`** (Task 4.1) — Noch exportiert.

9. **`_parse_keywords()` zusammenführen** (Task 4.3) — Nicht geprüft.

10. **`EmbeddingPipeline` Graceful Degradation** (Task 4.4) — Nicht umgesetzt.

### Aus dem Audit (AUDIT_PHASE_BCD.md) erwähnt aber nicht in MICRO_FIX_PLAN:

11. **`ChromaIntegrationV2` + V2-Methoden entfernen** — `@deprecated` vorhanden, aber Code existiert noch (~120 Zeilen Totcode). Kein Termin für Entfernung.

12. **`batching.py` Backend-Funktionen** — `batched_chroma_upsert/delete()` und `batched_executemany()` koppeln Utility an ChromaDB/SQLite. Nicht verschoben.

13. **`embedding_pipeline.py` Sub-Package** — Nicht aufgeteilt geblieben.

14. **`Result`-Typ / Fehlerkommunikation** (G-4) — Kein `Result[T]` oder Error-Flags in `SearchResult`. Unterscheidung "leer weil nichts gefunden" vs. "leer wegen Fehler" nicht möglich.

15. **ChromaDB `is_available()` Cache-Problem** (3.7) — Permanent-Cache, kein TTL-basiertes Re-Check.

---

## 4. Welche Dateien wurden geändert? (Grober Überblick)

### Neue Dateien (durch Refactor):
- `kb/framework/paths.py` — Zentraler Pfad-Resolver
- `kb/framework/exceptions.py` — Custom Exception-Hierarchie (8 Klassen)
- `kb/framework/text.py` — Umbenannt von `utils.py`
- `kb/framework/data/stopwords_de.json` — Ausgelagerte Stopword-Daten
- `kb/framework/data/synonyms_medical.json` — Ausgelagerte Synonym-Daten
- `kb/framework/data/synonyms_technical.json` — Ausgelagerte Synonym-Daten
- `kb/framework/hybrid_search/` — Sub-Package (vorher Monolith):
  - `__init__.py`
  - `engine.py`
  - `models.py`
  - `keyword.py`
  - `semantic.py`
  - `filters.py`
- `kb/framework/providers/__init__.py` — Provider-Sub-Package
- `kb/framework/providers/chroma_provider.py` — ChromaDB Semantic Provider
- `kb/framework/providers/fts5_provider.py` — FTS5 Keyword Provider
- `kb/framework/search_providers.py` — Protocol-Interfaces + `ProviderResult`

### Signifikant geänderte Dateien:
- `kb/framework/chroma_integration.py` — `RLock`, `@deprecated`, Custom Exceptions, Pfade via `paths.py`
- `kb/framework/hybrid_search/` (ehemals `hybrid_search.py`) — Aufgeteilt, `RLock`, Custom Exceptions, Pfade
- `kb/framework/embedding_pipeline.py` — KBConfig-Pfade, Pfade via `paths.py`
- `kb/framework/chroma_plugin.py` — Pfade via `paths.py`
- `kb/framework/__init__.py` — `__version__`, `STABLE_API`, Custom Exception-Exports, `ProviderResult`
- `kb/framework/stopwords.py` — `RLock`, JSON-Loading
- `kb/framework/synonyms.py` — `RLock`, JSON-Loading
- `kb/framework/reranker.py` — `RLock`
- `kb/framework/fts5_setup.py` — Logging-Cleanup (kein `basicConfig` mehr)
- `kb/base/config.py` — (Teilweise angepasst)
- `kb/scripts/` — Import-Pfade angepasst
- `kb/commands/` — Import-Pfade angepasst
- Diverse `README.md`, `SKILL.md`, `FUNCTIONS.md`, etc. — Import-Pfade aktualisiert

### Gelöscht:
- `kb/knowledge_base/` — Komplett entfernt (war nur Redirect-Stubs)
- `src/library/` → nach `kb/framework/` verschoben

---

## 5. Fortschritts-Übersicht

| Phase | Geplante Tasks | Erledigt | Teilweise | Offen |
|-------|---------------|---------|-----------|-------|
| **Struktur-Refactor** | 8 | 8 | 0 | 0 |
| **Phase 1 (Kritisch)** | 4 | 4 | 0 | 0 |
| **Phase 2 (Hoch)** | 7 | 4 | 2 | 1 |
| **Phase 3 (Mittel)** | 8 | 4 | 0 | 4 |
| **Phase 4 (Niedrig)** | 4 | 0 | 1 | 3 |
| **Total** | 31 | 20 | 3 | 8 |

**Fortschritt:** ~65% der geplanten Tasks erledigt oder teilweise erledigt.

### Kritischste offene Punkte:
1. 🔴 **ChromaDBPlugin duplizierte Logik** (Task 2.6) — Wartungsaufwand verdoppelt
2. 🟠 **`except Exception` Breitfang** (Task 2.8) — Noch ~27 breite Catches, Custom Exceptions nur teilweise genutzt
3. 🟠 **SQLite Graceful Degradation** (Task 2.5) — Potenzielle Crashes bei DB-Fehlern
4. 🟡 **`__all__` reduzieren + Namespacing** (Tasks 3.1/3.2) — API-Oberfläche unübersichtlich

---

*Erstellt von Sir Stern 🔍 — Phase 1 Review*