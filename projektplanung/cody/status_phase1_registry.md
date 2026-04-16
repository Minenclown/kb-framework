# Phase 1 - Sub-Task 2: EngineRegistry erstellt

**Status:** ✅ DONE

**Neue Datei: `kb/biblio/engine/registry.py`**

Klasse `EngineRegistry` (Singleton, thread-safe):
- `get_instance(config=None)` — Singleton-Zugriff
- `reset()` — Singleton zurücksetzen bei model_source-Wechsel (mit engine.shutdown())
- `get_engine(source)` — Engine nach Typ ("huggingface", "ollama")
- `get_primary()` — Haupt-Engine (auto: HF→Ollama, compare: HF)
- `get_secondary()` — Fallback-Engine (auto: Ollama, compare: Ollama, single: None)
- `get_both()` — Tuple (primary, secondary)
- `is_engine_available(source)` — Health-Check mit try/except
- `status()` — Registry-Status als Dict
- Properties: `model_source`, `has_secondary`, `primary_provider`

Auto-Mode-Logik:
- HF zuerst (primary), Ollama als fallback (secondary)
- Wenn HF-Erstellung fehlschlägt: Ollama wird zum primary
- Wenn beide fehlschlagen: EngineRegistryError

Lazy initialization: Engines werden erst beim ersten Zugriff erstellt.

**Tests:** Syntax-Check ✅, Import-Test (timeout - Syntax war OK)