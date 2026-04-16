# Phase 4: Engine Singletons (DG-3 Option 2)

## Context
OllamaEngine ist Singleton, TransformersEngine nicht.
DG-3 Entscheidung: Beide Engines als Singletons implementieren.

## Files
- `src/llm/transformers_engine.py`
- `src/llm/ollama_engine.py` (verifizieren)

## Ziel
```python
class TransformersEngine(BaseLLMEngine):
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        super().__init__()
        self._initialized = True
```

## Steps

### 1. OllamaEngine prüfen
```bash
rg "_instance|get_instance" src/llm/ollama_engine.py

# Verify:
# - class variable _instance = None
# - get_instance() classmethod
```

### 2. TransformersEngine Singleton machen
```bash
# Pattern in transformers_engine.py einfügen:
# - _instance = None class variable
# - __new__ override
# - get_instance() classmethod
# - __init__ guard (nur einmal initialisieren)
```

### 3. Factory/Registry anpassen (falls vorhanden)
```bash
rg "create_engine|get_engine" src/llm/

# Alle Stellen auf get_instance() umstellen
```

### 4. Thread-Safety (optional für später)
```python
import threading
_lock = threading.Lock()

def __new__(cls):
    global _lock
    with _lock:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
    return cls._instance
```

## Verification
```python
# Test Singleton behavior
python -c "
from src.llm.transformers_engine import TransformersEngine
e1 = TransformersEngine.get_instance()
e2 = TransformersEngine.get_instance()
assert e1 is e2, 'Not a singleton!'
print('Singleton works!')
"

# Test auch für Ollama
python -c "
from src.llm.ollama_engine import OllamaEngine
e1 = OllamaEngine.get_instance()
e2 = OllamaEngine.get_instance()
assert e1 is e2, 'Not a singleton!'
print('Ollama Singleton works!')
"
```

## Rollback
```bash
cd ~/projects/kb-framework && git checkout src/llm/transformers_engine.py
```

## Timeout
2 Stunden

## Notes
- Factory Pattern konsistent mit Singleton (DG-3 Option 2)
- Thread-Safety für Production wichtig
- Initialization guard verhindert mehrfaches __init__