# AUDIT — Phase E, F, G

**Datum:** 2026-04-26  
**Prüfer:** Sir Stern 🔍  
**Scope:** API-Oberfläche, Hardcoded Pfade, Error Handling

---

## Phase E — API-Oberfläche

### E-1: Überdimensionierter `__all__`-Export (38 Symbole)

| Feld | Wert |
|------|------|
| **Datei** | `kb/framework/__init__.py` |
| **Problem** | 38 Symbole werden exportiert — Ziel war < 50, also formal im Rahmen, aber: viele sind Interna, die als Public-API de-facto nicht stabil sein können. Factory-Funktionen (`get_chroma`, `get_search`, `get_reranker`, `get_expander`, `get_stopword_handler`, `get_semantic_provider`, `get_keyword_provider`) und Convenience-Wrapper (`embed_text`, `embed_batch`, `rerank`, `expand_query`, `chunk_document`, `build_embedding_text`) mischen sich mit Klassen-Typen. |
| **Schwere** | 🟡 Mittel |
| **Empfehlung** | Reduziere auf eine stabile Kern-API (~15-20 Symbole). Strategie: (1) Klassen und Dataclasses als Public, (2) Factory-Funktionen als Public, (3) Convenience-Wrapper (`embed_text`, `rerank` etc.) als **nicht** in `__all__` — User können sie bei Bedarf direkt aus dem Submodul importieren. Dokumentiere explizit, was "stable API" vs. "internal convenience" ist. |

### E-2: Keine Submodul-Namespacing

| Feld | Wert |
|------|------|
| **Datei** | `kb/framework/__init__.py` |
| **Problem** | Alles wird flach in `kb.framework` exportiert. Es gibt keine hierarchische Struktur wie `kb.framework.search`, `kb.framework.embeddings`, etc. Das Namespace-Flatting macht die API schwer navigierbar und zwingt alles in einen Top-Level-Namespace. |
| **Schwere** | 🟡 Mittel |
| **Empfehlung** | Führe Sub-Namespaces ein: `kb.framework.search` (HybridSearch, SearchResult, SearchConfig), `kb.framework.embeddings` (ChromaIntegration, EmbeddingPipeline, embed_text), `kb.framework.text` (Chunker, Stopwords, Synonyms). Behalte Top-Level-Re-Exports für die 5-6 wichtigsten Symbole für Backward-Compat, aber deprecate sie. |

### E-3: Doppelte `SearchResult`-Klasse mit Alias

| Feld | Wert |
|------|------|
| **Datei** | `kb/framework/__init__.py` (Zeile 31), `kb/framework/search_providers.py` (Zeile 47) |
| **Problem** | Zwei verschiedene `SearchResult`-Dataclasses existieren: `hybrid_search.SearchResult` (viele Felder) und `search_providers.SearchResult` (vereinfacht, mit `source`/`metadata`). Im `__init__.py` wird die Provider-Version als `ProviderSearchResult` aliasiert. Das ist verwirrend — User wissen nicht, welche sie verwenden sollen. |
| **Schwere** | 🟡 Mittel |
| **Empfehlung** | Klare Trennung: `SearchResult` = User-Facing (hybrid_search), `ProviderResult` = Intern (search_providers). Den Alias `ProviderSearchResult` entfernen aus `__all__`, oder explizit als "advanced/internal" dokumentieren. Langfristig: Merge zu einer einheitlichen Klasse mit Optional-Feldern. |

### E-4: Backward Compatibility nicht dokumentiert

| Feld | Wert |
|------|------|
| **Datei** | `kb/framework/__init__.py` |
| **Problem** | Keine `__version__` definiert, keine Deprecation-Policy, keine Stability-Guarantees dokumentiert. Wenn Symbole aus `__all__` entfernt werden, brechen Imports stillschweigend. |
| **Schwere** | 🟠 Hoch |
| **Empfehlung** | (1) `__version__ = "0.x.y"` hinzufügen. (2) Docstring oder `STABLE_API`-Liste definieren, die explizit verspricht: "Diese Symbole bleiben bis v1.0 stabil". (3) `warnings.deprecate` für entfernte Symbole nutzen, bevor sie gelöscht werden. |

