# KB-Framework Review — Phase 7: Performance

**Datum:** 2026-04-26  
**Reviewer:** Sir Stern 🔍  
**Scope:** Algorithmische Komplexität, Datenbank-Queries, Memory-Nutzung, Embedding-Batching

---

## Zusammenfassung

Das Framework zeigt eine **gute Batch-Infrastruktur** (`batching.py`) mit dedizierten Utilities für ChromaDB-Upserts, SQLite-Executemany und Embedding-Batches. Es gibt jedoch **konkrete Performance-Probleme** in der Such-Pipeline: eager Materialisierung, N+1-Queries, fehlende Prepared Statements und ein naives LRU-Cache-Design. Der Embedding-Pipeline ist gut strukturiert, aber bei großen Datensätzen gibt es Memory-Risiken.

---

## Ergebnisse im Detail

| # | Datei | Problem | Impact | Empfohlener Fix | Aufwand |
|---|-------|---------|--------|------------------|---------|
| 1 | `hybrid_search/keyword.py:126` | `fetchall()` lädt alle FTS5-Ergebnisse sofort in RAM | **Hoch** — Bei großen Ergebnislisten (z.B. `limit=1000`) wird alles auf einmal materialisiert, obwohl es danach nur iteriert wird | Iterator-basierte Verarbeitung mit `cursor` statt `fetchall()`, oder `yield` pro Zeile | S |
| 2 | `hybrid_search/keyword.py:224-243` | N+1 Query: Pro LIKE-Ergebnis wird `file_path` in einem **separaten SELECT** abgefragt | **Mittel-Hoch** — Bei 100 Ergebnissen → 101 SQL-Queries statt 1 JOIN | JOIN mit `files`-Tabelle in der Hauptquery, analog zu FTS5-Query | S |
| 3 | `hybrid_search/keyword.py:92-135` | FTS5-Check bei **jedem Suchaufruf** (`is_available()` oder direkter `sqlite_master`-Query) | **Mittel** — Overhead pro Query, obwohl sich FTS5-Verfügbarkeit nie ändert | Verfügbarkeit beim `HybridSearch.__init__()` einmalig prüfen und cachen (wird bereits in `HybridSearch._fts5_available` gemacht, aber `_keyword_search_fts` nutzt es nicht konsistent) | S |
| 4 | `hybrid_search/engine.py:102-104, 367-377` | Naiver Dict-basierter LRU-Cache: `next(iter(self._query_cache))` zum Finden des ältesten Eintrags | **Mittel** — `next(iter(dict))` ist O(1) seit Python 3.7+, aber es gibt keine TTL-Invalidierung und die Cache-Größe (100) ist sehr klein. Cache-Eviction löscht immer nur 1 Eintrag pro Überlauf | `functools.lru_cache` oder `cachetools.TTLCache` mit konfigurierbarer TTL und max-size; Batch-Eviction statt 1-pro-Überlauf | S |
| 5 | `hybrid_search/engine.py:243-247` | `_merge_and_rank` berechnet `max()` über alle scores für Normalisierung, dann iteriert erneut | **Niedrig** — Zwei Durchläufe über `result_map.values()`, aber bei typischen `final_limit=20` irrelevant | Single-Pass mit laufendem `max_semantic`/`max_keyword` Tracking, oder Normalisierung entfernen wenn Scores schon vergleichbar | S |
| 6 | `hybrid_search/engine.py:274-291` | `rerank_results` konvertiert `SearchResult` → `dict` → Reranker → zurück zu `SearchResult` | **Mittel** — Doppelte Kopie von allen Feldern pro Ergebnis. Bei 20 Ergebnissen harmlos, aber unnötiger Overhead | Reranker direkt mit `SearchResult` arbeiten lassen, oder `dataclasses.asdict()` nutzen | S |
| 7 | `hybrid_search/filters.py:78-118` | `search_with_filters` fragt **3× mehr Ergebnisse** ab (`limit * 3`) und filtert danach | **Mittel-Hoch** — Verdrehter Overhead auf ChromaDB + FTS5, besonders bei teuren Embedding-Queries | Filter-Parameter als `where`-Clause in ChromaDB-Query übergeben (ChromaDB unterstützt Metadata-Filter); FTS5 mit `WHERE`-Subselect | M |
| 8 | `hybrid_search/filters.py:91-107` | **N+1 Query im Date-Filter**: Pro Ergebnis wird `last_modified` einzeln aus DB abgefragt | **Hoch** — Bei 60 Ergebnissen (20 * 3) → 60+ extra SQL-Queries | Batch-Query mit `IN (...)` für alle `file_id`s oder JOIN im Haupt-Query | S |
| 9 | `chroma_integration.py:170, 190` | `embed_text()` und `embed_batch()` rufen `.tolist()` auf → konvertiert numpy-Array in Python-Liste, was Memory fast verdoppelt | **Mittel** — Bei 16k Embeddings à 384 floats = ~25MB raw, ~50MB als Python-Liste. Für kleine Batches harmlos, bei `embed_batch` mit 16k Texten problematisch | Numpy-Arrays bis zum finalen Upsert behalten, `.tolist()` erst bei ChromaDB-Übergabe | M |
| 10 | `embedding_pipeline.py:427` | `list(self.get_sections_for_embedding(...))` materialisiert den Generator komplett in RAM | **Hoch** — Bei 16.626 Sections wird die gesamte Liste auf einmal erzeugt, obwohl `batched()` den Generator ohnehin in Chunks verarbeiten würde | Generator direkt an `batched()` übergeben, `len()` über SQL-Count-Query vorab ermitteln | S |
| 11 | `embedding_pipeline.py:120` | `get_embedding_hash()` serialisiert Embedding-Vektor als JSON-String für SHA256 — extrem teuer | **Niedrig** — Wird nur in Pipeline-Run aufgerufen, nicht im Such-Pfad. Aber ineffizient | Numpy `tobytes()` + `hashlib.sha256` statt `json.dumps()` + encode | S |
| 12 | `embedding_pipeline.py:268-269` | Batch-Embedding in `embed()` erzeugt alle Embeddings auf einmal | **Mittel** — Bei `batch_size=32` harmlos, aber die `batched()`-Logik im `run_full()` splittet bereits. Doppeltes Batching | Embed-batch-size in `embed()` auf `min(len(sections), batch_size)` begrenzen oder die outer-batch-Größe als innere batch_size nutzen | S |
| 13 | `chroma_integration.py:377-419` | `delete_by_file_id` nutzt `collection.get(where=...)` → lädt alle Metadaten + Embeddings des file_id in RAM | **Mittel** — ChromaDB hat keinen DELETE-WHERE, aber `.get()` kann bei großen Collections Memory-drückend sein | ChromaDB's `get()` mit `include=["metadatas"]` statt default (inkl. embeddings), dann nur IDs für `delete()` nutzen | S |
| 14 | `fts5_setup.py:148-182` | `rebuild_fts5_index` iteriert zeilenweise `INSERT` statt `executemany()` | **Hoch** — Bei 16k Zeilen: 16k einzelne INSERTs statt ~16 Batch-Inserts | `executemany()` oder `batched_executemany()` aus `batching.py` nutzen (ist bereits vorhanden!) | S |
| 15 | `providers/fts5_provider.py:126-161` | FTS5-Query: row-by-key Zugriff (`row["section_id"]`) statt positioneller Tupel-Zuordnung | **Niedrig** — Leichter Overhead durch `Row`-Dictionary-Zugriff, aber SQLite's `row_factory = sqlite3.Row` ermöglicht beides | Positionellen Zugriff nutzen oder `row_factory` auf `None` setzen für FTS5-Queries | S |
| 16 | `reranker.py:120-141` | Cross-Encoder `model.predict(pairs)` verarbeitet alle Paare auf einmal | **Mittel** — Bei 20 Paaren OK, aber `rerank()` hat keinen Batch-Schutz. Bei versehentlich großen Ergebnislisten → OOM oder Timeout | `top_k`-Limit vorm `predict()` anwenden (nur top_k Paare scorieren), nicht erst danach | S |
| 17 | `hybrid_search/engine.py:561-567` | `get_stats()` führt 2 separate `COUNT(*)`-Queries aus | **Niedrig** — Zwei schnelle Aggregationen, aber unnötig | Einzel-Query mit Subselects oder `UNION ALL` | S |
| 18 | `hybrid_search/engine.py:38-42` | Mehrere Module werden bei Import geladen: `chromadb`, `sentence_transformers` | **Mittel** — ChromaDB + sentence-transformers sind schwere Libraries. Lazy-Import wäre besser | ChromaDB/SentenceTransformer nur in den Functions importieren, die sie brauchen (teilweise bereits lazy via `@property`, aber Module-Level-Import in `__init__.py` lädt alles) | M |

