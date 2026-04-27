# Exception Analysis: Custom Exceptions in `kb/framework/`

**Datum:** 2026-04-26  
**Analysiert von:** Sir Stern 🔍

## Zusammenfassung

Die Datei `kb/framework/exceptions.py` definiert 9 Custom Exceptions, die **keine einzige** im Framework-Code verwendet werden. Stattdessen nutzt der Code ausschließlich:

1. **Bare `except Exception as e`** — fängt alles, schluckt oft, gibt `None`/`False`/leere Liste zurück
2. **Standard-Python-Exceptions** — `ValueError`, `sqlite3.OperationalError`
3. **Kein Raising von Custom Exceptions** — Fehler werden geloggt, aber nie als typisierte Exception nach oben gereicht

**Ergebnis:** Caller können nicht gezielt auf Framework-Fehler reagieren. Jeder `except Exception`-Block ist ein potenzielles Fehler-Schwarzes Loch.

---

## Priorisierte Liste: Top 10 Stellen für Custom Exception Migration

### Priorität 1 — Kritisch: Fehler werden verschluckt, Caller hat keine Chance zu reagieren

| # | Datei | Zeile | Aktueller Code | Empfohlene Exception | Begründung |
|---|-------|-------|---------------|----------------------|------------|
| 1 | `providers/chroma_provider.py` | 63 | `except Exception as e: logger.warning(...); self._chroma = None` | **`ChromaConnectionError`** | ChromaDB-Initialisierung schlägt fehl → wird stillschweigend auf None gesetzt. Caller (`is_available()`, `search()`) bekommt kein Signal, dass ChromaDB unreachable ist. Sollte `ChromaConnectionError` raisen, damit Caller entscheiden kann: Retry? Fallback? Abbruch? |
| 2 | `embedding_pipeline.py` | 106 | `except Exception as e: self.chroma = None; logger.warning(...)` | **`ChromaConnectionError`** | Gleiche Situation wie #1: ChromaDB-Init im Pipeline-Konstruktor schlägt fehl → Degraded-Mode ohne Signal. Pipeline-Consumer weiß nicht, ob Embeddings wirklich erzeugt werden können. |
| 3 | `chroma_plugin.py` | 122 | `except Exception as e: logger.warning(...); self._chroma = None` | **`ChromaConnectionError`** | Drittes Vorkommen desselben Musters (Lazy-Load ChromaDB). Sollte `ChromaConnectionError` raisen statt stillschweigend None zu setzen. |
| 4 | `chroma_plugin.py` | 139 | `except Exception as e: logger.warning(...); self._pipeline = None` | **`PipelineError`** | EmbeddingPipeline-Initialisierung schlägt fehl → Pipeline=None. Plugin-Consumer kann keine Embeddings erzeugen, erfährt aber nicht warum. `PipelineError` gibt Context. |

### Priorität 2 — Hoch: Suchfehler werden stillschweigend zu leeren Results

| # | Datei | Zeile | Aktueller Code | Empfohlene Exception | Begründung |
|---|-------|-------|---------------|----------------------|------------|
| 5 | `providers/chroma_provider.py` | 147 | `except Exception as e: ... return []` | **`SearchError`** | ChromaDB-Suche schlägt fehl → gibt leere Liste zurück. Caller (HybridSearch Engine) interpretiert das als "keine Ergebnisse" statt als "Suche fehlgeschlagen". Unterscheidet nicht zwischen "nichts gefunden" und "Fehler bei der Suche". |
| 6 | `providers/fts5_provider.py` | 99 | `except Exception as e: logger.warning(...); return []` | **`SearchError`** | Gleiche Problematik wie #5: FTS5-Suche schlägt fehl → leere Liste. HybridSearch kann nicht entscheiden, ob Fallback nötig ist. |
| 7 | `chroma_integration.py` | 316 | `except Exception as e: logger.error(...); return 0` | **`DatabaseError`** | `delete_by_file_id()` schlägt fehl → return 0. Caller weiß nicht, ob 0 = "nichts zu löschen" oder "Löschen fehlgeschlagen". Kritisch für Datenkonsistenz. |

### Priorität 3 — Mittel: Degraded-Mode ohne klare Fehlerkommunikation

