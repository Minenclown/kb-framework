# REFACTOR_WORKFLOW.md — KB-Framework Ordnerstruktur-Refactor

## Ziel
- `kb/knowledge_base/` löschen (nur Redirect-Stubs)
- `src/library/` → `kb/framework/` verschieben
- Semantisch saubere Architektur: `kb/framework/` = Code-Gerüst, `kb/library/` = Nutzdaten

## Zeitbudget
Max. 3-5 Minuten pro Phase. Gesamt: ~30-35 Min.
Kein Backup nötig — GitHub Repo + aktive KB existieren als Fallback.

---

## PHASE 1: Baseline Tests (3 Min)

**Aktion:** Alle Tests ausführen
```bash
cd ~/projects/kb-framework && python -m pytest tests/ -v 2>&1 | head -50
```

**Erwartung:** Ergebnisse speichern — müssen nach Refactor >= Baseline sein

**Deliverable:** Baseline-Testreport (`REFACTOR_BASELINE.md`)

---

## PHASE 2: kb/knowledge_base/ löschen + Config (5 Min)

### A. `kb/knowledge_base/` entfernen
- `kb/knowledge_base/__init__.py` löschen
- `kb/knowledge_base/chroma_integration.py` löschen
- `kb/knowledge_base/hybrid_search.py` löschen
- `kb/knowledge_base/embedding_pipeline.py` löschen
- `kb/knowledge_base/fts5_setup.py` löschen
- `kb/knowledge_base/__pycache__/` löschen

### B. Config-Anpassungen
**`kb/base/config.py`:**
- `knowledge_base_path` property → "framework" statt "knowledge_base"
- `db_path` → `library/biblio.db` statt `knowledge.db`
- `chroma_path` → `library/chroma_db/` statt Root `chroma_db/`
- `library_path` → `~/.openclaw/kb/library/` statt `~/knowledge/library`

### C. Root `chroma_db/` konsolidieren
- `chroma_db/` entfernen
- Symlink erstellen: `chroma_db -> library/chroma_db/`

**Deliverable:** Patch-File + Config-Änderungen

---

## PHASE 3: src/library/ → kb/framework/ verschieben (5 Min)

### A. Verzeichnis verschieben
```bash
mv src/library kb/framework
```

### B. `src/` aufräumen (falls leer)
```bash
rmdir src 2>/dev/null || echo "src/ nicht leer, manuell prüfen"
```

### C. `__init__.py` erstellen
- `kb/framework/__init__.py` mit sinnvollen Exports

**Deliverable:** Verschobenes Verzeichnis + neue `__init__.py`

---

## PHASE 4: Code-Imports anpassen — Scripts (5 Min)

### `kb/scripts/` (6 Dateien)
| Datei | Was ändern |
|-------|-----------|
| `kb/scripts/reembed_all.py` | `from kb.knowledge_base.chroma_integration` → `from kb.framework.chroma_integration` |
| `kb/scripts/reembed_all.py` | `from kb.knowledge_base.embedding_pipeline` → `from kb.framework.embedding_pipeline` |
| `kb/scripts/kb_warmup.py` | `from kb.knowledge_base.chroma_integration` → `from kb.framework.chroma_integration` |
| `kb/scripts/sync_chroma.py` | `from kb.knowledge_base.chroma_integration` → `from kb.framework.chroma_integration` |
| `kb/scripts/sync_chroma.py` | `from kb.knowledge_base.embedding_pipeline` → `from kb.framework.embedding_pipeline` |
| `kb/scripts/sync_chroma.py` | `from src.library.batching` → `from kb.framework.batching` |
| `kb/scripts/migrate_fts5.py` | `from kb.knowledge_base.fts5_setup` → `from kb.framework.fts5_setup` |
| `kb/scripts/kb_full_audit.py` | `from library.knowledge_base.chroma_integration` → `from kb.framework.chroma_integration` |
| `kb/scripts/index_pdfs.py` | Hardcoded `Path.home()/knowledge/library/knowledge_base` → `kb.framework` |

### `kb/__init__.py`
- Dokumentation: "kb.knowledge_base" → "kb.framework"
- "kb.knowledge_base: Search & retrieval engine" → "kb.framework: Search & retrieval engine"

**Deliverable:** Patch-File `patches/04_scripts.patch`

---

