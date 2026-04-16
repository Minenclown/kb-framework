# Status: EngineRegistry Factory Refactor

## Datum
2026-04-16

## Ziel
EngineRegistry für bessere Testbarkeit refactoren – Factory-Methode injizieren statt interne Engine-Erstellung.

## Problem
Die `_create_ollama_engine()` und `_create_hf_engine()` Methoden in EngineRegistry erstellten die Engines intern. Tests mussten `patch.object(EngineRegistry, '_create_ollama_engine', ...)` verwenden, was auf private Methods zugreift und spröde ist.

## Lösung: Factory-Injection (Option 1)

### Neue Komponenten

1. **`EngineFactory` Protocol** (`kb/biblio/engine/factory.py`)
   - `@runtime_checkable` Protocol mit zwei Methoden:
     - `create_ollama_engine(config) -> BaseLLMEngine`
     - `create_hf_engine(config) -> BaseLLMEngine`

2. **`DefaultEngineFactory`** (`kb/biblio/engine/factory.py`)
   - Produktions-Factory, die `OllamaEngine.get_instance()` und `TransformersEngine.get_instance()` verwendet
   - Enthält die `is_available()`-Prüfung für HF, die vorher in `_create_hf_engine()` war

3. **`MockEngineFactory`** (in Tests)
   - Test-Helfer, der Mock-Engines zurückgibt
   - Unterstützt `ollama_side_effect` und `hf_side_effect` für Fehler-Simulation

### Geänderte Dateien

| Datei | Änderung |
|-------|----------|
| `kb/biblio/engine/factory.py` | `EngineFactory` Protocol + `DefaultEngineFactory` hinzugefügt |
| `kb/biblio/engine/registry.py` | `__init__` und `get_instance` akzeptieren `engine_factory` Parameter; `_create_*` delegieren an Factory |
| `kb/biblio/engine/__init__.py` | `EngineFactory`, `DefaultEngineFactory` exportiert |
| `tests/test_llm/test_engine_registry.py` | Alle Tests umgeschrieben: `MockEngineFactory` statt `patch.object` |

### Backward Compatibility
- ✅ `EngineRegistry(config=...)` funktioniert weiterhin ohne Factory-Parameter
- ✅ `EngineRegistry.get_instance(config=...)` funktioniert weiterhin
- ✅ `create_engine()` Convenience-Funktion unverändert
- ✅ `DefaultEngineFactory` als Standard wenn keine Factory übergeben wird

### Test-Ergebnis
- **45 Tests**, alle bestanden
- Neue Test-Klasse `TestEngineFactoryProtocol` (4 Tests) für Protocol-Konformität
- Keine `patch.object`-Aufrufe mehr in Registry-Tests

### Beispiel: Mock-Factory in Tests
```python
factory = MockEngineFactory(hf_engine=mock_hf(), ollama_engine=mock_ollama())
registry = EngineRegistry(config=auto_config, engine_factory=factory)
```

### Beispiel: Fehler simulieren
```python
factory = MockEngineFactory(
    hf_side_effect=EngineRegistryError("HF unavailable"),
    ollama_engine=mock_ollama(),
)
registry = EngineRegistry(config=auto_config, engine_factory=factory)
```