# Phase 8: Sicherheit & Error Handling — Review

**Datum:** 2026-04-26  
**Reviewer:** Sir Stern 🔍  
**Codebase:** `kb-framework/` (Post-Phase-7)

---

## Zusammenfassung

| Kategorie | Risiko | Befund |
|---|---|---|
| SQL Injection | 🟢 KEIN RISIKO | Alle Queries parametrisiert (`?`-Platzhalter) |
| Path Traversal | 🟡 MITTEL | Keine Validierung in `chroma_integration.py`; `ChromaDBPlugin` akzeptiert beliebige `db_path`/`chroma_path` |
| Information Leakage | 🟡 MITTEL | Exception-Messages leaken Pfade (`db_path`, `chroma_path`) in Logs |
| Breite `except Exception` | 🟡 MITTEL | 35 Vorkommen, davon ~8 problematisch (verschlucken Errors) |
| Input Validation | 🔴 HOCH | Keine File-Size-Limits, keine Batch-Size-Validation |

---

## 1. SQL Injection — 🟢 KEIN RISIKO

### Befund

Alle SQL-Queries verwenden **parametrisierte Platzhalter (`?`)** statt String-Interpolation.

**Geprüfte Dateien:**

| Datei | Methode | Parameterisierung |
|---|---|---|
| `providers/fts5_provider.py` | `_search_fts()`, `_search_like()` | ✅ `?`-Platzhalter |
| `hybrid_search/keyword.py` | `_keyword_search_fts()`, `_keyword_search()` | ✅ `?`-Platzhalter |
| `hybrid_search/filters.py` | `search_with_filters()` | ✅ `?`-Platzhalter |
| `fts5_setup.py` | `rebuild_fts5_index()` | ✅ `?`-Platzhalter |
| `chroma_plugin.py` | `on_file_indexed()`, `on_file_removed()` | ✅ `?`-Platzhalter |
| `embedding_pipeline.py` | Diverse Queries | ✅ `?`-Platzhalter |

**FTS5 MATCH-Query** (`keyword.py:191`):
```python
fts5_query = ' AND '.join(fts5_query_parts)
sql = "... WHERE file_sections_fts MATCH ?"
cursor = db_conn.execute(sql, (fts5_query, limit))
```
Der FTS5-Query-String wird als Parameter übergeben — **keine Injection möglich**, obwohl der String dynamisch aus User-Input konstruiert wird. SQLites `MATCH`-Syntax wird sicher als Parameter übergeben.

**LIKE-Query** (`keyword.py:228-237`):
```python
for term in terms:
    like_clauses.append("(section_content LIKE ? OR section_header LIKE ?)")
    params.extend([f"%{term}%", f"%{term}%"])
```
✅ Platzhalter statt f-string.

**Bewertung:** Sauber implementiert. Kein Handlungsbedarf.

---

## 2. Path Traversal — 🟡 MITTEL

### 2.1 `chroma_integration.py`

**Problem:** `ChromaIntegration.__init__()` und `ChromaIntegrationV2.__init__()` akzeptieren beliebige Pfade ohne Validierung:

```python
# chroma_integration.py:117
self.chroma_path = Path(chroma_path).expanduser()

# chroma_integration.py:562
self.chroma_path = Path(chroma_path).expanduser()
```

`expanduser()` resolved `~`, validiert aber nicht gegen `../`-Sequenzen. Ein Aufruf mit `chroma_path="/etc/../../etc/passwd"` würde `Path("/etc/passwd")` ergeben — kein echtes Traversal-Risiko, da ChromaDB nur Verzeichnisse erstellt. Aber es gibt keine Prüfung, ob der Pfad innerhalb eines erlaubten Basisverzeichnisses liegt.

**Empfehlung:**
```python
def _validate_path(self, path: Path, allowed_base: Path) -> Path:
    """Ensure path is within allowed base directory."""
    resolved = path.resolve()
    base = allowed_base.resolve()
    if not str(resolved).startswith(str(base)):
        raise ValueError(f"Path {resolved} is outside allowed base {base}")
    return resolved
```

### 2.2 `ChromaDBPlugin`

