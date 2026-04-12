# ChromaDB Integration Plan
**Erstellt:** 2026-04-12 21:45 UTC  
**Status:** Zur Implementierung durch Softaware  
**Architektur:** Hub-and-Spoke (Orchestrator-Modus)

---

## Executive Summary

**Problem:** `BiblioIndexer.index_file()` schreibt NUR in SQLite. ChromaDB/Embedding ist komplett separiert und erfordert manuelles `reembed_all.py` nach jeder Indexierung.

**Lösung:** Integration von `EmbeddingPipeline` direkt in `BiblioIndexer` als optionales Post-Processing-Plugin, mit Callback-Hook-System für flexible ChromaDB-Updates.

---

## 1. Konzept

### Current State
```
index_file() → SQLite (nur)
                ↓
         [MANUELL]
                ↓
        reembed_all.py → ChromaDB
```

### Target State
```
index_file() → SQLite
                │
                ├──→ [Callback Hook] → ChromaDB (automatic)
                │
                └──→ [Optional] Silent ChromaDB Update (non-blocking)
```

### Architektur-Entscheidung: Callback-Hook-System

Statt ChromaDB direkt in `index_file()` einzubauen (tight coupling), nutzen wir ein **Plugin-System**:

```python
class IndexingPlugin:
    """Base class für Post-Indexierung Plugins."""
    def on_file_indexed(self, file_path: Path, sections: int) -> None:
        """Wird nach erfolgreicher Indexierung aufgerufen."""
        pass

class ChromaDBPlugin(IndexingPlugin):
    """Chromadb-Embedding als Plugin."""
    def on_file_indexed(self, file_path: Path, sections: int) -> None:
        # Queue für Background-Embedding
        pass
```

**Vorteile:**
- Loose coupling
- Toggle ChromaDB on/off ohne Code-Änderung
- Testbar ohne ChromaDB
- Erweiterbar für zukünftige Plugins (z.B. Elasticsearch, etc.)

---

## 2. Architektur-Änderungen

### Phase A: Plugin-System in BiblioIndexer

**Datei:** `kb/indexer.py`

```python
class IndexingPlugin(ABC):
    """Abstract Base Class für Indexing-Plugins."""
    @abstractmethod
    def on_file_indexed(self, file_path: Path, sections: int, file_id: str) -> None:
        """Callback nach erfolgreicher Indexierung einer Datei."""
        pass

    @abstractmethod
    def on_file_removed(self, file_path: Path) -> None:
        """Callback nach Entfernung einer Datei aus dem Index."""
        pass

class BiblioIndexer:
    def __init__(self, db_path: str, plugins: List[IndexingPlugin] = None):
        self.plugins = plugins or []

    def index_file(self, file_path: Path) -> int:
        # ... existierender Code ...
        
        # Callback für alle Plugins
        for plugin in self.plugins:
            try:
                plugin.on_file_indexed(file_path, len(sections), file_id)
            except Exception as e:
                logger.warning(f"Plugin {plugin.__class__.__name__} failed: {e}")
        
        return len(sections)
```

### Phase B: ChromaDBPlugin Implementation

**Neue Datei:** `kb/library/knowledge_base/chroma_plugin.py`

```python
class ChromaDBPlugin(IndexingPlugin):
    """
    ChromaDB-Embedding Plugin für BiblioIndexer.
    
    Nutzt Background-Queue für non-blocking Embedding.
    """
    
    def __init__(
        self,
        db_path: str,
        chroma_path: str = "~/.knowledge/chroma_db",
        batch_size: int = 32,
        enabled: bool = True
    ):
        self.db_path = db_path
        self.chroma_path = Path(chroma_path).expanduser()
        self.batch_size = batch_size
        self.enabled = enabled
        self._queue: List[str] = []  # section_ids
        self._pending_files: Set[str] = set()
        
    def on_file_indexed(self, file_path: Path, sections: int, file_id: str) -> None:
        """Queue alle Sections einer frisch indexierten Datei für Embedding."""
        if not self.enabled:
            return
            
        self._pending_files.add(file_id)
        
        # Hole alle section_ids für diese file_id
        conn = sqlite3.connect(self.db_path)
        section_ids = [
            row[0] for row in conn.execute(
                "SELECT id FROM file_sections WHERE file_id = ?", (file_id,)
            ).fetchall()
        ]
        conn.close()
        
        self._queue.extend(section_ids)
        
    def on_file_removed(self, file_path: Path) -> None:
        """Entferne Sections aus ChromaDB wenn Datei gelöscht wird."""
        # Implementierung für ChromaDB Cleanup
        
    def flush(self) -> int:
        """
        Verarbeitet die Queue und schreibt nach ChromaDB.
        
        Returns:
            Anzahl verarbeiteter Sections
        """
        if not self._queue:
            return 0
            
        pipeline = EmbeddingPipeline(
            db_path=self.db_path,
            chroma_path=str(self.chroma_path),
            batch_size=self.batch_size
        )
        
        # Process queued sections
        processed = 0
        while self._queue:
            batch = self._queue[:self.batch_size]
            self._queue = self._queue[self.batch_size:]
            
            # Hier spezifische Sections aus DB holen und embedden
            # ...
            processed += len(batch)
            
        return processed
```