| # | Datei | Zeile | Aktueller Code | Empfohlene Exception | Begründung |
|---|-------|-------|---------------|----------------------|------------|
| 8 | `hybrid_search/engine.py` | 90 | `except Exception as e: logger.warning(...); self.chroma = None` | **`ChromaConnectionError`** | HybridSearch-Engine initiiert ChromaDB → Fehler → chroma=None. Engine läuft im degraded-Mode weiter. Sollte `ChromaConnectionError` raisen, damit Engine selbst entscheiden kann, ob sie ohne Semantic-Search starten will. |
| 9 | `reranker.py` | 138 | `except Exception as e: logger.warning(...); return results (with 0.0 scores)` | **`ProviderError`** | Cross-Encoder Reranking schlägt fehl → Ergebnis wird mit 0.0-Scores zurückgegeben. Caller kann nicht unterscheiden zwischen "nicht reranked" und "reranking fehlgeschlagen". `ProviderError` gibt Context. |
| 10 | `embedding_pipeline.py` | 278 | `except Exception as e: logger.error(...); [failed jobs]` | **`EmbeddingError`** | Batch-Embedding schlägt fehl → alle Sections in Batch werden als "failed" markiert. Caller (Plugin) erfährt nur über Log, nicht über Exception. `EmbeddingError` würde gezieltes Retry-Handling ermöglichen. |

---

## Architekturelle Empfehlungen

### 1. Exception-Hierarchie nutzen

```
KBFrameworkError
├── ConfigError          → Pfade, Settings, Umgebungsvariablen
├── ChromaConnectionError → Alle ChromaDB-Verbindungsprobleme
├── SearchError          → Alle Suchfehler (Semantic + Keyword)
├── EmbeddingError       → Embedding-Generierung, Model-Loading
├── DatabaseError        → SQLite-Fehler (nicht-FTS5)
├── PluginError          → Plugin-Lifecycle, Hook-Fehler
├── PipelineError        → Pipeline-Verarbeitung, Batch-Fehler
└── ProviderError        → Provider-Schnittstellen, Reranking
```

### 2. Muster: Graceful Degradation MIT Custom Exceptions

**Aktuell (schlecht):**
```python
try:
    self.chroma = get_chroma()
except Exception as e:
    logger.warning(f"ChromaDB not available: {e}")
    self._chroma = None  # ← Schwarzes Loch
```

**Empfohlen:**
```python
try:
    self.chroma = get_chroma()
except ChromaConnectionError as e:
    logger.warning(f"ChromaDB not available: {e}")
    self._chroma = None
    self._chroma_error = e  # ← Fehler behalten für spätere Diagnose
    # ODER: raise, wenn ChromaDB zwingend nötig
```

### 3. Zwei-Phasen-Strategie

**Phase 1 (Low-Hanging Fruit):** Ersetze `except Exception as e` durch spezifische `except ChromaConnectionError` / `except SearchError` etc. und re-raise als Custom Exception:

```python
except Exception as e:
    raise ChromaConnectionError(f"ChromaDB init failed: {e}") from e
```

**Phase 2 (Architecture):** Führe Result-Types oder Error-Flags ein, damit Graceful Degradation UND Fehlerkommunikation koexistieren:

```python
@dataclass
class SearchResult:
    results: list
    error: Optional[KBFrameworkError] = None
    degraded: bool = False
```

### 4. Verbleibende `except Exception as e`-Blöcke

Nicht in Top-10, aber erwähnenswert:
- `chunker.py:103` — NLTK/Sentence-Splitter Import-Fehler → `PluginError`
- `fts5_setup.py:85,130,192,222` — FTS5 Setup-Fehler → `DatabaseError`
- `chroma_integration.py:421,618` — ChromaDB-Operationen → `ChromaConnectionError`
- `chroma_plugin.py:244,365` — Plugin-Operationen → `PluginError`
- `fts5_provider.py:253` — FTS5 Insert → `DatabaseError`

---

## Fazit

| Metrik | Wert |
|--------|------|
| Custom Exceptions definiert | 9 |
| Custom Exceptions verwendet | **0** |
| `except Exception as e` in `kb/framework/` | **~25** |
| `raise RuntimeError/Exception` in `kb/framework/` | **0** (nur 1× `ValueError` in `batching.py:78`) |
| Kritische Stellen (Top 10) | 4× ChromaConnectionError, 2× SearchError, 1× DatabaseError, 1× PipelineError, 1× ProviderError, 1× EmbeddingError |

**Hauptproblem:** Nicht fehlende `raise RuntimeError`, sondern **fehlende `raise CustomException`**. Der Code fängt alle Fehler mit `except Exception`, loggt sie, und gibt Fallback-Werte zurück. Custom Exceptions werden nie geworfen, nie gefangen, nie nach oben gereicht. Die Exception-Hierarchie ist tot.

**Empfehlung:** Mindestens die Top-4 Stellen sofort migrieren. Die restlichen in einem Folgeschritt.