```python
# chroma_plugin.py:98
self.db_path = Path(db_path).expanduser()
self.chroma_path = Path(chroma_path).expanduser()
```

Gleiches Problem: Keine Validierung, dass die Pfade innerhalb des erwarteten Workspace liegen.

### 2.3 `paths.py`

```python
# paths.py — alle Pfade basieren auf Path.home() oder KBConfig
def get_default_db_path() -> Path:
    try:
        return KBConfig.get_instance().db_path
    except Exception:
        return Path.home() / ".openclaw" / "kb" / "library" / "biblio.db"
```

**Positiv:** Die Default-Pfade sind sicher (fest kodiert). Das Problem entsteht nur, wenn externe Inputs als `db_path`/`chroma_path` übergeben werden.

### 2.4 `HybridSearch.__init__()`

```python
# hybrid_search/engine.py:75-84
self.db_path = Path(db_path).expanduser()
self.chroma_path = Path(chroma_path)
```

Keine Validierung. Wenn `db_path` aus User-Input stammt, könnte beliebige SQLite-DB geöffnet werden.

**Risiko-Bewertung:**  
Aktuell **Mittel**, da die API voraussichtlich nur intern aufgerufen wird. Wenn eine Web/API-Schnittstelle dazukommt, wird dies zu **Hoch**.

---

## 3. Information Leakage — 🟡 MITTEL

### 3.1 Exception-Messages leaken Pfade

**Problematisch:** In Error-Messages werden absolute Dateipfade und ChromaDB-Pfade geloggt:

```python
# engine.py:111
logger.error(f"Cannot open database {self.db_path}: {e}. Keyword provider disabled.")

# engine.py:92
logger.warning(f"ChromaDB initialization failed: {e}")

# fts5_provider.py:61
logger.error(f"Cannot open database {self.db_path}: {e}. FTS5 search disabled.")

# embedding_pipeline.py:161
logger.error(f"Cannot open database {self.db_path}: {e}. Pipeline disabled.")
```

Diese Pfade werden auch in Custom Exceptions gespeichert:

```python
# chroma_provider.py:152-153
self._last_search_error = SearchError(f"ChromaDB search failed: {e}")
self._last_search_error.__cause__ = e  # Original-Exception mit Traceback!

# chroma_integration.py:422-424
self._last_delete_error = DatabaseError(f"ChromaDB delete failed: {e}")
self._last_delete_error.__cause__ = e
```

**Risiko:** Wenn Exceptions an Clients/APIs weitergegeben werden, könnten interne Pfade (`/home/user/...`) leaken.

### 3.2 `exceptions.py` — sicher

```python
class KBError(Exception):
    """Base exception for knowledge-base errors."""
    pass

class DatabaseError(KBError):
    """Database operation failed."""
    pass

class ChromaConnectionError(KBError):
    """ChromaDB connection/initialization error."""
    pass
```

✅ Keine `__str__`/`__repr__`-Overrides, die Pfade/Credentials exponieren würden.  
✅ Keine Credentials in Exception-Klassen.

### 3.3 Keine Credentials im Code

✅ Keine `password`, `secret`, `token`, `api_key` oder `credential`-Strings gefunden (bis auf NLTK-Token).  
✅ Kein `.env`-Hardcoding.

**Empfehlung:** Sanitize Error-Messages bevor sie an externe Clients gehen:

```python
def sanitize_path(path: str) -> str:
    """Replace home directory with ~ for logging."""
    return str(path).replace(str(Path.home()), "~")
```

---

## 4. Breite `except Exception` — 🟡 MITTEL

### Inventar: 35 Vorkommen