### Phase C: Hybrid Search Update

**Datei:** `kb/library/knowledge_base/hybrid_search.py`

```python
def search_with_chroma(query: str, n_results: int = 10) -> List[dict]:
    """
    Hybrid Search: ChromaDB Vector + SQLite Metadata.
    
    1. Query-Embedding via ChromaDB
    2. Metadata-Enrichment via SQLite
    3. Combined Results
    """
    chroma = get_chroma()
    query_emb = chroma.embed_text(query)
    
    collection = chroma.sections_collection
    results = collection.query(
        query_embeddings=[query_emb],
        n_results=n_results
    )
    
    # Enrich mit SQLite Metadata
    # ...
```

---

## 3. Workflows

### Workflow A: Index → ChromaDB Automatic (mit Plugin)

```python
# Usage Example
with BiblioIndexer("knowledge.db", plugins=[ChromaDBPlugin()]) as indexer:
    indexer.index_file(Path("test.md"))
    # → SQLite + ChromaDB (automatic)
    
    # Am Ende: Queue flushen
    indexer.plugins[0].flush()
```

### Workflow B: Background-Processing

```python
# Non-blocking: Indexing läuft, ChromaDB kommt später
indexer = BiblioIndexer("knowledge.db", plugins=[ChromaDBPlugin()])

# 100 Dateien indexieren
indexer.index_directory("projektplanung/")

# Später: Embedding verarbeiten
indexer.plugins[0].flush()  # Oder via CronJob
```

### Workflow C: Incremental Update

```python
# Check and Update mit ChromaDB-Sync
indexer = BiblioIndexer("knowledge.db", plugins=[ChromaDBPlugin()])
indexer.check_and_update(["/path/to/watch"])

# Nur geänderte Dateien → nur geänderte Sections in ChromaDB
```

---

## 4. Implementierungs-Phasen

### Phase 1: Core Plugin System
**Aufwand:** ~1 Stunde  
**Verantwortlich:** Softaware

- [ ] `IndexingPlugin` ABC in `kb/indexer.py` definieren
- [ ] `BiblioIndexer` um `plugins`-Parameter erweitern
- [ ] `on_file_indexed()` Callback in `index_file()` integrieren
- [ ] `on_file_removed()` Callback in `remove_file()` integrieren
- [ ] Unit Tests für Plugin-System

### Phase 2: ChromaDBPlugin
**Aufwand:** ~2 Stunden  
**Verantwortlich:** Softaware

- [ ] `ChromaDBPlugin` Klasse in neuer Datei `kb/library/knowledge_base/chroma_plugin.py`
- [ ] `flush()` Methode implementieren
- [ ] Queue-basiertes Batch-Processing
- [ ] Error Handling und Logging
- [ ] Toggle `enabled` Flag

### Phase 3: Background Queue (Optional)
**Aufwand:** ~2 Stunden  
**Verantwortlich:** Softaware

- [ ] `threading.Thread` für non-blocking embedding
- [ ] `flush_async()` Methode
- [ ] Queue-Persistenz für Crash-Recovery (JSON-Datei)

### Phase 4: Hybrid Search Integration
**Aufwand:** ~1 Stunde  
**Verantwortlich:** Softaware

- [ ] `search_with_chroma()` in `hybrid_search.py`
- [ ] Metadata-Enrichment von SQLite
- [ ] Combined Result Ranking

### Phase 5: Documentation & Cleanup
**Aufwand:** ~1 Stunde  
**Verantwortlich:** Sir Stern

- [ ] `reembed_all.py` Workflow dokumentieren
- [ ] `INSTALLATION_GUIDE.md` korrigieren (richtiger Inhalt)
- [ ] `install.sh` Pfad-Fehler beheben (`kb_framework/` → `kb-framework/`)
- [ ] Leere Ordner aufräumen oder entfernen