## PHASE 5: Code-Imports anpassen — Commands + Circular Import (5 Min)

### `kb/commands/` (2 Dateien)
| Datei | Was ändern |
|-------|-----------|
| `kb/commands/sync.py` | `from src.library.chroma_integration` → `from kb.framework.chroma_integration` |
| `kb/commands/sync.py` | `from src.library.batching` → `from kb.framework.batching` |
| `kb/commands/search.py` | `HybridSearch`-Import: `kb.library.knowledge_base.hybrid_search` → `kb.framework.hybrid_search` |

### `kb/framework/chroma_plugin.py` (CIRCULAR IMPORT!)
- **WARNUNG:** Importierte VON `kb.knowledge_base` (das jetzt gelöscht ist)
- `from kb.knowledge_base.chroma_integration` → `from kb.framework.chroma_integration`
- `from kb.knowledge_base.embedding_pipeline` → `from kb.framework.embedding_pipeline`
- `from kb.knowledge_base.chroma_plugin import ChromaDBPlugin` → **entfernen** (Datei ist jetzt in `kb/framework/`)

**Deliverable:** Patch-File `patches/05_commands_and_plugin.patch`

---

## PHASE 6: Tests fixen (3 Min)

### C1. `tests/test_kb.py`
- `from kb.knowledge_base.chroma_integration` → `from kb.framework.chroma_integration`

### C2. `tests/test_chroma_singleton.py`
- `from src.library.chroma_integration` → `from kb.framework.chroma_integration`

### C3. `tests/test_indexer.py`
- `sys.path.insert` mit `kb/library/knowledge_base` → `kb/framework`

**Deliverable:** Patch-File `patches/06_tests.patch`

---

## PHASE 7: Dokumentation anpassen (3 Min)

| Datei | Was ändern |
|-------|-----------|
| `README.md` | Alle `kb.knowledge_base` → `kb.framework`, `src.library` → `kb.framework` |
| `SKILL.md` | `kb.library.knowledge_base` → `kb.framework`, `src.library` → `kb.framework` |
| `FUNCTIONS.md` | `kb.library.knowledge_base` → `kb.framework`, `src.library` → `kb.framework` |
| `HOW_TO_KB.md` | `kb.library.knowledge_base` → `kb.framework`, `src.library` → `kb.framework` |
| `CHANGELOG.md` | `kb/library/knowledge_base` → `kb/framework`, `src/library` → `kb/framework` |
| `kb/DOCSTRING_INVENTORY.md` | `library/knowledge_base` → `kb/framework`, `src.library` → `kb/framework` |
| `kb/DOCSTRING_PRIORITY.md` | `library/knowledge_base` → `kb/framework`, `src.library` → `kb/framework` |

**Deliverable:** Patch-File `patches/07_documentation.patch`

---

## PHASE 8: Verifikation (3 Min)

**Aktion:**
```bash
cd ~/projects/kb-framework
# 1. Grep nach alten Imports
grep -rn "from kb.knowledge_base" --include="*.py" .
grep -rn "kb.knowledge_base" --include="*.py" --include="*.md" .
grep -rn "src.library" --include="*.py" --include="*.md" .

# 2. Tests erneut ausführen
python -m pytest tests/ -v 2>&1 | tail -20

# 3. Dry-Run Import-Test
python -c "from kb.framework import chroma_integration; print('OK')"
```

**Erwartung:**
- 0 Treffer für `kb.knowledge_base` in Python-Files
- 0 Treffer für `src.library` in Python-Files
- Alle Tests grün
- Import-Test erfolgreich

**Deliverable:** Verifikations-Report (`REFACTOR_VERIFICATION.md`)

---

## ROLLBACK (falls nötig)
```bash
cd ~/projects/kb-framework && git checkout -- .
```

---

## CHECKLISTE

- [ ] Phase 1: Baseline dokumentiert
- [ ] Phase 2: `kb/knowledge_base/` gelöscht + Config angepasst
- [ ] Phase 3: `src/library/` → `kb/framework/` verschoben
- [ ] Phase 4: `kb/scripts/` Imports angepasst
- [ ] Phase 5: `kb/commands/` + Circular Import gelöst
- [ ] Phase 6: Tests angepasst
- [ ] Phase 7: Dokumentation aktualisiert
- [ ] Phase 8: Verifikation erfolgreich
