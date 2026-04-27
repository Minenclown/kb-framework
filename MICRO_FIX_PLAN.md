# MICRO_FIX_PLAN — KB-Framework Audit

**Datum:** 2026-04-26  
**Zweck:** Atomare, mikroskopische Tasks (1–2 Fixes, max. 10 Min)  
**Problem:** Kontextfenster-Überlastung bei mehreren Fixes gleichzeitig  

---

## ✅ BERITS ERLEDIGT — Phase 1

| Task | Fix | Datei(en) | Aufwand |
|------|-----|-----------|---------|
| 1.1 | Deadlock-Fix: `threading.Lock()` → `threading.RLock()` | `chroma_integration.py` | ~1 Min |
| 1.2a | Relative Default-Pfade → absolut (`library/biblio.db` etc.) | `hybrid_search.py`, `embedding_pipeline.py`, `chroma_plugin.py` | ~5 Min |
| 1.2b | Portable Pfade: `Path.home()` → `KBConfig.get_instance().base_path` | `kb_ghost_scanner.py`, `index_pdfs.py`, `kb_full_audit.py`, `hybrid_search.py`, `chroma_integration.py`, `fts5_provider.py` | ~10 Min |
| 1.3 | Geschluckte Exceptions: `bare except:` + `except Exception:` → `logger.debug(...)` | `hybrid_search.py`, `chroma_integration.py`, `fts5_provider.py`, `embedding_pipeline.py`, `chroma_plugin.py` | ~5 Min |

---

## Phase 2 — Hohe Priorität (7 Tasks)

### Block A: Pfad-Zentralisierung

#### Task 2.1 — `_get_default_chroma_path()` zentralisieren
**Dateien:** `kb/framework/chroma_integration.py` (Z.4–7), `kb/framework/hybrid_search.py` (Z.30–34), `kb/framework/embedding_pipeline.py` (Z.70–73), `kb/framework/chroma_plugin.py` (Z.68–71)  
**Änderung:** Eine neue Datei `kb/framework/_paths.py` anlegen mit der Funktion `def _get_default_chroma_path() -> Path`. Alle 4 Stellen ersetzen durch `from kb.framework._paths import _get_default_chroma_path`.  
**Aufwand:** ~7 Min  
**Abhängigkeiten:** keine  

#### Task 2.2 — `kb/config.py` bereinigen
**Dateien:** `kb/config.py`, `kb/framework/hybrid_search.py` (Z.38)  
**Änderung:** Prüfen ob `CHROMA_PATH = "library/chroma_db/"` in `kb/config.py` noch benötigt wird. Falls nicht: Eintrag entfernen + den Fallback-Import in `hybrid_search.py` ersetzen durch `from kb.framework._paths import _get_default_chroma_path`.  
**Aufwand:** ~3 Min  
**Abhängigkeiten:** Task 2.1  

---

### Block B: Logging & Side-Effects

#### Task 2.3 — `logging.basicConfig()` entfernen
**Dateien:** `kb/framework/hybrid_search.py` (Z.38), `kb/framework/chroma_integration.py` (Z.52), `kb/framework/embedding_pipeline.py` (Z.37), `kb/framework/providers/fts5_setup.py` (Z.235)  
**Änderung:** Jeweils die Zeile `logging.basicConfig(level=logging.INFO)` entfernen. Keine Ersetzung nötig — nur löschen.  
**Aufwand:** ~3 Min  
**Abhängigkeiten:** keine  

---

### Block C: Thread-Safety

#### Task 2.4 — Thread-unsafe Lazy Singletons beheben
**Dateien:** `kb/framework/stopwords.py`, `kb/framework/synonyms.py`, `kb/framework/hybrid_search.py`, `kb/framework/reranker.py`  
**Änderung:** In `get_handler()` (oder equivalent): `threading.Lock()` durch `threading.RLock()` ersetzen ODER `@functools.lru_cache(maxsize=1)` auf die Handler-Getter-Funktion setzen. Pro Datei eine Stelle.  
**Aufwand:** ~8 Min (2 Min pro Datei × 4 Dateien)  
**Abhängigkeiten:** keine  

---

### Block D: Error Handling

#### Task 2.5 — SQLite Graceful Degradation
**Dateien:** `kb/framework/providers/fts5_provider.py` (Z.48–50, Z.81–83), `kb/framework/hybrid_search.py` (Z.??? fallback path)  
**Änderung:** In `FTS5KeywordProvider.search()`: `try: conn = sqlite3.connect(...); ... except Exception as e: logger.error(f"FTS5 not available: {e}"); return []`. In `HybridSearch.__init__()`: wenn `db_conn` fehlschlägt, `self.keyword_provider = None` statt zu crashen.  
**Aufwand:** ~7 Min  
**Abhängigkeiten:** keine  