---

## 5. Zeitplan

| Phase | Beschreibung | Aufwand | Summe |
|-------|-------------|---------|-------|
| 1 | Core Plugin System | 1h | 1h |
| 2 | ChromaDBPlugin | 2h | 3h |
| 3 | Background Queue | 2h | 5h |
| 4 | Hybrid Search | 1h | 6h |
| 5 | Docs & Cleanup | 1h | 7h |
| **Total** | | **7h** | |

**Empfohlene Reihenfolge:** Phase 1 → 2 → 3 → 4 → 5

---

## 6. Risiken

### Risk 1: Blocking during embedding
**Severity:** 🟠 MEDIUM  
**Description:** `flush()` könnte bei vielen Sections blockieren  
**Mitigation:** Background-Thread + Batch-Size Limit (32)

### Risk 2: ChromaDB unavailable
**Severity:** 🟡 LOW  
**Description:** ChromaDB nicht erreichbar → Plugin-Fehler  
**Mitigation:** Graceful degradation, try/except, `enabled=False` Toggle

### Risk 3: Duplicate embeddings
**Severity:** 🟡 LOW  
**Description:** Gleiche Section mehrfach in Queue  
**Mitigation:** Deduplizierung in `flush()` via Set

### Risk 4: Cache invalidation
**Severity:** 🟠 MEDIUM  
**Description:** File geändert aber altes ChromaDB-Embedding noch da  
**Mitigation:** `on_file_indexed` löscht alte Entries via Upsert (ChromaDB Behaviour)

### Risk 5: Memory bei großen Batches
**Severity:** 🟡 LOW  
**Description:** 10k+ Sections → Batch-Embedding braucht RAM  
**Mitigation:** Batch-Size Limit + Generator-basiertes Processing

---

## 7. Alternativen

### Alternative A: Sync-Embedding in index_file()
**Pro:** Einfach, keine Queue  
**Con:** Blocking, langsam bei vielen Sections, tight coupling

### Alternative B: External Worker (Celery/RQ)
**Pro:** Production-grade async, resilient  
**Con:** Overhead (Redis), zu komplex für diesen Use-Case

### Alternative C: nur SQLite, ChromaDB nur auf Anfrage
**Pro:** Keine Änderung nötig  
**Con:** User muss manuell reembedden

**Empfehlung:** Plugin-System ( Current Plan) bietet beste Balance.

---

## 8. Files to Modify

| File | Action | Lines |
|------|--------|-------|
| `kb/indexer.py` | Modify: Add Plugin-ABC, extend BiblioIndexer | ~50 |
| `kb/library/knowledge_base/chroma_plugin.py` | Create: ChromaDBPlugin class | ~150 |
| `kb/library/knowledge_base/hybrid_search.py` | Modify: Add `search_with_chroma()` | ~30 |
| `INSTALLATION_GUIDE.md` | Replace: Wrong content with correct install guide | ~100 |
| `install.sh` | Fix: `kb_framework/` → `kb-framework/` | 1 line |

---

## 9. Test Strategy

```python
# Test Plugin System
def test_plugin_callback():
    class TestPlugin(IndexingPlugin):
        called = False
        def on_file_indexed(self, path, sections, file_id):
            self.called = True
    
    plugin = TestPlugin()
    indexer = BiblioIndexer("test.db", plugins=[plugin])
    indexer.index_file(Path("test.md"))
    
    assert plugin.called

# Test ChromaDBPlugin non-blocking
def test_chroma_plugin_queue():
    plugin = ChromaDBPlugin(db_path="test.db", enabled=True)
    plugin.on_file_indexed(Path("test.md"), 5, "file-123")
    
    assert len(plugin._queue) == 5
```

---

## 10. Success Criteria

- [ ] `index_file()` → SQLite + ChromaDB automatic (mit Plugin)
- [ ] Non-blocking Embedding (Background-Thread)
- [ ] Graceful degradation wenn ChromaDB unavailable
- [ ] `INSTALLATION_GUIDE.md` enthält korrekte Installationsanleitung
- [ ] `install.sh` funktioniert mit korrektem Pfad
- [ ] Alle Tests passen

---

**Nächste Schritte für Softaware:**
1. Phase 1 implementieren (Plugin-ABC + BiblioIndexer-Erweiterung)
2. Review mit Sir Stern
3. Phase 2 implementieren (ChromaDBPlugin)