### E-5: `build_embedding_text` als einziges Utility im Top-Level-Export

| Feld | Wert |
|------|------|
| **Datei** | `kb/framework/__init__.py`, `kb/framework/utils.py` |
| **Problem** | `build_embedding_text` ist ein reines Implementation-Detail (wie Embedding-Text formatiert wird). Es wird von `embedding_pipeline.py` und `chroma_plugin.py` intern genutzt. Es hat im Public-API nichts zu suchen. |
| **Schwere** | 🟢 Niedrig |
| **Empfehlung** | Aus `__all__` entfernen. Bei Bedarf können User `from kb.framework.utils import build_embedding_text` verwenden, aber es sollte nicht als stabiles Public-API gelten. |

---

## Phase F — Hardcoded Pfade

### F-1: Drei verschiedene `_get_default_chroma_path()`-Definitionen

| Feld | Wert |
|------|------|
| **Datei** | `chroma_integration.py` (Z.41-49), `hybrid_search.py` (Z.31-35), `embedding_pipeline.py` (Z.34), `chroma_plugin.py` (Z.38) |
| **Problem** | `_get_default_chroma_path()` wird in **vier** Dateien unabhängig definiert, mit leicht unterschiedlichen Implementierungen: `chroma_integration.py` und `hybrid_search.py` haben try/except mit KBConfig-Fallback, `embedding_pipeline.py` importiert KBConfig direkt (ohne Fallback!), `chroma_plugin.py` importiert KBConfig direkt (ohne Fallback!). Das ist Codeduplizierung + Inkonsistenz. |
| **Schwere** | 🟠 Hoch |
| **Empfehlung** | Zentralisiere in `kb/framework/_paths.py` oder `kb/framework/config.py`: eine einzige Funktion `_get_default_chroma_path()` mit einheitlichem Fallback-Verhalten. Alle anderen Dateien importieren von dort. |

### F-2: Fallback-Pfad inkonsistent zwischen chroma und db

| Feld | Wert |
|------|------|
| **Datei** | `chroma_integration.py` (Z.45), `hybrid_search.py` (Z.35), `fts5_provider.py` (Z.49) |
| **Problem** | ChromaDB-Fallback: `Path.home() / ".openclaw" / "kb" / "chroma_db"` — aber DB-Fallback in `fts5_provider.py`: `Path.home() / ".openclaw" / "kb" / "library" / "biblio.db"`. In `hybrid_search.py` ist der DB-Fallback `db_path="library/biblio_db"` (relativ!), was ganz woanders auflöst je nach CWD. |
| **Schwere** | 🟠 Hoch |
| **Empfehlung** | Alle Default-Pfade zentral über `KBConfig` lösen. Fallback-Pfade einheitlich auf `~/.openclaw/kb/` als Base. Relative Pfade (`"library/biblio.db"`) gehören **nicht** in Default-Parameter — sie werden CWD-abhängig aufgelöst und sind ein häufiger Bug-Quelle. |

### F-3: Relative Default-Pfade in Funktionsparametern

| Feld | Wert |
|------|------|
| **Datei** | `hybrid_search.py` (Z.128: `db_path="library/biblio.db"`), `embedding_pipeline.py` (Z.79: `db_path="library/biblio.db"`, Z.81: `cache_path="library/embeddings/cache.json"`), `chroma_plugin.py` (Z.74: `db_path="library/biblio.db"`) |
| **Problem** | `"library/biblio.db"` ist ein **relativer** Pfad, der je nach Arbeitsverzeichnis der aufrufenden Process unterschiedlich aufgelöst wird. Wird das Framework z.B. von `/home/user` aufgerufen, landet die DB in `/home/user/library/biblio.db` statt in `~/.openclaw/kb/library/biblio.db`. |
| **Schwere** | 🔴 Kritisch |
| **Empfehlung** | Alle Default-Pfade als **absolut** definieren: `Path(KBConfig.get_instance().db_path)` oder `Path.home() / ".openclaw" / "kb" / "library" / "biblio.db"`. Relative Pfade nur erlauben wenn explizit vom User übergeben. |

