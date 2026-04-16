# Status Phase 4: Engine Singletons

**Datum:** 2026-04-16 19:05 UTC
**Status:** ✅ ABGESCHLOSSEN

## Änderungen

### 1. TransformersEngine — Singleton Pattern implementiert
- `_instance = None` class variable hinzugefügt
- `_lock = threading.Lock()` für Thread-Sicherheit
- `__new__()` mit Double-Checked Locking
- `__init__()` mit `_initialized` Guard (verhindert wiederholte Initialisierung)
- `get_instance(config=None)` classmethod
- `reset()` classmethod (entlädt Modell und setzt Singleton zurück)
- Docstring aktualisiert ("Singleton" statt "Not a singleton")

### 2. OllamaEngine
- Bereits korrekt als Singleton implementiert, keine Änderung nötig

### 3. Factory angepasst
- `OllamaEngine(config)` → `OllamaEngine.get_instance(config)`
- `TransformersEngine(config)` → `TransformersEngine.get_instance(config)`

### 4. Test Fixture aktualisiert
- `transformers_engine` fixture ruft `TransformersEngine.reset()` vor jeder Erstellung

## Verifikation
- ✅ Syntax Check bestanden
- ✅ TransformersEngine hat `_instance`, `_lock`, `__new__`, `get_instance`, `reset`
- ✅ Factory nutzt `get_instance()` für beide Engines

## Dauer
~5 Minuten