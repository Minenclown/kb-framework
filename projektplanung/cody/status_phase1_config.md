# Phase 1 - Sub-Task 1: Config erweitert

**Status:** ✅ DONE

**Änderungen in `kb/biblio/config.py`:**
- `model_source`: erlaubt jetzt "auto" und "compare" (zusätzlich zu "ollama" und "huggingface")
- Neue Klassen-Defaults: `DEFAULT_OLLAMA_MODEL`, `DEFAULT_OLLAMA_TIMEOUT`, `DEFAULT_OLLAMA_TEMPERATURE`, `DEFAULT_PARALLEL_MODE`, `DEFAULT_PARALLEL_STRATEGY`
- Neue `__init__` Parameter: `ollama_model`, `ollama_timeout`, `ollama_temperature`, `parallel_mode`, `parallel_strategy`
- Alle neuen Felder mit Env-Var-Support: `KB_LLM_OLLAMA_MODEL`, `KB_LLM_OLLAMA_TIMEOUT`, `KB_LLM_OLLAMA_TEMPERATURE`, `KB_LLM_PARALLEL_MODE`, `KB_LLM_PARALLEL_STRATEGY`
- Validierung erweitert: `VALID_MODEL_SOURCES`, `VALID_PARALLEL_STRATEGIES`, HF-Validierung für auto/compare, ollama_timeout/temperature Validierung, compare erfordert ollama_model
- `to_dict()` und `__str__()` aktualisiert

**Tests:** Syntax-Check ✅, Import-Test ✅