| Datei | Zeile | Kontext | Risiko |
|---|---|---|---|
| `hybrid_search/engine.py` | 91 | ChromaDB init | 🟢 OK — graceful degradation |
| `hybrid_search/engine.py` | 543 | ChromaDB stats | 🟢 OK — nicht kritisch |
| `batching.py` | 329 | Batch-Verarbeitung | 🟡 Prüft `on_error` |
| `batching.py` | 558 | Embedding-Fallback | 🟡 Verschluckt Fehler (zero vectors) |
| `fts5_setup.py` | 85 | FTS5-Check | 🟢 OK — Feature-Detection |
| `fts5_setup.py` | 130 | FTS5-Setup | 🔴 **Kritisch** — `conn.rollback()` könnte fehlschlagen |
| `fts5_setup.py` | 192 | FTS5-Rebuild | 🔴 **Kritisch** — `conn.rollback()` könnte fehlschlagen |
| `fts5_setup.py` | 222 | FTS5-Stats | 🟢 OK — nicht kritisch |
| `chunker.py` | 103 | NLTK-Tokenizer | 🟢 OK — graceful fallback |
| `chroma_integration.py` | 317 | Collection löschen | 🟡 Fehler wird verschluckt |
| `chroma_integration.py` | 422 | ChromaDB delete | 🟡 Speichert Fehler, aber Caller prüft nicht |
| `chroma_integration.py` | 621 | At-exit Cleanup | 🟢 OK — nicht kritisch |
| `providers/chroma_provider.py` | 65 | ChromaDB init | 🟢 OK — graceful degradation |
| `providers/chroma_provider.py` | 85 | Availability-Check | 🟢 OK |
| `providers/chroma_provider.py` | 151 | Search-Fehler | 🟡 Fehler nur geloggt, leake `e` in `SearchError` |
| `providers/fts5_provider.py` | 84 | FTS5-Check | 🟢 OK |
| `providers/fts5_provider.py` | 100 | Availability-Check | 🟢 OK |
| `providers/fts5_provider.py` | 163 | FTS5-Fallback | 🟢 OK — Fallback zu LIKE |
| `providers/fts5_provider.py` | 256 | LIKE-Fehler | 🟡 Leere Rückgabe verschluckt Fehler |
| `stopwords.py` | 115 | NLTK-Stopwords | 🟢 OK — graceful |
| `reranker.py` | 139 | Cross-Encoder | 🟡 Speichert Fehler, aber Caller ignoriert |
| `paths.py` | 23,32,41,50,59 | Config-Fallback | 🟢 OK — Fallback-Pfade |
| `embedding_pipeline.py` | 107 | ChromaDB init | 🟢 OK — graceful degradation |
| `embedding_pipeline.py` | 145 | Cache-Save | 🟡 Fehler verschluckt |
| `embedding_pipeline.py` | 281 | Batch-Embedding | 🟡 Speichert Fehler |
| `embedding_pipeline.py` | 464 | Batch-Fehler | 🟡 Loggt + fährt fort |
| `chroma_plugin.py` | 123 | ChromaDB init | 🟢 OK — graceful |
| `chroma_plugin.py` | 142 | Pipeline init | 🟢 OK — graceful |
| `chroma_plugin.py` | 249 | ChromaDB delete | 🟡 Fehler verschluckt |
| `chroma_plugin.py` | 338 | Batch-Embedding | 🟡 Fehler verschluckt |
| `chroma_plugin.py` | 370 | BG-Flush | 🔴 **Kritisch** — Fehler im Background-Thread verschluckt |

### Problematischste Fälle

#### 🔴 `chroma_plugin.py:370` — Background Flush Error
```python
def _bg_flush_worker(self) -> None:
    try:
        self.flush()
    except Exception as e:
        logger.error(f"Background flush error: {e}")
    finally:
        self._bg_running = False
```
**Problem:** Wenn `flush()` fehlschlägt, wird der Fehler nur geloggt. Der Caller hat keine Möglichkeit, den Fehler zu bemerken. Bei wiederholtem Stillstillstand keine Benachrichtigung.

#### 🔴 `fts5_setup.py:130,192` — FTS5 Setup/Rebuild
```python
except Exception as e:
    logger.error(f"FTS5 setup failed: {e}")
    conn.rollback()
    return False
```
**Problem:** `conn.rollback()` innerhalb von `except Exception` könnte selbst fehlschlagen (z.B. bei Connection-Verlust). Sollte `except` spezifischer sein oder `rollback` in eigenem `try/except`.

#### 🟡 `batching.py:558` — Zero-Vector Fallback
```python
except Exception as exc:
    # On embedding failure, add zero vectors as fallback
```
**Problem:** Bei Embedding-Fehlern werden Zero-Vectors eingefügt, die Suchergebnisse verfälschen. Kein Flag, dass die Vektoren ungültig sind.