---

## Performance-Profils nach Kategorie

### 1. Algorithmische Komplexität

| Muster | Fundstelle | Bewertung |
|--------|-----------|-----------|
| Verschachtelte Schleifen | Keine `for.*for`-Muster gefunden | ✅ Gut |
| O(n²) Patterns | Keine O(n²)-Algorithmen gefunden | ✅ Gut |
| Normalisierung in `_merge_and_rank` | 2 Durchläufe → O(n), nicht O(n²) | ✅ Akzeptabel |
| ChromaDB-Query-Caching | Dict-Cache mit max 100 Einträgen, keine TTL | ⚠️ Verbesserbar |

### 2. Datenbank-Queries

| Problem | Fundstelle | Schwere |
|---------|-----------|---------|
| N+1: `file_path` pro Zeile | `keyword.py:243` | 🔴 Hoch |
| N+1: `last_modified` pro Zeile | `filters.py:91` | 🔴 Hoch |
| Zeilenweiser INSERT | `fts5_setup.py:178` | 🔴 Hoch |
| Keine Prepared Statements | `fts5_provider.py:161` | 🟡 Mittel |
| FTS5-Check pro Query | `keyword.py:74` | 🟡 Mittel |

### 3. Memory-Nutzung

| Problem | Fundstelle | Schwere |
|---------|-----------|---------|
| `list()` materialisiert Generator | `embedding_pipeline.py:427` | 🔴 Hoch |
| `fetchall()` statt Iterator | `keyword.py:126` | 🟡 Mittel |
| `.tolist()` verdoppelt Memory | `chroma_integration.py:170` | 🟡 Mittel |
| `embed_batch()` lädt alle Embeddings | `batching.py:553-561` sammelt in `all_embeddings` | 🟡 Mittel |
| ChromaDB `.get()` lädt Embeddings | `chroma_integration.py:397` | 🟡 Mittel |

