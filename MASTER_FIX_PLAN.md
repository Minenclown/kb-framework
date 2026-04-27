# Master-Fix-Plan — KB-Framework Audit

**Datum:** 2026-04-26  
**Quellen:** `AUDIT_PHASE_A.md`, `AUDIT_PHASE_BCD.md`, `AUDIT_PHASE_EFG.md`  
**Scope:** `~/projects/kb-framework/kb/framework/`

---

## Zusammenfassung aller Funde

| Schwere | Anzahl | Beschreibung |
|---------|--------|--------------|
| 🔴 Kritisch | 3 | Relative Pfade, geschluckte Exceptions, Deadlock-Risiko |
| 🟠 Hoch | 9 | Pfad-Duplikation, Exception-Handling, ChromaDBPlugin-Duplikation, etc. |
| 🟡 Mittel | 13 | API-Design, Thread-Safety, Modul-Aufteilung, Daten-Management |
| 🟢 Niedrig | 4 | Naming, V2-Deprecation, Custom Errors (niedrig) |
| **Total** | **29** | |

---

## Phase 1 — Kritische Fixes (≤15 Min)

### 1.1 [🔴 KRITISCH] Deadlock-Risiko beheben

**Datei:** `kb/framework/chroma_integration.py`  
**Problem:** `threading.Lock()` in `get_instance()` + `__new__` → selber Thread kann Lock nicht zweimal nehmen → Deadlock.  
**Fix:** `threading.Lock()` → `threading.RLock()` in Zeile ~10 (`_lock = threading.Lock()`).  
**Aufwand:** ~1 Minute, 1 Zeile ändern.  
**Phase:** 1 (Blocker für Parallel-Arbeit)

---

### 1.2b [🔴 KRITISCH] Portable Pfade — KBConfig nutzen statt Hardcoded Paths

**Dateien:** `kb/scripts/kb_ghost_scanner.py`, `kb/scripts/index_pdfs.py`, `kb/scripts/kb_full_audit.py`, `kb/framework/hybrid_search.py`, `kb/framework/chroma_integration.py`, `kb/framework/providers/fts5_provider.py`
**Problem:** Hartcodierte `Path.home() / ".openclaw" / "kb"` Pfade überall — wenn KB kopiert wird, zeigen alle Pfade auf `/home/lumen/.openclaw/kb` statt auf die kopierte Instanz.
**Fix:** Alle direkten `Path.home()`-Zugriffe durch `KBConfig.get_instance().base_path` ersetzen. `KBConfig` ist bereits der Singleton dafür.
**Betroffene Stellen:**
- `kb/scripts/kb_ghost_scanner.py` Z.22-33: 6× `Path.home() / ".openclaw" / "kb"`
- `kb/scripts/index_pdfs.py` Z.326: `Path.home() / "knowledge" / "kb" / "framework"`
- `kb/scripts/kb_full_audit.py` Z.20-21: `Path.home() / "knowledge" / "library"`
- `kb/framework/hybrid_search.py` Z.35: `Path.home() / ".openclaw" / "kb" / "chroma_db"`
- `kb/framework/chroma_integration.py` Z.45: `Path.home() / ".openclaw" / "kb" / "chroma_db"`
- `kb/framework/providers/fts5_provider.py` Z.14,49: `Path.home() / ".openclaw" / "kb" / "library" / "biblio.db"`
**Aufwand:** ~10 Minuten.  
**Phase:** 1 (Blocker für Portabilität)

---

### 1.2 [🔴 KRITISCH] Relative Default-Pfade → absolut

**Dateien:** `hybrid_search.py`, `embedding_pipeline.py`, `chroma_plugin.py`  
**Problem:** `"library/biblio.db"` ist relativ → CWD-abhängig → Bug.  
**Fix:** Alle Default-Pfade als absolut definieren via `Path.home() / ".openclaw" / "kb" / "library" / "biblio.db"` oder zentraler `KBConfig`-Resolver.  
**Betroffene Zeilen:**
- `hybrid_search.py` Z.128: `db_path="library/biblio.db"`
- `embedding_pipeline.py` Z.79: `db_path="library/biblio.db"`, Z.81: `cache_path="library/embeddings/cache.json"`
- `chroma_plugin.py` Z.74: `db_path="library/biblio.db"`  
**Aufwand:** ~5 Minuten.  
**Phase:** 1

---

### 1.3 [🔴 KRITISCH] Geschluckte Exceptions beheben