**Empfehlung:** Die ~8 problematischen `except Exception` sollten spezifischer werden:
- `fts5_setup.py`: `except (sqlite3.OperationalError, sqlite3.DatabaseError)`
- `chroma_plugin.py:370`: Retry-Mechanismus + Error-Flag für Caller
- `batching.py:558`: Invalid-Vectors-Markierung in Metadata

---

## 5. Input Validation — 🔴 HOCH

### 5.1 File-Size Limits — KEINE

Es existieren **keine Limits für Dateigrößen** in der gesamten Codebase:

- `BiblioIndexer` indexiert beliebige Dateien ohne Größenbeschränkung
- `ChromaDBPlugin.on_file_indexed()` verarbeitet beliebige Section-Mengen
- `EmbeddingPipeline` hat kein Limit für einzelne Embedding-Texte
- Keine `MAX_FILE_SIZE`, `MAX_SECTION_SIZE`, oder `MAX_CONTENT_LENGTH` Konstanten

**Risiko:** Eine sehr große Datei (z.B. 500MB Markdown) könnte:
- Den Arbeitsspeicher erschöpfen (Section-Splitting)
- ChromaDB-Embedding zum Stillstand bringen
- SQLite-DB aufblähen

**Empfehlung:**
```python
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_SECTION_CONTENT = 100_000      # 100K chars per section
MAX_SECTIONS_PER_FILE = 1000       # Max sections per file
```

### 5.2 Batch-Size Limits — MINIMAL

```python
# chroma_plugin.py:83
batch_size: int = 32

# embedding_pipeline.py
batch_size = 32
```

Die Default-Werte sind vernünftig, aber es gibt **keine Validierung**:

```python
# chroma_plugin.py — keine Validierung
self.batch_size = batch_size  # Negativ? Null? 1000000?
```

**Risiko:** `batch_size=1` (ineffizient) oder `batch_size=100000` (OOM).

**Empfehlung:**
```python
self.batch_size = max(1, min(batch_size, 1000))  # Clamp to [1, 1000]
```

### 5.3 Query-Length Limits — KEINE

```python
# hybrid_search/engine.py:284
def search(self, query: str, ...):
    if not query or not query.strip():
        return []
    query = query.strip()
```

Kein Limit für `len(query)`. Ein sehr langer Query-String könnte:
- FTS5-MATCH-Syntax brechen
- ChromaDB-Embedding-Modell überlasten
- LIKE-Query-Explosion verursachen

**Empfehlung:**
```python
MAX_QUERY_LENGTH = 2000
if len(query) > MAX_QUERY_LENGTH:
    logger.warning(f"Query truncated: {len(query)} -> {MAX_QUERY_LENGTH}")
    query = query[:MAX_QUERY_LENGTH]
```

### 5.4 NLTK `pickle.load` — Niedriges Risiko

```python
# chunker.py:94
self._tokenizer = nltk.data.load('tokenizers/punkt_tab/german.pickle')
```

`nltk.data.load()` mit `.pickle`-Datei ist potenziell unsicher (Arbitrary Code Execution via Pickle). Da der Pfad aber fest kodiert ist (kein User-Input), ist das Risiko **minimal**. Eine zukünftige NLTK-Version sollte `json` oder `safetensors` verwenden.

---

## 6. Sonstige Befunde

### 6.1 Thread-Sicherheit — 🟡

```python
# chroma_plugin.py
self._queue: List[EmbeddingTask] = []
self._lock = threading.RLock()
```

`_processed_files` (Set) wird unter `self._lock` verwendet, aber `on_file_indexed()` führt SQLite-Queries **außerhalb** des Locks durch (Zeilen 155-170). Race Condition möglich, wenn dieselbe Datei zweimal gleichzeitig indexiert wird.

### 6.2 Connection-Leaks — 🟡

```python
# chroma_plugin.py:156
with sqlite3.connect(str(self.db_path)) as conn:
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT ... WHERE file_id = ?", (file_id,)).fetchall()
```

✅ Verwendet `with` — sauber.

