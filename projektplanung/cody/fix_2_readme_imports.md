# Fix 2: README Python Imports korrigieren

## Meta
- **Project:** kb-framework
- **Version Target:** 1.0
- **Priority:** CRITICAL (P0)
- **Est. Duration:** 10 minutes
- **Domain:** DOCUMENTATION

## Context

### Problem
README.md enthält falsche Import-Pfade für `EngineRegistry` und `create_engine`.

### Read First
- `README.md`
- `kb_engine.py` oderEngine-Modul
- `src/engine/` falls strukturiert

### Dependencies
- Fix 1 (requirements.txt) sollte已完成 für stabile Struktur
- Aber NICHT zwingend erforderlich

### Similar Patterns
- `from kb_framework.engine import EngineRegistry` (Beispiel)

---

## Requirements

### Functional
- [ ] Alle Import-Beispiele in README identifizieren
- [ ] Korrekte Import-Pfade verifizieren
- [ ] README mit korrekten Imports aktualisieren

### Technical
- [ ] Prüfen dass alle dokumentierten Imports tatsächlich funktionieren
- [ ] Konsistente Formatierung

### Constraints
- README soll korrekt und vollständig sein
- Keine README-Formatierung kaputt machen

---

## Deliverables

### Neue Dateien
- Keine

### Geänderte Dateien
- `README.md`

### Tests
- Optional: Showcase-Test-Skript

### Dokumentation
- README.md Sections: Installation, Usage, API

---

## Verification

- [ ] Syntax-Check: `python3 -m py_compile README.py` (falls enthalten)
- [ ] Import-Test: `python3 -c "from kb_framework import ..."`
- [ ] README lesbar und korrekt

---

## Output

Status-Datei: `~/.openclaw/workspace/.task_fix_2_readme_imports_status`