#### Task 2.8 — `except Exception` Breitfang reduzieren
**Dateien:** `kb/framework/hybrid_search.py`, `kb/framework/chroma_plugin.py`, `kb/framework/embedding_pipeline.py`  
**Änderung:** Gezielte Exception-Typen verwenden: `except sqlite3.OperationalError` statt `except Exception` bei DB-Zugriffen; `except (KeyError, ValueError)` statt `except Exception` bei Parsing. Nicht alle 40 Stellen auf einmal — die 10 kritischsten Stellen ersetzen.  
**Aufwand:** ~10 Min  
**Abhängigkeiten:** Task 1.3 (muss bereits done sein)  

---

### Block E: Code-Duplikation

#### Task 2.6 — ChromaDBPlugin duplizierte Logik entfernen
**Dateien:** `kb/framework/chroma_plugin.py`, `kb/framework/embedding_pipeline.py`  
**Änderung:** In `ChromaDBPlugin.flush()`: den eigenen Implementationscode durch einen Aufruf von `EmbeddingPipeline.get_instance().flush()` ersetzen. Vorher prüfen ob `EmbeddingPipeline` die gleiche Logik schon vollständig abdeckt.  
**Aufwand:** ~5 Min  
**Abhängigkeiten:** keine  

---

### Block F: API-Stability

#### Task 2.7 — `__version__` + Backward-Compatibility dokumentieren
**Dateien:** `kb/framework/__init__.py`  
**Änderung:** Am Anfang der Datei `__version__ = "0.1.0"` setzen. Eine Liste `_STABLE_API = [...]` mit den Symbolen die als stabil gelten (nicht intern).  
**Aufwand:** ~3 Min  
**Abhängigkeiten:** keine  

#### Task 2.9 — Custom Exception-Hierarchie erstellen
**Dateien:** `kb/framework/exceptions.py` (neu), alle Module die Exceptions werfen  
**Änderung:** Neue Datei mit `class KBFrameworkError(Exception)`, davon abgeleitet `ChromaConnectionError`, `SearchError`, `EmbeddingError`, `ConfigError`, `DatabaseError`. Bestehende `raise RuntimeError(...)` und `raise Exception(...)` an den wichtigsten 5–10 Stellen durch die neuen Klassen ersetzen.  
**Aufwand:** ~10 Min  
**Abhängigkeiten:** Task 2.8 (für saubere Exception-Strukturierung)  

---

## Phase 3 — Mittlere Priorität (8 Tasks)

### Block G: API-Aufräumen

#### Task 3.1 — `__all__` reduzieren
**Dateien:** `kb/framework/__init__.py` (Z.5–38)  
**Änderung:** Die `__all__`-Liste von 38 auf ~15–20 stabile öffentliche Symbole kürzen. Interne Helfer (`_parse_keywords`, `build_embedding_text`, etc.) entfernen.  
**Aufwand:** ~5 Min  
**Abhängigkeiten:** keine  

#### Task 3.2 — Submodul-Namespacing einführen
**Dateien:** `kb/framework/__init__.py`, Untermodule (`search_providers.py`, `embedding_pipeline.py`, etc.)  
**Änderung:** Explizite Sub-Namespaces als Re-Exports definieren: `search = _search_modul`, `embeddings = _embedding_modul`. Top-Level für wichtigste Symbole (Backward-Compat) behalten.  
**Aufwand:** ~7 Min  
**Abhängigkeiten:** Task 3.1  

---

### Block H: Daten-Modell bereinigen

#### Task 3.3 — Doppelte `SearchResult`-Klasse bereinigen
**Dateien:** `kb/framework/__init__.py`, `kb/framework/search_providers.py`, `kb/framework/hybrid_search.py`  
**Änderung:** `SearchResult` bleibt in `hybrid_search.py` (User-Facing). In `search_providers.py` umbenennen zu `ProviderResult`. Alias für Backward-Compat in `__init__.py`. `__all__` aktualisieren.  
**Aufwand:** ~5 Min  
**Abhängigkeiten:** Task 2.9 (Custom Exceptions für saubere Hierarchie)  

#### Task 3.4 — `utils.py` → `text.py` umbenennen
**Dateien:** `kb/framework/utils.py` → `kb/framework/text.py`, `kb/framework/embedding_pipeline.py`, `kb/framework/chroma_plugin.py`  
**Änderung:** Datei umbenennen. Imports in `embedding_pipeline.py` und `chroma_plugin.py` aktualisieren.  
**Aufwand:** ~3 Min  
**Abhängigkeiten:** keine  

---

### Block I: Große Refaktorierungen

#### Task 3.5 — `hybrid_search.py` als Sub-Package
**Dateien:** `kb/framework/hybrid_search.py` → `kb/framework/hybrid_search/` (6 neue Dateien)  
**Änderung:** Aufspalten in: `__init__.py` (Re-Export), `models.py` (SearchResult, SearchConfig), `engine.py` (HybridSearch-Klasse), `keyword.py` (keyword search), `semantic.py` (semantic search), `filters.py` (filter logic). Imports in allen externen Dateien aktualisieren.  
**Aufwand:** ~10 Min  
**Abhängigkeiten:** Task 3.3, Task 3.4  