**Dateien:** `hybrid_search.py`, `chroma_integration.py`, `fts5_provider.py`, `embedding_pipeline.py`, `chroma_plugin.py`  
**Problem:** Bare `except:` und `except Exception:` ohne Logging verschlucken Fehler komplett.  
**Fix:** Mindestens `logger.debug(f"...: {e}")` in jeden `except`-Block. Bare `except:` → `except Exception as e: logger.debug(...)`.  
**Kritische Stellen:**
- `hybrid_search.py` Z.624: `bare except: pass` → `except Exception as e: logger.debug(f"...")`
- `hybrid_search.py` Z.915, Z.990: `except Exception:` → `except Exception as e: logger.debug(...)`
- `chroma_integration.py` Z.600: `except Exception: pass`
- `fts5_provider.py` Z.48, Z.81: `except Exception: [nichts]`
- `embedding_pipeline.py` Z.199: `except Exception: [nichts]`
- `chroma_plugin.py` Z.192: `except Exception: [nichts]`  
**Aufwand:** ~5 Minuten.  
**Phase:** 1

---

## Phase 2 — Hohe Priorität (≤20 Min)

### 2.1 [🟠 HOCH] `_get_default_chroma_path()` zentralisieren

**Problem:** 4x definiert in `chroma_integration.py`, `hybrid_search.py`, `embedding_pipeline.py`, `chroma_plugin.py`.  
**Fix:** Eine zentrale Funktion in `kb/framework/_paths.py` (oder in `kb/base/config.py` erweitern). Alle anderen importieren von dort.  
**Aufwand:** ~3 Minuten erstellen, ~5 Minuten alte Standorte ersetzen.  
**Phase:** 2

---

### 2.2 [🟠 HOCH] `kb/config.py` bereinigen

**Datei:** `kb/config.py`  
**Problem:** `CHROMA_PATH = "library/chroma_db/"` ist relativ und nicht konsistent. Import in `hybrid_search.py` nur als NameError-Fallback.  
**Fix:** Entweder entfernen (wenn tot) oder konsistent zu `KBConfig` machen. Den Import in `hybrid_search.py` ersetzen.  
**Aufwand:** ~2 Minuten.  
**Phase:** 2 (abh. von 2.1)

---

### 2.3 [🟠 HOCH] `logging.basicConfig()` entfernen

**Dateien:** `hybrid_search.py` (Z.38), `chroma_integration.py` (Z.52), `embedding_pipeline.py` (Z.37), `fts5_setup.py` (Z.235)  
**Problem:** Global-Side-Effect — alle Logger auf INFO gesetzt, Root-Handler überschrieben. Bibliotheken dürfen das nicht.  
**Fix:** Alle `logging.basicConfig(level=logging.INFO)` entfernen. Nur `logging.getLogger(__name__)` nutzen.  
**Aufwand:** ~3 Minuten, 4 Dateien.  
**Phase:** 2

---

### 2.4 [🟠 HOCH] Thread-unsafe Lazy Singletons beheben

**Dateien:** `stopwords.py`, `synonyms.py`, `hybrid_search.py`, `reranker.py`  
**Problem:** `get_handler()` ohne Lock → Race-Condition bei konkurrierendem Zugriff.  
**Fix:** `threading.RLock()` hinzufügen oder `functools.lru_cache` nutzen.  
**Aufwand:** ~5 Minuten pro Modul, batchbar.  
**Phase:** 2

---

### 2.5 [🟠 HOCH] SQLite Graceful Degradation

**Dateien:** `fts5_provider.py`, `hybrid_search.py`  
**Problem:** `sqlite3.connect()` wirft Exception wenn DB nicht erreichbar → Crash. Kein Fallback.  
**Fix:** `search()` in FTS5KeywordProvider mit try/except um `sqlite3.OperationalError` schützen → `[]` + `logger.error`. HybridSearch: wenn `db_conn` fehlschlägt, Keyword-Suche deaktivieren.  
**Aufwand:** ~5 Minuten.  
**Phase:** 2

---

### 2.6 [🟠 HOCH] ChromaDBPlugin dupliziert EmbeddingPipeline

**Dateien:** `chroma_plugin.py`, `embedding_pipeline.py`  
**Problem:** Beide implementieren dieselbe Logik (Sections lesen → Embeddings → ChromaDB). Wartungsaufwand verdoppelt.  
**Fix (kurzfristig):** `ChromaDBPlugin.flush()` delegiert an `EmbeddingPipeline`.  
**Aufwand:** ~5 Minuten.  
**Phase:** 2

---

### 2.7 [🟠 HOCH] `__version__` + Backward-Compatibility dokumentieren

