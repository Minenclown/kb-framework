# TASK: KB Library Refactor - Cody Task für Specialista

**Agent:** Specialista  
**Projekt:** ~/projects/kb-framework/  
**Ziel:** Trennung von Code und Daten - `kb/library/` soll ausschließlich Daten enthalten

---

## Problem Statement

Aktuell befindet sich Code in `~/projects/kb-framework/kb/library/`:
- `chroma_integration.py`
- `embedding_pipeline.py`
- `hybrid_search.py`
- `README.md`, `CHANGELOG.md`

Dies verletzt die Regel: **Library = Nur Daten, keine Funktionen.**

---

## Ziel-Struktur

```
~/projects/kb-framework/
├── src/                          # Code-Root
│   ├── base/                     # Existiert bereits
│   ├── commands/                 # Existiert bereits
│   ├── scripts/                  # Existiert bereits
│   ├── llm/                      # Existiert bereits
│   ├── obsidian/                 # Existiert bereits
│   └── library/                  # NEU: Code aus kb/library/
│       ├── __init__.py
│       ├── chroma_integration.py
│       ├── embedding_pipeline.py
│       ├── hybrid_search.py
│       └── ...
├── kb/
│   └── library/                  # NUR DATEN
│       ├── content/              # Indexierte Dateien (keine .md)
│       ├── agent/                # Ausschließlich .md Dateien
│       ├── biblio/               # Umbenennen: war llm/ → LLM-Essenzen
│       └── [user-defined]/       # Frei erweiterbar (nur Wissen)
└── tests/                        # Existiert bereits
```

---

## Cody-Template Anwendung

**Verwende das Cody Template aus SKILL.md:**
- Phase 1: Verzeichnisstruktur erstellen
- Phase 2: Code verschieben (nur Verschieben, keine Import-Updates)
- Phase 3: Importe aktualisieren
- Phase 4: Backup-Befehle implementieren
- Phase 5: Tests

---

## Deliverables

1. **5 Phasen-Dateien** in `projektplanung/cody/phase_{1-5}_*.md`
2. **Visualisierung** der neuen Struktur
3. **Checkliste** für jede Phase
4. **Rollback-Plan** falls etwas schiefgeht

---

## Constraints

- `~/kb/library/` darf NACHHER keine .py Dateien enthalten
- User darf neue Ordner in `~/kb/library/` anlegen (nur Wissen)
- Backup-Befehl adressiert ausschließlich `~/kb/library/`
- Import-Updates müssen alle Referenzen finden (grep über gesamtes Projekt)

---

## Success Criteria

- [ ] `kb/library/` enthält nur Daten (keine .py, keine Systemdateien)
- [ ] `src/library/` enthält den verschobenen Code
- [ ] Alle Imports funktionieren
- [ ] Tests passen
- [ ] Backup-Befehl existiert und funktioniert

---

**Nächster Agent:** Specialista
**Output:** 5 Phasen-Dateien im Cody-Format
