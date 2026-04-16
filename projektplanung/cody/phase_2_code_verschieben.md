# Phase 2: Code verschieben (nur Verschieben, keine Import-Updates)

## Ziel
Alle Code-Dateien aus `kb/library/` nach `src/library/` verschieben.

## Dateien zu verschieben

| Quelle | Ziel | Typ |
|--------|------|-----|
| `kb/library/__init__.py` | `src/library/__init__.py` | Code |
| `kb/library/chroma_integration.py` | `src/library/chroma_integration.py` | Code |
| `kb/library/embedding_pipeline.py` | `src/library/embedding_pipeline.py` | Code |
| `kb/library/hybrid_search.py` | `src/library/hybrid_search.py` | Code |
| `kb/library/README.md` | `src/library/README.md` | Doc |
| `kb/library/CHANGELOG.md` | `src/library/CHANGELOG.md` | Doc |

## NICHT verschieben (bleiben in `kb/library/`)

| Pfad | Grund |
|------|-------|
| `kb/library/content/` | Daten |
| `kb/library/agent/` | Daten (.md) |
| `kb/library/biblio/` | Daten (umbenannt von llm/) |

## Schritte

```bash
# In src/library/ verschieben
mv ~/projects/kb-framework/kb/library/__init__.py \
   ~/projects/kb-framework/src/library/

mv ~/projects/kb-framework/kb/library/chroma_integration.py \
   ~/projects/kb-framework/src/library/

mv ~/projects/kb-framework/kb/library/embedding_pipeline.py \
   ~/projects/kb-framework/src/library/

mv ~/projects/kb-framework/kb/library/hybrid_search.py \
   ~/projects/kb-framework/src/library/

mv ~/projects/kb-framework/kb/library/README.md \
   ~/projects/kb-framework/src/library/

mv ~/projects/kb-framework/kb/library/CHANGELOG.md \
   ~/projects/kb-framework/src/library/
```

## Verifikation

```bash
# Prüfen: kb/library/ hat keine .py mehr
find ~/projects/kb-framework/kb/library -name "*.py" -type f
# Sollte: KEINE ERGEBNISSE

# Prüfen: src/library/ hat die Dateien
ls -la ~/projects/kb-framework/src/library/
# Sollte: __init__.py, chroma_integration.py, embedding_pipeline.py, hybrid_search.py, README.md, CHANGELOG.md
```

## Checkliste
- [ ] Alle .py Dateien aus `kb/library/` verschoben
- [ ] Alle Dateien in `src/library/` angekommen
- [ ] `kb/library/` enthält nur noch: `content/`, `agent/`, `biblio/`

## Wichtig
⚠️ **KEINE Importe ändern in Phase 2!** Das passiert in Phase 3.