**Datei:** `kb/framework/__init__.py`  
**Problem:** Keine Version, keine Stability-Guarantees. Entfernte Symbole brechen stillschweigend.  
**Fix:** `__version__ = "0.x.y"` + `STABLE_API`-Liste definieren. Symbole die entfernt werden sollen zuerst mit `warnings.deprecate()` markieren.  
**Aufwand:** ~3 Minuten.  
**Phase:** 2

---

### 2.8 [🟠 HOCH] `except Exception` Breitfang reduzieren

**Betroffene Module:** Alle Framework-Module (insb. `hybrid_search.py`, `chroma_plugin.py`, `embedding_pipeline.py`)  
**Problem:** 40× `except Exception` — zu breit, kein gezieltes Catchen.  
**Fix:** Gezielt catchen: `except sqlite3.OperationalError`, `except chromadb.errors.ChromaError`, etc.一步步 migrieren.  
**Aufwand:** ~10 Minuten (batch-Replace mit.regex, dann manuell prüfen).  
**Phase:** 2

---

### 2.9 [🟠 HOCH] Custom Exception-Hierarchie

**Datei:** `kb/framework/exceptions.py` (neu)  
**Problem:** Keine eigenen Exception-Klassen → User können nicht gezielt reagieren.  
**Fix:** Basis-Klasse `KBFrameworkError` → `ChromaConnectionError`, `SearchError`, `EmbeddingError`, `ConfigError`, `DatabaseError`. Bestehende `raise`-Stellen migrieren.  
**Aufwand:** ~5 Minuten erstellen, ~10 Minuten migrieren.  
**Phase:** 2

---

## Phase 3 — Mittlere Priorität (≤20 Min)

### 3.1 [🟡 MITTEL] `__all__` reduzieren

**Datei:** `kb/framework/__init__.py`  
**Problem:** 38 Symbole exportiert — viele sind Internals.  
**Fix:** Reduziere auf ~15-20 stabile Symbole. Convenience-Wrapper (`embed_text`, `rerank`) nicht in `__all__` (direkter Submodul-Import möglich).  
**Aufwand:** ~3 Minuten.  
**Phase:** 3

---

### 3.2 [🟡 MITTEL] Submodul-Namespacing einführen

**Datei:** `kb/framework/__init__.py`  
**Problem:** Alles flach exportiert → keine hierarchische Struktur.  
**Fix:** `kb.framework.search`, `kb.framework.embeddings`, `kb.framework.text` als Sub-Namespaces. Top-Level-Re-Exports für wichtigste Symbole (Backward-Compat).  
**Aufwand:** ~5 Minuten.  
**Phase:** 3 (abh. von 3.1)

---

### 3.3 [🟡 MITTEL] Doppelte `SearchResult`-Klassen bereinigen

**Dateien:** `kb/framework/__init__.py`, `kb/framework/search_providers.py`  
**Problem:** `SearchResult` in `hybrid_search` vs. `search_providers` — User wissen nicht welche sie verwenden sollen.  
**Fix:** Klare Trennung: `SearchResult` = User-Facing (hybrid_search), `ProviderResult` = Intern. Alias aus `__all__` entfernen.  
**Aufwand:** ~3 Minuten.  
**Phase:** 3

---

### 3.3 [🟡 MITTEL] `utils.py` → `text.py` umbenennen

**Datei:** `kb/framework/utils.py` → `kb/framework/text.py`  
**Problem:** "utils" ist ein Code-Smell-Name. Die Funktion `build_embedding_text` hat eine klare Domäne: Text-Formatierung.  
**Fix:** Umbenennen + Imports aktualisieren in `embedding_pipeline.py`, `chroma_plugin.py`.  
**Aufwand:** ~2 Minuten.  
**Phase:** 3

---

### 3.4 [🟡 MITTEL] `hybrid_search.py` als Sub-Package

**Datei:** `kb/framework/hybrid_search.py` (1.095 L)  
**Problem:** Zu groß für eine Datei, aber gut strukturiert.  
**Fix:** Aufspalten in:
```
hybrid_search/
├── __init__.py
├── models.py      # SearchResult, SearchConfig
├── engine.py      # HybridSearch-Klasse
├── keyword.py     # _keyword_search_fts(), _keyword_search()
├── semantic.py    # _semantic_search()
└── filters.py     # search_with_filters()
```  
**Aufwand:** ~10 Minuten.  
**Phase:** 3

---

### 3.5 [🟡 MITTEL] Stopword-/Synonym-Daten in JSON auslagern