### F-4: `kb/config.py` definiert `CHROMA_PATH = "library/chroma_db/"` — relativ und nicht genutzt?

| Feld | Wert |
|------|------|
| **Datei** | `kb/config.py` (Z.7) |
| **Problem** | `CHROMA_PATH = "library/chroma_db/"` ist relativ und in `hybrid_search.py` (Z.154) wird `from kb.config import CHROMA_PATH` verwendet. Dieser Import funktioniert nur, wenn KBConfig nicht geladen werden kann (NameError-Fallback). Aber der Pfad ist relativ → CWD-abhängig. Zudem: `kb/config.py` scheint eine alte Template-Konfiguration zu sein, die halb tot ist. |
| **Schwere** | 🟠 Hoch |
| **Empfehlung** | `kb/config.py` bereinigen: entweder entfernen (wenn tot) oder konsistent zu `KBConfig` machen. Den `CHROMA_PATH`-Import in `hybrid_search.py` ersetzen durch zentralen Pfad-Resolver. |

### F-5: `logging.basicConfig()` in Bibliothekscode

| Feld | Wert |
|------|------|
| **Datei** | `hybrid_search.py` (Z.38), `chroma_integration.py` (Z.52), `embedding_pipeline.py` (Z.37), `fts5_setup.py` (Z.235) |
| **Problem** | `logging.basicConfig(level=logging.INFO)` in vier Modulen. Das ist ein Global-Side-Effect: wenn ein User das Framework importiert, werden **alle** Logger auf INFO gesetzt und die Root-Handler-Konfiguration überschrieben. Bibliotheken dürfen `basicConfig` **nicht** aufrufen — das ist dem aufrufenden Programm überlassen. |
| **Schwere** | 🟠 Hoch |
| **Empfehlung** | Alle `logging.basicConfig()`-Aufrufe entfernen. Logger nur via `logging.getLogger(__name__)` definieren. Wenn nötig, NullHandler setzen: `logger.addHandler(logging.NullHandler())`. |

### F-6: Keine Umgebungsvariablen für Pfade im Framework-Layer

| Feld | Wert |
|------|------|
| **Datei** | `kb/base/config.py` (unterstützt `KB_DB_PATH`, `KB_CHROMA_PATH`, `KB_BASE_PATH`) |
| **Problem** | `KBConfig` unterstützt Env-Vars korrekt (`KB_DB_PATH`, `KB_CHROMA_PATH`, `KB_BASE_PATH`). Aber das Framework (`kb/framework/`) nutzt `KBConfig` nur optional (try/except ImportError). Wenn KBConfig nicht verfügbar, greifen die Fallbacks — und die berücksichtigen Env-Vars nicht. |
| **Schwere** | 🟡 Mittel |
| **Empfehlung** | Zentraler Pfad-Resolver, der immer Env-Vars prüft: (1) `KB_CHROMA_PATH` env → (2) `KBConfig.get_instance().chroma_path` → (3) `~/.openclaw/kb/chroma_db`. Analog für db_path. Niemals relative Fallbacks. |

---

## Phase G — Error Handling

### G-1: Keine Custom Exception-Klassen im Framework

| Feld | Wert |
|------|------|
| **Datei** | `kb/framework/` (alle Module) |
| **Problem** | Im gesamten `kb/framework/`-Package gibt es **null** eigene Exception-Klassen. Es wird nur `ValueError`, `Exception`, und `chromadb.errors.NotFoundError` (als `ChromaNotFoundError` aliasiert) verwendet. User können nicht gezielt auf Framework-Fehler reagieren, weil alles `except Exception` fängt. |
| **Schwere** | 🟠 Hoch |
| **Empfehlung** | Exception-Hierarchie einführen: `KBFrameworkError` (Base) → `ChromaConnectionError`, `SearchError`, `EmbeddingError`, `ConfigError`, `DatabaseError`. Bestehende `raise`/`except` schrittweise migrieren. |

### G-2: 40× `except Exception` — Breitfang-Exceptions

