# Fix 5: Module Split - report_generator (1562 Zeilen!)

## Meta
- **Project:** kb-framework
- **Version Target:** 1.0
- **Priority:** HIGH (P1)
- **Est. Duration:** 60-90 minutes
- **Domain:** REFACTORING

## Context

### Problem
`report_generator` ist 1562 Zeilen lang. 18 Module sind >500 Zeilen.
Der Report-Generator ist das größte Problem.

### Read First
- `report_generator.py` (1562 Zeilen analysieren)
- Projektstruktur verstehen
- Verzeichnisstruktur

### Dependencies
- Keine (aber nach Fix 3 und 4 sinnvoll)

### Similar Patterns
- Andere Module die bereits aufgeteilt wurden

---

## Requirements

### Functional
- [ ] Report-Generator in logische Teilmodule aufteilen:
  - `report_generation/` - Kernlogik
  - `report_formatting/` - Formatierung
  - `report_templates/` - Templates
  - `report_export/` - Export-Funktionen

### Technical
- [ ] Jedes Modul <300 Zeilen anstreben
- [ ] Klare Schnittstellen definieren
- [ ] Imports konsistent halten
- [ ] `__init__.py` mit sauberen Exports

### Constraints
- Keine Funktionalität ändern (nur umstrukturieren)
- Alle bestehenden Tests müssen weiterhin funktionieren
- Rückwärtskompatibel für externe Imports

---

## Deliverables

### Neue Dateien
- `report_generation/report_core.py`
- `report_generation/report_formatting.py`
- `report_generation/report_templates.py`
- `report_generation/report_export.py`
- `report_generation/__init__.py`

### Geänderte Dateien
- `report_generator.py` → Legacy-Wrapper (temporär)
- Import-Referenzen

### Tests
- Unit-Tests für jeden Teil
- Integration-Tests
- Regression-Tests

### Dokumentation
- ARCHITECTURE.md aktualisieren
- CHANGELOG.md

---

## Verification

- [ ] Syntax-Check: `python3 -m py_compile`
- [ ] Import-Test: `from kb_framework.report_generation import ...`
- [ ] Unit-Tests: `pytest tests/report_generation/`
- [ ] Integration-Test: Voller Report-Generation-Durchlauf

---

## Rollback

Falls etwas schief geht:
1. `git checkout` auf vorherigen Stand
2. Tests laufen lassen
3. Struktur wiederherstellen

---

## Output

Status-Datei: `~/.openclaw/workspace/.task_fix_5_module_split_status`