**Dateien:** `stopwords.py`, `synonyms.py`  
**Problem:** Hardcodierte Daten → Änderung erfordert Code-Edit.  
**Fix:** Daten in `kb/framework/data/stopwords_de.json` und `kb/framework/data/synonyms_*.json` auslagern. Via `importlib.resources` oder `Path` laden.  
**Aufwand:** ~5 Minuten.  
**Phase:** 3

---

### 3.6 [🟡 MITTEL] KBConfig-Konstruktor-Enforcement

**Datei:** `kb/base/config.py`  
**Problem:** Nach `reset()` könnte Race-Condition beim Neukonstruieren auftreten.  
**Fix:** `__new__`-basiertes Enforcing wie `ChromaIntegration` oder `reset()` intern `_create_instance()` unter Lock aufrufen lassen.  
**Aufwand:** ~3 Minuten.  
**Phase:** 3

---

### 3.7 [🟡 MITTEL] ChromaDB `is_available()` Cache-Problem

**Dateien:** `providers/chroma_provider.py`  
**Problem:** `is_available()` cached permanent → bei ChromaDB-Restart bleibt Status `False`.  
**Fix:** TTL-basiertes Re-Check oder Retry-Count. Mindestens: `logger.info` wenn Semantic Search deaktiviert wird (nicht nur `debug`).  
**Aufwand:** ~3 Minuten.  
**Phase:** 3

---

### 3.8 [🟡 MITTEL] ChromaDB-Fallback-Pfade vereinheitlichen

**Dateien:** `chroma_integration.py`, `hybrid_search.py`, `fts5_provider.py`  
**Problem:** ChromaDB-Fallback `~/.openclaw/kb/chroma_db`, DB-Fallback `~/.openclaw/kb/library/biblio.db` — verschiedene Bases.  
**Fix:** Einheitliche Base `~/.openclaw/kb/` für alle Fallbacks.  
**Aufwand:** ~2 Minuten (abh. von 2.1).  
**Phase:** 3

---

## Phase 4 — Niedrige Priorität (Nice-to-have, ≤10 Min)

### 4.1 [🟢 NIEDRIG] `build_embedding_text` aus `__all__` entfernen

**Datei:** `kb/framework/__init__.py`  
**Problem:** Implementations-Detail im Public-API.  
**Fix:** Aus `__all__` entfernen. User können direkt `from kb.framework.text import build_embedding_text` importieren.  
**Aufwand:** 1 Minute.  
**Phase:** 4

---

### 4.2 [🟢 NIEDRIG] `ChromaIntegrationV2` deprecaten

**Dateien:** `chroma_integration.py`  
**Problem:** V2-Klasse + 5 v2-Methoden auf Basisklasse — 0 externe Aufrufer. ~120 Zeilen Totcode.  
**Fix:** Mit `@deprecated` markieren oder in Branch/Tag auslagern. Entfernen in nächstem Major-Release.  
**Aufwand:** 1 Minute.  
**Phase:** 4

---

### 4.3 [🟢 NIEDRIG] `_parse_keywords()` zusammenführen

**Dateien:** `providers/chroma_provider.py`, `providers/fts5_provider.py`  
**Problem:** Identische Funktion 2× definiert.  
**Fix:** Nach `kb/framework/text.py` verschieben, beide importieren von dort.  
**Aufwand:** 2 Minuten.  
**Phase:** 4

---

### 4.4 [🟢 NIEDRIG] `EmbeddingPipeline` Graceful Degradation

**Datei:** `embedding_pipeline.py`  
**Problem:** ChromaDB-Init im Konstruktor → bei Fehler kompletter Crash.  
**Fix:** Init in try/except → `self.chroma = None` + `logger.warning`. `embed()` prüft `if self.chroma is None`.  
**Aufwand:** 2 Minuten.  
**Phase:** 4

---

## Abhängigkeiten zwischen Phasen

