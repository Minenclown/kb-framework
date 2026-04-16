# Fix Phase 6 Status
**Phase:** 6 - Hardcoded Paths in Scripts beheben
**Status:** ✅ COMPLETED
**Time:** 2026-04-16 18:08 UTC

## Was wurde gemacht

### kb/scripts/reembed_all.py
- `Path.home() / ".openclaw" / "kb" / ...` hardcoded Pfade → `KBConfig.get_instance().db_path` / `.chroma_path`
- Helper-Funktion `_get_paths()` hinzugefügt
- Falschen `sys.path.insert` für nicht-existierendes `library/knowledge_base` entfernt
- `from kb.base.config import KBConfig` Import hinzugefügt

### kb/scripts/sync_chroma.py
- `from config import CHROMA_PATH, DB_PATH` → `from kb.base.config import KBConfig`
- `sqlite3.connect(str(DB_PATH))` → `sqlite3.connect(str(config.db_path))`
- `CHROMA_PATH` → `config.chroma_path` in allen Aufrufen
- Falschen Import `from library.knowledge_base.chroma_integration` → `from kb.knowledge_base.chroma_integration` (via Phase 1 Redirect)

## Verifikation
- reembed_all.py Syntax: ✅
- sync_chroma.py Syntax: ✅

## Rollback
```bash
cd ~/projects/kb-framework && git checkout kb/scripts/reembed_all.py kb/scripts/sync_chroma.py
```