#### Task 3.6 — Stopword-/Synonym-Daten in JSON auslagern
**Dateien:** `kb/framework/stopwords.py`, `kb/framework/synonyms.py`, `kb/framework/data/stopwords_de.json` (neu), `kb/framework/data/synonyms_*.json` (neu)  
**Änderung:** Hardcodierte Listen in jeweilige JSON-Dateien auslagern. Loader-Funktion in `stopwords.py`/`synonyms.py` ändert sich zu `json.load(open(data_path))`. `importlib.resources` oder `Path(__file__).parent / "data" / "..."` nutzen.  
**Aufwand:** ~7 Min  
**Abhängigkeiten:** Task 3.4  

---

### Block J: Config & Caching

#### Task 3.7 — KBConfig-Konstruktor-Enforcement
**Dateien:** `kb/base/config.py`  
**Änderung:** Prüfen ob nach `reset()` eine Race-Condition möglich ist. Falls ja: `__new__`-basiertes Singleton-Enforcing hinzufügen (wie bei ChromaIntegration) oder `reset()` intern mit Lock aufrufen.  
**Aufwand:** ~5 Min  
**Abhängigkeiten:** Task 1.1  

#### Task 3.8 — ChromaDB-Fallback-Pfade vereinheitlichen
**Dateien:** `kb/framework/chroma_integration.py`, `kb/framework/hybrid_search.py`, `kb/framework/providers/fts5_provider.py`  
**Änderung:** Alle Fallbacks konsolidieren auf `~/.openclaw/kb/` als einheitliche Base. Überall `from kb.framework._paths import _get_default_chroma_path` nutzen (Task 2.1 Voraussetzung).  
**Aufwand:** ~3 Min  
**Abhängigkeiten:** Task 2.1  

---

## Phase 4 — Niedrige Priorität (4 Tasks)

#### Task 4.1 — `build_embedding_text` aus `__all__` entfernen
**Dateien:** `kb/framework/__init__.py`  
**Änderung:** `build_embedding_text` aus `__all__`-Liste streichen. User können direkt `from kb.framework.text import build_embedding_text` importieren.  
**Aufwand:** ~2 Min  
**Abhängigkeiten:** Task 3.2  

#### Task 4.2 — `ChromaIntegrationV2` deprecaten
**Dateien:** `kb/framework/chroma_integration.py`  
**Änderung:** `@deprecated("ChromaIntegrationV2 is deprecated and will be removed in 1.0")` Decorator auf die Klasse setzen. Alternative: in `__init__.py` nur noch `ChromaIntegration` exportieren.  
**Aufwand:** ~2 Min  
**Abhängigkeiten:** Task 2.9  

#### Task 4.3 — `_parse_keywords()` zusammenführen
**Dateien:** `kb/framework/providers/chroma_provider.py` (Z.???), `kb/framework/providers/fts5_provider.py` (Z.???) → `kb/framework/text.py`  
**Änderung:** Die identische Funktion `_parse_keywords()` aus beiden Providern extrahieren und nach `kb/framework/text.py` verschieben. Beide Provider importieren von dort.  
**Aufwand:** ~3 Min  
**Abhängigkeiten:** Task 3.4  

#### Task 4.4 — `EmbeddingPipeline` Graceful Degradation
**Dateien:** `kb/framework/embedding_pipeline.py`  
**Änderung:** ChromaDB-Initialisierung im Konstruktor in `try/except` wrappen. Bei Fehler: `self.chroma = None` + `logger.warning("ChromaDB unavailable, semantic search disabled")`. In `embed()` und `flush()`: `if self.chroma is None: return` bzw. early-return.  
**Aufwand:** ~5 Min  
**Abhängigkeiten:** Task 2.5  

---

## Übersicht

| Phase | Tasks | Geschätzte Zeit |
|-------|-------|-----------------|
| Phase 1 (Kritisch) | 4 Tasks ✅ | ~15 Min (done) |
| Phase 2 (Hoch) | 7 Tasks | ~53 Min |
| Phase 3 (Mittel) | 8 Tasks | ~45 Min |
| Phase 4 (Niedrig) | 4 Tasks | ~12 Min |
| **Gesamt** | **23 Tasks** | **~125 Min** |

---

## Reihenfolge (Critical Path)

```
[Phase 1 done]
       ↓
Task 2.1 → Task 2.2
Task 2.3 (parallel)
Task 2.4 (parallel)
Task 2.5 (parallel)
Task 2.8 (nach 1.3)
       ↓
Task 2.6, 2.7 (parallel)
Task 2.9 (nach 2.8)
       ↓
Phase 2 complete
       ↓
Task 3.1, 3.4 (parallel)
Task 3.2 (nach 3.1)
Task 3.7 (nach 1.1)
Task 3.8 (nach 2.1)
Task 3.3 (nach 2.9)
Task 3.5, 3.6 (nach 3.3+3.4)
       ↓
Phase 3 complete
       ↓
Task 4.1 (nach 3.2)
Task 4.2 (nach 2.9)
Task 4.3 (nach 3.4)
Task 4.4 (nach 2.5)
       ↓
Phase 4 complete ✓
```

---

*Erstellt: 2026-04-26*  
*Grundlage: MASTER_FIX_PLAN.md*  
*Kein Beispiel-Code — nur strukturierte, atomare Tasks*  
