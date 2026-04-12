# Fix-Plan: ChromaDB Integration Bugs
**Erstellt:** 2026-04-12
**Für:** Softaware
**Quelle:** Sir Stern Audit

---

## Übersicht

| Priorität | Bug | Datei | Aufwand |
|-----------|-----|-------|---------|
| 🔴 Kritisch | ChromaDB Orphan Entries | `kb/indexer.py` | 30 min |
| 🔴 Kritisch | Connection Leak | `kb/library/knowledge_base/chroma_plugin.py` | 15 min |
| 🟠 Mittel | Ineffizientes batch.index() | `kb/library/knowledge_base/chroma_plugin.py` | 20 min |
| 🟢 Niedrig | Falsches pip-Paket | `install.sh` | 5 min |

---

## 🔴 Bug 1: ChromaDB Orphan Entries

**Datei:** `kb/indexer.py` (~Zeile 210)

**Problem:**
```python
def on_file_removed(self, file_path: Path) -> None:
    # ChromaDB löscht automatisch via upsert wenn die section nicht mehr in DB
    # Optional: explizit löschen wenn nötig
    logger.debug(f"File removed: {file_path} (ChromaDB will be updated on next embed)")
```
→ Kommentar vs. Realität: ChromaDB löscht **nichts** automatisch.

**Fix:**
```python
def on_file_removed(self, file_path: Path) -> None:
    """
    Callback nach Entfernung einer Datei aus dem Index.

    Entfernt zugehörige Entries aus ChromaDB.

    Args:
        file_path: Pfad der entfernten Datei
    """
    if not self.enabled:
        return

    try:
        # Hole alle file_ids für diesen Pfad
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id FROM files WHERE file_path = ?", (str(file_path),)
        ).fetchall()
        conn.close()

        if not rows:
            return

        file_ids = [row['id'] for row in rows]

        # Lösche aus ChromaDB
        if self.chroma:
            for file_id in file_ids:
                self.chroma.delete_by_file_id(file_id)
            logger.info(f"ChromaDB entries removed for: {file_path}")
        else:
            logger.warning("ChromaDB not available, orphan entries may remain")

    except Exception as e:
        logger.error(f"Error removing ChromaDB entries for {file_path}: {e}")
```

**Voraussetzung:** `ChromaIntegration` braucht eine `delete_by_file_id(file_id)` Methode.

**Aufwand:** 30 min + ggf. 20 min für ChromaIntegration-Methode
**Risiko:** Mittel - kein Test vorhanden

---

## 🟡 Ergänzung: ChromaIntegration.delete_by_file_id()

**Datei:** `kb/library/knowledge_base/chroma_integration.py`

Falls die Methode noch nicht existiert, muss sie hinzugefügt werden:

```python
def delete_by_file_id(self, file_id: str) -> int:
    """
    Löscht alle Embeddings für eine file_id aus ChromaDB.
    
    Args:
        file_id: UUID der Datei
        
    Returns:
        Anzahl der gelöschten Einträge
    """
    try:
        collection = self.get_collection(self.collection_name)
        # ChromaDB speichert file_id als Metadatum
        # Lösche alle Entries wo file_id = ?
        # 
        # Hinweis: ChromaDB unterstützt kein DELETE mit WHERE
        # Lösung: Query alle IDs mit passender file_id, dann delete_by_ids()
        
        return 0  # Placeholder
    except Exception as e:
        logger.error(f"Error deleting from ChromaDB for file_id {file_id}: {e}")
        return 0
```

**Hinweis:** ChromaDB hat keine direkte DELETE WHERE Klausel. Lösung via `get()` + `delete_by_ids()`.

---

## 🔴 Bug 2: Connection Leak

**Datei:** `kb/library/knowledge_base/chroma_plugin.py` (~Zeile 98)

**Problem:**
```python
def on_file_indexed(self, file_path: Path, sections: int, file_id: str) -> None:
    # ...
    try:
        conn = sqlite3.connect(str(self.db_path))
        # ... arbeit mit conn ...
        # conn.close() fehlt bei Exception!
    except Exception as e:
        logger.error(f"Error queuing sections for {file_path}: {e}")
        # ← Hier Leak: conn bleibt offen
```

**Fix:** Context Manager nutzen:
```python
try:
    with sqlite3.connect(str(self.db_path)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT id, file_id, file_path, section_header,
                   content_full, content_preview, section_level, keywords
            FROM file_sections
            WHERE file_id = ?
        """, (file_id,)).fetchall()

        # ... restlicher Code ...

except Exception as e:
    logger.error(f"Error queuing sections for {file_path}: {e}")
```

**Aufwand:** 15 min
**Risiko:** Niedrig - bewährtes Pattern

---

## 🟠 Bug 3: Ineffizientes batch.index()

**Datei:** `kb/library/knowledge_base/chroma_plugin.py` (~Zeile 198)

**Problem:** O(n) Lookups bei jedem `batch.index(EmbeddingTask(...))`

**Aktueller Code (vermutlich):**
```python
for task in tasks:
    batch.index(EmbeddingTask(...))  # O(n) pro Item
```

**Soll:** Index-basiert mit `enumerate`:
```python
for idx, task in enumerate(tasks):
    batch.index(EmbeddingTask(
        idx=idx,  # Index statt Lookup
        ...
    ))
```

**Aufwand:** 20 min
**Risiko:** Niedrig - Algorithmus-Optimierung

**Hinweis:** Code-Stelle muss direkt inspiziert werden. Zeile ~198 im Original.

---

## 🟢 Bug 4: Falsches pip-Paket

**Datei:** `install.sh` (~Zeile 30)

**Problem:**
```bash
pip install pypdf --quiet  # FALSCH
```

**Fix:**
```bash
pip install PyMuPDF --quiet  # RICHTIG
```

**Aufwand:** 5 min
**Risiko:** Keins

---

## Reihenfolge

1. **Bug 4** → Quick Win, keine Abhängigkeiten
2. **Bug 2** → Connection Leak beheben
3. **Bug 1** → ChromaDB Integration prüfen (evtl. `delete_by_file_id` hinzufügen)
4. **Bug 3** → Letzter Schritt, muss Code-Stelle lokalisiert werden

---

## Getestet?

| Bug | Test vorhanden? | Empfehlung |
|-----|-----------------|------------|
| 1 | Nein | Manuell testen: Datei indexieren → löschen → ChromaDB prüfen |
| 2 | Nein | Manuell testen: Exception during indexing → Connection prüfen |
| 3 | Nein | Code-Stelle lokaliseren |
| 4 | N/A | pip list \| grep -i pymupdf |

---

## Files to Modify

1. `install.sh` - Zeile 30: `pypdf` → `PyMuPDF`
2. `kb/library/knowledge_base/chroma_plugin.py` - Zeile ~155: Context Manager
3. `kb/library/knowledge_base/chroma_plugin.py` - Zeile ~198: Index-basiert
4. `kb/indexer.py` - Zeile ~210: `on_file_removed` implementieren

**ChromaIntegration Update (falls delete_by_file_id fehlt):**
- `kb/library/knowledge_base/chroma_integration.py` - Neue Methode `delete_by_file_id()`