Aber `hybrid_search/engine.py` verwaltet eine persistente Connection:

```python
# engine.py:128-132
@property
def db_conn(self) -> sqlite3.Connection:
    if self._db_conn is None:
        self._db_conn = sqlite3.connect(str(self.db_path))
```

Diese Connection wird nie explizit geschlossen (außer `close()`-Methode). Kein `__del__` oder Context-Manager.

### 6.3 FTS5 MATCH-Syntax — 🟢

Die FTS5-Query-Konstruktion in `keyword.py:186-191` ist sicher:
```python
terms = [t.strip().lower() for t in query.split() if len(t.strip()) > 1]
fts5_query_parts = []
for term in terms:
    if ' ' in term:
        fts5_query_parts.append(f'"{term}"')
    else:
        fts5_query_parts.append(term)
fts5_query = ' AND '.join(fts5_query_parts)
```

Da `query.split()` Terms isoliert, können FTS5-Operatoren (`OR`, `NOT`, `*`) nicht injiziert werden. Ein Query wie `"health OR NOT *"` wird zu `["health", "or", "not"]` → `"health AND or AND not"`, was FTS5 als Literal-Terms interpretiert.

**Aber:** Die Anführungszeichen für Multi-Word-Terms (`f'"{term}"'`) könnten theoretisch FTS5-Syntax injizieren, wenn der Input bereits Anführungszeichen enthält. Da die Terms aber durch `query.split()` isoliert werden (Leerzeichen als Delimiter), können keine Anführungszeichen in einem Term überleben. **Sicher.**

---

## Action Items

### 🔴 Hoch — Sofort

1. **Input-Validation: File-Size Limits**  
   `MAX_FILE_SIZE`, `MAX_SECTION_CONTENT`, `MAX_SECTIONS_PER_FILE` einführen  
   → `chunker.py`, `embedding_pipeline.py`

2. **Input-Validation: Batch-Size Clamping**  
   `batch_size = max(1, min(batch_size, 1000))`  
   → `chroma_plugin.py:83`, `embedding_pipeline.py`

3. **Input-Validation: Query-Length Limit**  
   `MAX_QUERY_LENGTH = 2000`, Truncate + Warnung  
   → `hybrid_search/engine.py:284`

### 🟡 Mittel — Nächster Sprint

4. **Path Traversal: Pfadvalidierung**  
   `_validate_path()` für `chroma_path`, `db_path`  
   → `chroma_integration.py`, `chroma_plugin.py`, `engine.py`

5. **Information Leakage: Pfad-Sanitizing in Logs**  
   `sanitize_path()` für Error-Messages  
   → Alle `logger.error(f"... {self.db_path} ...")` Stellen

6. **Breite `except Exception`:**  
   Spezifischere Exceptions für:
   - `fts5_setup.py:130,192` → `sqlite3.OperationalError`
   - `chroma_plugin.py:370` → Retry + Error-Flag
   - `batching.py:558` → Invalid-Vector-Markierung

### 🟢 Niedrig — Gelegentlich

7. **Thread-Sicherheit:** `on_file_indexed()` → DB-Query unter Lock
8. **Connection-Management:** `HybridSearch` → Context-Manager (`__enter__`/`__exit__`)
9. **NLTK Pickle:** Auf `punkt_tab` JSON-Format migrieren wenn möglich

---

## Fazit

Die Codebase hat **keine SQL-Injection-Schwachstellen** — alle Queries sind korrekt parametrisiert. Das ist hervorragend.

Die Hauptrisiken liegen in der **fehlenden Input-Validation** (File-Size, Batch-Size, Query-Length) und **fehlender Path-Traversal-Prävention**. Diese sind aktuell mittel-riskant, da die API intern verwendet wird, würden aber bei einer externen API-Schnittstelle zu **hohem Risiko** werden.

Die 35 `except Exception`-Blöcke sind überwiegend begründet (graceful degradation), aber ~8 sollten spezifischer sein, um Fehler nicht zu verschlucken.

**Gesamtbewertung: 🟡 MITTEL** — Keine kritischen Lücken, aber Input-Validation sollte prioritär ergänzt werden.