# Status Minor Fix 2: EngineFactory redundanter Aufruf

**Date:** 2026-04-16
**Issue:** `EngineFactory` class doesn't exist; `LLMConfig()` called directly (bypasses singleton); double engine creation
**File:** `kb/commands/engine.py`

## Fix
- Removed import of non-existent `EngineFactory`
- Replaced `LLMConfig()` direct constructor calls with `LLMConfig.get_instance()`
- Replaced `factory.is_engine_available()` calls with `create_engine()` + `engine.is_available()`
- For non-configured engines, creates alt config with `skip_validation=True`

## Before
```python
from kb.biblio.engine.factory import EngineFactory
...
llm_config = LLMConfig()  # Would raise LLMConfigError if singleton exists
factory = EngineFactory()  # Class doesn't exist!
available = factory.is_engine_available(name)
```

## After
```python
from kb.biblio.engine.factory import create_engine
...
llm_config = LLMConfig.get_instance()
...
engine = create_engine(llm_config) if llm_config.model_source == name else None
if engine:
    available = engine.is_available()
```

## Verification
- ✅ Syntax valid (py_compile)
- ✅ AST parse OK
- ✅ No EngineFactory reference
- ✅ Uses LLMConfig.get_instance()
- ✅ Uses create_engine from factory