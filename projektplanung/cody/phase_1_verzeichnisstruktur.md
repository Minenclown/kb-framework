# Phase 1: Verzeichnisstruktur erstellen

## Ziel
Neue Verzeichnisstruktur anlegen ohne Dateien zu verschieben.

## Aktuelle Struktur (Problem)
```
~/projects/kb-framework/kb/
└── library/
    ├── __init__.py              # ❌ Code
    ├── chroma_integration.py    # ❌ Code
    ├── embedding_pipeline.py    # ❌ Code
    ├── hybrid_search.py       # ❌ Code
    ├── README.md              # ❌ Systemdatei
    ├── CHANGELOG.md           # ❌ Systemdatei
    ├── content/               # ✅ OK (Daten)
    ├── agent/                 # ✅ OK (Daten)
    └── llm/                   # ⚠️ Umbenennen in biblio/
```

## Ziel-Struktur
```
~/projects/kb-framework/
├── src/
│   ├── base/                  # Existiert
│   ├── commands/              # Existiert
│   ├── scripts/               # Existiert
│   ├── llm/                   # Existiert
│   ├── obsidian/              # Existiert
│   └── library/               # NEU: Hier kommt der Code hin
│       ├── __init__.py        # Aus kb/library/ verschieben
│       ├── chroma_integration.py
│       ├── embedding_pipeline.py
│       ├── hybrid_search.py
│       └── README.md          # Aus kb/library/ verschieben
├── kb/
│   └── library/               # NUR DATEN
│       ├── content/           # Bleibt
│       ├── agent/             # Bleibt
│       └── biblio/            # Umbenannt von llm/
└── tests/                     # Existiert
```

## Schritte

1. **Neues Verzeichnis anlegen:**
   ```bash
   mkdir -p ~/projects/kb-framework/src/library
   ```

2. **Umbenennen:** `kb/library/llm/` → `kb/library/biblio/`
   ```bash
   mv ~/projects/kb-framework/kb/library/llm \
      ~/projects/kb-framework/kb/library/biblio
   ```

3. **Prüfen:** Keine Dateien verschoben, nur Umbenennung

## Checkliste
- [ ] `src/library/` existiert
- [ ] `kb/library/biblio/` existiert (war `llm/`)
- [ ] Keine Dateien verschoben (nur Umbenennung)

## Output für Phase 2
- Verzeichnis `src/library/` bereit
- `kb/library/biblio/` bereit