| Feld | Wert |
|------|------|
| **Datei** | Alle Framework-Module (insb. `hybrid_search.py`, `chroma_plugin.py`, `embedding_pipeline.py`) |
| **Problem** | 40 `except Exception`-Handler im Framework. Davon sind ~7 `except Exception:` (ohne `as e`, also Fehler-Info komplett geschluckt) und 1 bare `except:` (fängt auch `KeyboardInterrupt`, `SystemExit`). Das macht Debugging extrem schwer und verschluckt kritische Fehler. |
| **Schwere** | 🟠 Hoch |
| **Empfehlung** | (1) Bare `except:` → `except Exception:` (Z.624, hybrid_search.py). (2) `except Exception:` ohne `as e` → `except Exception as e:` + `logger.debug(...)`. (3) Gezielt catchen wo möglich: `except sqlite3.OperationalError`, `except chromadb.errors.ChromaError`, etc. (4) Langfristig: Custom Exceptions (siehe G-1). |

### G-3: Geschluckte Exceptions ohne Logging

| Feld | Wert |
|------|------|
| **Datei** | `hybrid_search.py` (Z.624: bare `except: pass`, Z.915: `except Exception: [nichts]`, Z.990: `except Exception: [nichts]`), `chroma_integration.py` (Z.600: `except Exception: pass`), `fts5_provider.py` (Z.48, Z.81: `except Exception: [nichts]`), `embedding_pipeline.py` (Z.199: `except Exception: [nichts]`), `chroma_plugin.py` (Z.192: `except Exception: [nichts]`) |
| **Problem** | Fehler werden komplett verschluckt — kein Log, kein Traceback. Wenn etwas schiefgeht, gibt es keine Möglichkeit zu debuggen, weil der Fehler nirgends sichtbar wird. |
| **Schwere** | 🔴 Kritisch |
| **Empfehlung** | Mindestens `logger.debug(f"...: {e}")` in jedem `except`-Block. Bei `except: pass` → `except Exception as e: logger.debug(f"Non-critical error: {e}")`. Geschluckte Errors sollen immer sichtbar sein, mindestens auf DEBUG-Level. |

### G-4: Kein `Result`-Typ / Keine strukturierte Fehler-Rückgabe

| Feld | Wert |
|------|------|
| **Datei** | `kb/framework/` (alle Module) |
| **Problem** | Fehler werden entweder geschluckt (→ leere Ergebnisse), als `None` zurückgegeben, oder als Exception propagiert. Es gibt keinen `Result`-Typ (wie `Ok`/`Err`), der es dem Caller erlaubt, zwischen "leer weil nichts gefunden" und "leer weil Fehler" zu unterscheiden. |
| **Schwere** | 🟡 Mittel |
| **Empfehlung** | Einen `SearchResult` um ein `errors: List[str]`-Feld erweitern, oder einen `Result[T]`-Typ einführen. Kurzfristig: Fehler-Information in den `metadata` des SearchResults liefern. Langfristig: `Result`-Monade für kritische Operationen (Embedding, Indexierung). |

### G-5: Graceful Degradation — ChromaDB

| Feld | Wert |
|------|------|
| **Datei** | `hybrid_search.py` (Z.349-350), `providers/chroma_provider.py` (Z.62, Z.80) |
| **Problem** | Graceful Degradation für ChromaDB existiert **teilweise**: Wenn ChromaDB nicht verfügbar → `self.chroma = None`, Semantic Search gibt `[]` zurück. Das funktioniert, aber: User erfährt nicht, dass Semantic Search deaktiviert ist (nur `logger.debug`). Zudem: ChromaSemanticProvider fängt alle Exceptions und loggt Warning, was besser ist, aber `is_available()` cached den Status — wenn ChromaDB während der Laufzeit restartet, bleibt `is_available() = False`. |
| **Schwere** | 🟡 Mittel |
| **Empfehlung** | (1) `logger.info` statt `logger.debug` wenn Semantic Search deaktiviert wird (User soll es merken). (2) `is_available()` sollte nicht permanent cachen, sondern periodisch re-checken (z.B. TTL-basiert oder Retry-Count). (3) Metrik/Fallback-Info im SearchResult verfügbar machen. |

### G-6: Graceful Degradation — SQLite / DB

