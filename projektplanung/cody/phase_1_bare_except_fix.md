# Phase 1: Bare except Statements beheben

## Context
Bare `except:` fangen alle Exceptions ab, inklusive KeyboardInterrupt und SystemExit.
Dies führt zu silent failures und macht Debugging unmöglich.
KB Sync (Phase 6) braucht robustes Error-Handling.

## Files
- `kb/scripts/migrate.py:18`
- `kb/scripts/kb_ghost_scanner.py:80, 102, 133`

## Problem
```python
# PROBLEMATISCH - fängt auch SystemExit/KeyboardInterrupt
except:
    pass

# KORREKT
except Exception as e:
    logger.warning(f"Operation failed: {e}")
```

## Steps
1. **migrate.py Zeile 18**
   ```bash
   # Zeile finden und prüfen
   rg -n "^\s+except:" kb/scripts/migrate.py
   
   # Ersetzen: except: → except Exception as e:
   ```

2. **kb_ghost_scanner.py Zeile 80, 102, 133**
   ```bash
   rg -n "^\s+except:" kb/scripts/kb_ghost_scanner.py
   
   # Ersetzen: except: → except Exception as e:
   # Logging hinzufügen wo sinnvoll
   ```

3. **Prüfen ob weitere existieren**
   ```bash
   rg "^\s+except:" kb/scripts/ --no-ignore
   ```

4. **Logging hinzufügen**
   - Wo `silent pass` existiert: Logging oder explizite Fehlerbehandlung
   - `logger.warning()` oder `logger.error()`

## Verification
```bash
# Keine bare except mehr
rg "^\s+except:" kb/scripts/ --no-ignore

# Sollte nur "except Exception:" oder "except SpecificError:" zeigen
# Oder keine Treffer
```

## Rollback
```bash
cd ~/projects/kb-framework && git checkout kb/scripts/migrate.py kb/scripts/kb_ghost_scanner.py
```

## Timeout
30 Minuten