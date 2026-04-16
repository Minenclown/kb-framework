# Phase 1 - Sub-Task 3: Factory + __init__ aktualisiert

**Status:** ✅ DONE

**`kb/biblio/engine/factory.py`:**
- `create_engine()` unterstützt jetzt "auto" und "compare" über Delegation an `EngineRegistry`
- Single-source ("ollama", "huggingface") bleibt direkt für Backward-Kompatibilität
- Multi-source ("auto", "compare") delegiert an `EngineRegistry.get_instance(config).get_primary()`
- `EngineRegistryError` wird in `LLMConfigError` gewrapped

**`kb/biblio/engine/__init__.py`:**
- Neue Exports: `EngineRegistry`, `EngineRegistryError`, `get_engine_registry`

**Tests:** Syntax-Check ✅ für alle geänderten Dateien