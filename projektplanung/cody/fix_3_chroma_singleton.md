# Fix 3: ChromaDB Singleton implementieren

## Meta
- **Project:** kb-framework
- **Version Target:** 1.0
- **Priority:** HIGH (P1)
- **Est. Duration:** 20 minutes
- **Domain:** INFRASTRUCTURE

## Context

### Problem
ChromaDB-Connection wird mehrfach erstellt. Kein Singleton-Pattern.

### Read First
- `chroma_client.py` oder Chroma-Integration
- Wo ChromaDB initialisiert wird
- Singleton-Pattern-Beispiele im Projekt

### Dependencies
- ChromaDB muss installiert sein

### Similar Patterns
- Andere Singleton-Implementierungen im Projekt (Engine-Singleton?)

---

## Requirements

### Functional
- [ ] Singleton-Manager für ChromaDB erstellen
- [ ] Bestehende ChromaDB-Initialisierung auf Singleton umstellen
- [ ] Connection-Pool falls sinnvoll

### Technical
- [ ] Thread-safe Implementation
- [ ] Lazy Initialization
- [ ] Graceful Fallback falls ChromaDB nicht verfügbar

### Constraints
- Keine Breaking Changes
- Rückwärtskompatibel

---

## Deliverables

### Neue Dateien
- `singleton_manager.py` (falls nötig)
- Oder: Singleton direkt in bestehendem Modul

### Geänderte Dateien
- ChromaDB-Initialisierungscode

### Tests
- Unit-Test: Singleton gibt gleiche Instance zurück
- Integration-Test: ChromaDB funktioniert wie vorher

### Dokumentation
- CHANGELOG.md

---

## Verification

- [ ] Syntax-Check: `python3 -m py_compile`
- [ ] Import-Test: `python3 -c "from kb_framework.chroma import get_client"`
- [ ] Singleton-Test: `get_client() == get_client()`

---

## Output

Status-Datei: `~/.openclaw/workspace/.task_fix_3_chroma_singleton_status`