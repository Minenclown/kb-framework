# Phase 3: SQLite Resource Management

## Context
Mehrere Scripts schließen SQLite Connections nicht korrekt im `finally`-Block.
Connection Leaks können bei langlaufenden Prozessen auftreten.

## Files
- `kb/scripts/reembed_all.py:55`
- `kb/scripts/kb_ghost_scanner.py:70`
- `kb/scripts/sync_chroma.py:114`

## Problem
```python
# PROBLEMATISCH - Connection könnte nicht geschlossen werden bei Exception
conn = sqlite3.connect(db_path)
cursor.execute("...")
conn.close()

# KORREKT - try-finally
conn = sqlite3.connect(db_path)
try:
    cursor.execute("...")
finally:
    conn.close()
```

## Steps

### 1. reembed_all.py
```bash
# Zeile ~55 finden
rg -n "sqlite3.connect" kb/scripts/reembed_all.py

# Pattern anwenden:
# conn = sqlite3.connect(...)
# try:
#     ... work ...
# finally:
#     conn.close()
```

### 2. kb_ghost_scanner.py
```bash
rg -n "sqlite3.connect" kb/scripts/kb_ghost_scanner.py

# try-finally wrapper hinzufügen
```

### 3. sync_chroma.py
```bash
rg -n "sqlite3.connect" kb/scripts/sync_chroma.py

# try-finally wrapper hinzufügen
```

## Verification
```python
# Prüfe ob alle Connections in try-finally sind
rg -A2 "sqlite3.connect" kb/scripts/*.py | rg -B1 "finally"
# Sollte Treffer zeigen
```

## Rollback
```bash
cd ~/projects/kb-framework && git checkout kb/scripts/reembed_all.py kb/scripts/kb_ghost_scanner.py kb/scripts/sync_chroma.py
```

## Timeout
30 Minuten