```
Phase 1 (Critical)
├── 1.1 Deadlock-Fix → ermöglicht sicheres Testen
├── 1.2 Relative Pfade → Voraussetzung für 2.1
└── 1.3 Exception-Logging → Voraussetzung für G-1, G-2

Phase 2 (High)
├── 2.1 Pfad-Zentralisierung ← hängt ab von 1.2
├── 2.2 kb/config.py bereinigen ← hängt ab von 2.1
├── 2.3 logging.basicConfig() ← keine Abhängigkeiten
├── 2.4 Thread-Safety ← keine Abhängigkeiten
├── 2.5 SQLite Graceful Degradation ← keine Abhängigkeiten
├── 2.6 ChromaDBPlugin-Refaktor ← hängt ab von 2.1
├── 2.7 Version/Backw.Compat ← keine Abhängigkeiten
├── 2.8 Breitfang-Exceptions ← hängt ab von 1.3, 2.9
└── 2.9 Custom Exceptions ← hängt ab von 2.8

Phase 3 (Medium)
├── 3.1 __all__ reduzieren ← hängt ab von 3.2
├── 3.2 Namespacing ← hängt ab von 3.1
├── 3.3 SearchResult bereinigen ← hängt ab von 2.9
├── 3.4 utils.py → text.py ← keine Abhängigkeiten
├── 3.5 hybrid_search.py aufspalten ← hängt ab von 3.3, 3.4
├── 3.6 Stopword/Synonym-Daten ← hängt ab von 3.4
├── 3.7 KBConfig-Enforcement ← hängt ab von 1.1
├── 3.8 ChromaDB-Fallback vereinheitlichen ← hängt ab von 2.1

Phase 4 (Low)
├── 4.1 build_embedding_text aus __all__ ← hängt ab von 3.2
├── 4.2 V2 deprecaten ← hängt ab von 2.9
├── 4.3 _parse_keywords zusammenführen ← hängt ab von 3.4
└── 4.4 EmbeddingPipeline Graceful Degradation ← hängt ab von 2.5
```

---

## Rollback-Plan

### Strategie: Feature-Flags + Branching

1. **Vor Phase 1:** Git-Branch `fix/audit-phase1` erstellen
2. **Nach jeder Phase:** Testen, dann in `main` mergen
3. **Bei Problemen:** Zurück zum letzten funktionierenden Stand

### Rollback-Schritte pro Phase

| Phase | Rollback-Befehl | Revert-Zeit |
|-------|-----------------|-------------|
| 1.1 Deadlock | `git checkout HEAD~1 -- kb/framework/chroma_integration.py` | < 1 Min |
| 1.2 Relative Pfade | `git checkout HEAD~1 -- kb/framework/hybrid_search.py kb/framework/embedding_pipeline.py kb/framework/chroma_plugin.py` | < 2 Min |
| 1.3 Exception-Logging | `git checkout HEAD~1 -- kb/framework/*.py` | < 2 Min |
| Phase 2 gesamt | `git checkout HEAD~1 -- kb/framework/` | < 3 Min |
| Phase 3 gesamt | `git checkout HEAD~1 -- kb/framework/` | < 3 Min |
| Phase 4 gesamt | `git checkout HEAD~1 -- kb/framework/` | < 2 Min |

### Nota-Bene

- Phase 1 fixiert критичні bugs (Deadlock, CWD-Pfade, verschluckte Exceptions)
- **Diese sollten IMMER zuerst gefixt werden** — vor jedem anderen Work
- Bei Unsicherheit: erst testen, dann committen

---

## Quick Wins — Schnelle Erfolge mit hohem Impact

| # | Was | Warum | Aufwand |
|---|-----|-------|---------|
| **QW1** | `threading.Lock()` → `RLock()` in `chroma_integration.py` | Verhindert Deadlock bei Parallel-Zugriff. 1 Zeile. | 1 Min |
| **QW2** | Relative Pfade in `hybrid_search.py` Z.128 fixen | CWD-Bug → Daten landen am falschen Ort. Häufiger Bug. | 2 Min |
| **QW3** | `hybrid_search.py` Z.624: `bare except: pass` → `except Exception as e: logger.debug(...)` | Kritischer Fehler wird komplett verschluckt. | 1 Min |
| **QW4** | `logging.basicConfig()` aus 4 Dateien entfernen | Bibliotheken dürfen keine Global-Effects haben. | 3 Min |
| **QW5** | `ChromaIntegrationV2` mit `@deprecated` markieren | ~120 Zeilen Totcode, 0 Nutzer. Aufräumen ohne Risiko. | 1 Min |

**Gesamtaufwand Quick Wins:** ~8 Minuten  
**Impact:** Kritische Bugs + Technical Debt + Aufräumen

---

## Zeit-Schätzung Gesamt

| Phase | Geschätzter Aufwand |
|-------|---------------------|
| Phase 1 (Critical) | ~15 Min |
| Phase 2 (High) | ~20 Min |
| Phase 3 (Medium) | ~20 Min |
| Phase 4 (Low) | ~10 Min |
| **Gesamt** | **~65 Min** |

**Empfohlene Reihenfolge:** Phase 1 komplett → Testen → Phase 2 → Testen → Phase 3 → Phase 4

---

*Erstellt: 2026-04-26*  
*Quelle: Alle drei Audit-Berichte von Sir Stern*