### 4. Embedding-Batching

| Parameter | Wert | Bewertung |
|-----------|------|-----------|
| Min. Batch-Size | `batch_size=32` (Default in `ChromaIntegration.embed_batch`) | ✅ Gut — Sentence-Transformers empfiehlt 32-128 |
| Max. Batch-Size | Kein Limit, `batched_chroma_upsert` Default 500 | ✅ Gut — 500 ist konservativ |
| Embedding-Pipeline Batch | `batch_size=32` in `EmbeddingPipeline.__init__` | ✅ Gut — Memory-freundlich |
| `batched()` Generator | Effizient, yielded Listen | ✅ Gut |
| `batch_process()` Error-Toleranz | Fährt bei Fehlern fort | ✅ Gut |
| Overhead pro Batch | 1 Embed-Call + 1 ChromaDB-Upsert pro Batch | ✅ Akzeptabel |

---

## Top 5 Empfehlungen (nach Impact × Aufwand)

1. **🥇 N+1-Queries eliminieren** (`keyword.py:243`, `filters.py:91`)  
   *Aufwand: S, Impact: Hoch* — JOIN statt Einzel-Queries. Spart bei 100+ Ergebnissen hunderte SQL-Roundtrips.

2. **🥈 Generator statt `list()` in Pipeline** (`embedding_pipeline.py:427`)  
   *Aufwand: S, Impact: Hoch* — Sections als Generator an `batched()` übergeben, `len()` via `SELECT COUNT(*)`.

3. **🥉 FTS5-Rebuild mit `executemany()`** (`fts5_setup.py:148-182`)  
   *Aufwand: S, Impact: Hoch* — Das `batched_executemany()` aus `batching.py` ist bereits vorhanden, nur nutzen!

4. **🏅 TTL-Cache statt Dict** (`engine.py:102-104`)  
   *Aufwand: S, Impact: Mittel* — `cachetools.TTLCache` mit konfigurierbarer TTL und maxSize.

5. **🏅 Reranker top_k vor predict()** (`reranker.py:120`)  
   *Aufwand: S, Impact: Mittel* — Nur die Top-K Paare an Cross-Encoder senden, nicht alle.

---

## Positive Befunde

- **Batch-Infrastruktur** (`batching.py`) ist hervorragend: `batched()`, `BatchProgress`, `BatchResult`, `batch_process()`, `batched_chroma_upsert()`, `batched_executemany()`, `embed_in_batches()` — alles vorhanden und gut dokumentiert
- **Singleton-Pattern** für ChromaDB und HybridSearch mit Thread-Safety (RLock)
- **Error-Toleranz**: `batch_process()` fährt bei Fehlern fort, einzelne Batches können fehlschlagen
- **Lazy Loading**: Model-Loading in Properties (`model`, `client`), V2-Model on-demand
- **ChromaDB-Batching**: Upserts und Deletes in konfigurierbaren Batches (500/1000)
- **`batched()` als Generator**: Memory-freundlich, erzeugt Listen nur pro Chunk

---

## Fazit

Die Batch-Infrastruktur ist **solide und gut durchdacht**. Die Hauptprobleme liegen nicht im Batch-System, sondern in der **Such-Pipeline**: N+1-Queries, Generator-Materialisierung und fehlende TTL-basierte Cache-Invalidierung. Diese Fixes sind einfach (meist JOIN statt Einzel-Query), haben aber hohen Impact auf Latenz und Memory bei großen Datensätzen.

**Gesamtbewertung: 7/10** — Gut strukturiert, aber mit klaren Low-Hanging-Fruits für Performance-Verbesserungen.