| Feld | Wert |
|------|------|
| **Datei** | `hybrid_search.py` (Z.203), `providers/fts5_provider.py` (Z.58) |
| **Problem** | Wenn SQLite-DB nicht erreichbar → `sqlite3.connect()` wirft Exception, die nicht gefangen wird. Kein Fallback, kein In-Memory-Modus. FTS5KeywordProvider fängt den Fehler in `is_available()`, aber `search()` crasht direkt mit `sqlite3.OperationalError`. Kein SQLite-Fallback oder Graceful-Return. |
| **Schwere** | 🟠 Hoch |
| **Empfehlung** | (1) `search()` in FTS5KeywordProvider mit try/except um `sqlite3.OperationalError` schützen → `[]` zurückgeben + `logger.error`. (2) HybridSearch: wenn `db_conn` fehlschlägt, Keyword-Suche deaktivieren und nur mit Semantic weitermachen (falls verfügbar). (3) In-Memory-Fallback wäre overkill — besser: klarer Error mit Message. |

### G-7: `ChromaIntegrationV2` wirft keine Custom-Errors

| Feld | Wert |
|------|------|
| **Datei** | `chroma_integration.py` (Z.532-600+) |
| **Problem** | `ChromaIntegrationV2.__init__` kann fehlschlagen (Pfad nicht erstellbar, ChromaDB nicht installiert), wirft aber nur generische Exceptions (`OSError`, `ImportError`). Caller können nicht gezielt reagieren. |
| **Schwere** | 🟢 Niedrig |
| **Empfehlung** | Custom Exceptions nutzen (siehe G-1). `ChromaConnectionError` für Verbindungsprobleme, `ChromaInitError` für Initialisierungsfehler. |

### G-8: `EmbeddingPipeline` crasht bei ChromaDB-Fehler im Konstruktor

| Feld | Wert |
|------|------|
| **Datei** | `embedding_pipeline.py` (Z.106) |
| **Problem** | `self.chroma = get_chroma(chroma_path=str(self.chroma_path))` wird im `__init__` aufgerufen. Wenn ChromaDB nicht verfügbar (Pfad nicht erstellbar, chromadb nicht installiert), crasht der gesamte Konstruktor. Keine Graceful-Degradation — EmbeddingPipeline ist dann komplett unbrauchbar. |
| **Schwere** | 🟡 Mittel |
| **Empfehlung** | ChromaDB-Init in try/except wrappen. Bei Fehler: `self.chroma = None` + `logger.warning`. `embed()` prüft dann `if self.chroma is None` und gibt frühen Fehler/leeres Ergebnis zurück. |

---

## Zusammenfassung

| Phase | Kritisch | Hoch | Mittel | Niedrig |
|-------|----------|------|--------|---------|
| **E — API** | 0 | 1 | 3 | 1 |
| **F — Pfade** | 1 | 3 | 1 | 0 |
| **G — Errors** | 1 | 3 | 3 | 1 |
| **Total** | **2** | **7** | **7** | **2** |

### Top 3 Sofort-Maßnahmen

1. **F-3 (Kritisch):** Relative Default-Pfade → absolute Pfade via KBConfig/Fallback. Jeder Aufruf mit `"library/biblio.db"` ist CWD-abhängig und ein Bug.
2. **G-3 (Kritisch):** Geschluckte Exceptions ohne Logging → mindestens `logger.debug`. Bare `except:` entfernen.
3. **F-1 + F-4 (Hoch):** Zentralen Pfad-Resolver einführen, vierfache `_get_default_chroma_path()`-Duplizierung eliminieren, `kb/config.py` bereinigen.

### Architektur-Empfehlungen (mittelfristig)

- **Custom Exception-Hierarchie** (G-1): `KBFrameworkError` → Subclasses. Ermöglicht gezieltes Error-Handling.
- **Zentrale Pfad-Konfiguration** (F-1/F-2/F-6): Ein Modul `_paths.py` mit einheitlichem Env → KBConfig → Absolut-Fallback.
- **API-Aufräumen** (E-1/E-2/E-4): `__all__` auf ~15 stabile Symbole, Sub-Namespaces, `__version__` + Deprecation-Policy.
- **`logging.basicConfig()` entfernen** (F-5): Bibliotheken konfigurieren keine Logger global.