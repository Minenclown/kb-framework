# Phase 7: N+1 Queries Fixen

## Metadaten
- **Review-Datum:** 2026-04-27
- **Agent:** Softaware (Folge-Agent)
- **Status:** 📋 Zu erledigen

---

## Ausgangslage

| Metrik | Wert |
|--------|------|
| Bekannte N+1 Probleme | 18 |
| Kritische Issues | 3 |
| Betroffene Dateien | `keyword.py`, `filters.py` |

---

## Problem-Verständnis

### Was ist N+1?
```python
# SCHLECHT (N+1):
for item in items:
    result = db.query(f"SELECT * FROM tags WHERE id = {item.tag_id}")  # 1 + N queries

# GUT (JOIN):
results = db.query("SELECT * FROM items JOIN tags ON items.tag_id = tags.id")  # 1 query
```

### Warum ist es problematisch?
- 100 Zeilen = 101 Queries statt 1
- Latenz multipliziert sich
- DB-Load steigt dramatisch

---

## Betroffene Dateien analysieren

### 1. `kb/search/keyword.py`
```python
# Typisches N+1 Muster finden:
grep -n "for " kb/search/keyword.py
grep -n "\.get\|query\|filter" kb/search/keyword.py
```

### 2. `kb/search/filters.py`
```python
# Selbes Muster:
grep -n "for " kb/search/filters.py
grep -n "\.get\|query\|filter" kb/search/filters.py
```

---

## JOIN-Transformation (Beispiel)

### Vorher:
```python
def get_keywords_for_items(item_ids: list[int]):
    results = []
    for item_id in item_ids:
        # N+1: eine Query pro item
        keywords = db.execute(
            "SELECT * FROM keywords WHERE item_id = ?",
            (item_id,)
        )
        results.extend(keywords)
    return results
```

### Nachher:
```python
def get_keywords_for_items(item_ids: list[int]):
    if not item_ids:
        return []
    # JOIN: eine Query für alle
    placeholders = ",".join("?" * len(item_ids))
    keywords = db.execute(
        f"""
        SELECT k.* FROM keywords k
        WHERE k.item_id IN ({placeholders})
        """,
        item_ids
    )
    return keywords
```

---

## Konkrete Dateien zu prüfen

| Datei | Vermutetes Problem | Prüf-Methode |
|-------|-------------------|--------------|
| `kb/search/keyword.py` | Loop über item_ids | `grep -n "for item_id"` |
| `kb/search/filters.py` | Loop über results | `grep -n "for.*in.*filter"` |
| `kb/storage/chroma.py` | Fetch pro Dokument | `grep -n "for.*in.*docs"` |

---

## Schritt-für-Schritt für Softaware

### Phase 1: Identifizieren (30 min)
```bash
# N+1 Pattern in allen Python-Dateien finden:
grep -rn "for.*in.*:" kb/ --include="*.py" | head -30

# Dann prüfen ob im Loop DB-Zugriffe sind:
grep -B2 -A5 "for.*in.*:" kb/search/keyword.py
```

### Phase 2: Queries isolieren (20 min)
```python
# Debug-Logging hinzufügen:
import logging
logger = logging.getLogger(__name__)

def get_keywords_for_items(item_ids):
    logger.info(f"N+1 Check: fetching for {len(item_ids)} items")
    # ... restliche Logik
```

### Phase 3: JOIN schreiben (45 min)
```python
# Bulk-Query schreiben
# Achtung: bei sehr großen IN-Clauses (>1000) aufteilen
```

### Phase 4: Testen (30 min)
```bash
# Benchmark vorher/nachher:
python -c "
import time
from kb.search.keyword import get_keywords_for_items

# Test mit 100 Items
start = time.time()
result = get_keywords_for_items(range(100))
print(f'Time: {time.time() - start:.3f}s, Results: {len(result)}')
"
```

---

## Risiken & Mitigation

| Risiko | Mitigation |
|--------|------------|
| JOIN komplexer als erwartet | Erst mit einem Beispieltest |
| Query-Timeout bei großen Daten | Chunking wenn >1000 items |
| Breaking Changes | Erst bestehende Tests prüfen |

---

## Priorisierung

| Issue | Impact | Aufwand | Priorität |
|-------|--------|---------|----------|
| keyword.py N+1 | Hoch | Mittel | P1 |
| filters.py N+1 | Mittel | Mittel | P2 |
| chroma.py Fetch | Niedrig | Hoch | P3 |

---

## Checkliste für Softaware

- [ ] Alle N+1 Pattern in `keyword.py` identifiziert
- [ ] Alle N+1 Pattern in `filters.py` identifiziert  
- [ ] JOIN-Query geschrieben und getestet
- [ ] Benchmark: vorher/nachher verglichen
- [ ] Bestehende Tests bestehen
- [ ] Keine neuen N+1 eingeführt
