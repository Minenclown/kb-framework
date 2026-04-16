# Fix 1: requirements.txt erstellen

## Meta
- **Project:** kb-framework
- **Version Target:** 1.0
- **Priority:** CRITICAL (P0)
- **Est. Duration:** 15 minutes
- **Domain:** INFRASTRUCTURE

## Context

### Problem
Keine `requirements.txt` oder `pyproject.toml` dokumentiert. Neue Entwickler können Dependencies nicht installieren.

### Read First
- Alle `.py` Dateien im Projekt (für Imports)
- `setup.py` falls vorhanden
- `pyproject.toml` falls vorhanden

### Dependencies
- Keine externen Dependencies für diesen Fix

### Similar Patterns
- Standard Python setup

---

## Requirements

### Functional
- [ ] Alle verwendeten Python-Module identifizieren
- [ ] Externe Packages von Standard-Library unterscheiden
- [ ] requirements.txt erstellen

### Technical
- [ ] Alphabetisch sortierte Dependencies
- [ ] Minimale Version oder exacte Versionen
- [ ] Separate `requirements-dev.txt` für Dev-Dependencies

### Constraints
- Keine neuen Dependencies hinzufügen (nur dokumentieren was existiert)
- Virtual environment kompatibel

---

## Deliverables

### Neue Dateien
- `requirements.txt` (Hauptdependencies)
- `requirements-dev.txt` (Dev-Dependencies, optional)

### Geänderte Dateien
- Keine

### Tests
- `pip install -r requirements.txt` muss funktionieren

### Dokumentation
- README.md aktualisieren mit Installationsanleitung

---

## Verification

- [ ] Syntax-Check: `python3 -m py_compile` (keine Syntaxfehler im Projekt)
- [ ] Import-Test: Alle Haupt-Imports funktionieren
- [ ] Installation-Test: `pip install -r requirements.txt`

---

## Output

Status-Datei: `~/.openclaw/workspace/.task_fix_1_requirements_status`