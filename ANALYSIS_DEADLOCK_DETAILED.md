# 🔍 Deadlock-Analyse: kb-framework Import-Deadlock

**Datum:** 2026-04-15  
**Analyst:** Sir Stern  
**Status:** ROOT CAUSE IDENTIFIZIERT

---

## Executive Summary

Der Import-Deadlock ist **kein klassischer Threading-Deadlock** zwischen Locks. Es handelt sich um ein **Import-Time Initialization Deadlock** — eine Kombination aus:

1. **Module-Level Side Effects** (`KBConfig.get_instance()` bei Importzeit)
2. **Import-Reordering via `sys.path.insert()`**
3. **Double-Checked Locking Race Condition** in `KBConfig.get_instance()`

Dies erklärt die Nicht-Determinismus: Das Verhalten hängt von der **Import-Reihenfolge** ab, die sich je nach Einstiegspunkt (CLI, Test, Library-Import) unterscheidet.

---

## 1. Lock-Inventar

Alle `threading.Lock()` Instanzen im Codebase:

| Datei | Zeile | Variable | Typ | Scope |
|-------|-------|----------|-----|-------|
| `kb/base/config.py` | 41 | `KBConfig._lock` | `Lock` | Klassenvariable |
| `kb/base/logger.py` | 63 | `KBLogger._lock` | `Lock` | Klassenvariable |
| `kb/base/logger.py` | 70 | `KBLogger._cache_lock` | `Lock` | Klassenvariable |
| `kb/llm/config.py` | 42 | `LLMConfig._lock` | `Lock` | Klassenvariable |
| `kb/llm/engine/ollama_engine.py` | 68 | `OllamaEngine._lock` | `Lock` | Klassenvariable |
| `kb/library/knowledge_base/chroma_plugin.py` | 105 | `self._lock` | `Lock` | Instanzvariable |

**Wichtig:** `KBConnection` hat **keinen** Lock! Die Connection ist nicht thread-safe, aber das ist nicht das Deadlock-Problem.

---

## 2. ROOT CAUSE: Module-Level Side Effects bei Import

### Das Hauptproblem

**Drei Dateien rufen `KBConfig.get_instance()` auf MODULEVEL auf — nicht in Funktionen, sondern beim Import:**

#### ❌ `chroma_plugin.py` (Zeile 35-36)
```python
from kb.base.config import KBConfig
_default_chroma_path = str(KBConfig.get_instance().chroma_path)  # ← MODULE-LEVEL CALL
```

#### ❌ `embedding_pipeline.py` (Zeile 31-32)
```python
from kb.base.config import KBConfig
_default_chroma_path = str(KBConfig.get_instance().chroma_path)  # ← MODULE-LEVEL CALL
```

#### ❌ `chroma_integration.py` (Zeile 26-27)
```python
from kb.base.config import KBConfig
_default_chroma_path = str(KBConfig.get_instance().chroma_path)  # ← MODULE-LEVEL CALL
```

**Was passiert:** Wenn irgendein Modul `from kb.library.knowledge_base import ...` importiert, wird die `__init__.py` ausgeführt, die wiederum `chroma_integration`, `chroma_plugin`, und `embedding_pipeline` importiert — und **jeder dieser Importe ruft `KBConfig.get_instance()` auf**, bevor die Import-Kette vollständig aufgelöst ist.

### Die Import-Kette (vereinfacht)

```
from kb.library.knowledge_base import HybridSearch
  → kb/library/knowledge_base/__init__.py
    → from .chroma_integration import ChromaIntegration    # (1)
      → sys.path.insert(0, ...)  # ⚠️ MODIFIES IMPORT PATH
      → from kb.base.config import KBConfig                # (2)
      → KBConfig.get_instance()                            # (3) LOCK ACQUIRED
    → from .embedding_pipeline import EmbeddingPipeline     # (4)
      → sys.path.insert(0, ...)  # ⚠️ MODIFIES IMPORT PATH AGAIN
      → from kb.base.config import KBConfig                # (5) Already in sys.modules
      → KBConfig.get_instance()                            # (6) ALREADY EXISTS, no lock needed
    → from .chroma_plugin import ChromaDBPlugin             # (7)
      → sys.path.insert(0, ...)  # ⚠️ THIRD PATH MODIFICATION
      → from kb.base.config import KBConfig                # (8)
      → KBConfig.get_instance()                            # (9) ALREADY EXISTS
```

### Warum es manchmal hängt

In einem **Single-Thread-Kontext** funktioniert das meistens — `KBConfig.get_instance()` wird beim ersten Aufruf erstellt und nachfolgende Aufrufe finden es vor. ABER:

---

## 3. Der Race Condition-Bug in KBConfig.get_instance()

### Der fehlerhafte Code (Zeile 93-101 in `config.py`)

```python
@classmethod
def get_instance(cls, base_path: Optional[Path] = None) -> 'KBConfig':
    if cls._instance is None:                    # ← CHECK 1 (ohne Lock)
        with cls._lock:                          # ← LOCK ACQUIRED
            if cls._instance is None:            # ← CHECK 2 (mit Lock)
                cls._instance = cls(base_path)   # ← __init__ AQUIRED!
    elif base_path is not None:                   # ← HIER IST DER BUG
        existing = cls._instance._base_path.resolve()
        requested = Path(base_path).resolve()
        if existing != requested:
            cls._instance = cls(base_path)        # ← ⚠️ KEIN LOCK!
    return cls._instance
```

### Bug-Analyse

Der `elif base_path is not None`-Zweig wird **außerhalb des Locks** ausgeführt. Wenn zwei Threads gleichzeitig `get_instance(base_path=...)` aufrufen:

```
Thread A: cls._instance is None → acquired lock → creating instance → sets _instance
Thread B: cls._instance is not None (sees A's instance) → enters elif → 
          cls._instance = cls(base_path) ← ⚠️ CONSTRUCTOR RAISES because _instance is not None
```

Die `__init__`-Methode hat diese Prüfung:

```python
def __init__(self, base_path=None, skip_validation=False):
    if KBConfig._instance is not None:
        raise KBConfigError("Use KBConfig.get_instance() instead of constructor")
```

**Das bedeutet:** Wenn Thread A gerade `_instance` gesetzt hat und Thread B in den `elif`-Zweig geht und `cls(base_path)` aufruft, **wirft der Konstruktor eine Exception**, weil `_instance` bereits gesetzt ist. Das ist kein Deadlock im engeren Sinn, aber es kann zu **hängenden Imports** führen, wenn die Exception nicht sauber abgefangen wird und der Import-Thread in einem unklaren Zustand stecken bleibt.

---

## 4. Der sys.path.insert()-Chaos

### Das Problem

Drei Dateien modifizieren `sys.path` bei Import:

```python
# chroma_integration.py:24
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# embedding_pipeline.py:30
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# chroma_plugin.py:34
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
```

### Warum das schädlich ist

1. **Nicht-idempotent:** Jeder `insert(0, ...)` Aufruf schiebt den Pfad an Position 0, auch wenn er schon existiert. Bei Mehrfachimport wird der Pfad mehrfach vorne eingefügt.
2. **Import-Reordering:** Wenn `sys.path` modifiziert wird, **während** andere Module importiert werden, kann Python ein Modul aus dem falschen Pfad laden.
3. **Race Condition mit Threading:** Wenn ein Thread `sys.path.insert()` ausführt, während ein anderer Thread `import` ausführt, kann der Import-Mechanismus von Python (der GIL-basiert ist, aber trotzdem Import-locks hat) in einen unerwarteten Zustand geraten.

**Python hat einen internen Import-Lock** (`_imp.acquire_lock()`). Wenn Module-Level-Code diesen Lock hält und dann versucht, ein weiteres Modul zu importieren (z.B. `kb.base.config`), kann es zu einer **seltsamen Form von Import-Deadlock** kommen, insbesondere wenn:
- Thread A importiert `chroma_integration` (hält Python Import-Lock)
- Thread B importiert `kb.base.config` (wartet auf Python Import-Lock)
- Thread A's Module-Level-Code ruft `KBConfig.get_instance()` auf, was `cls._lock` acquired
- Wenn Thread B gleichzeitig `KBConfig.get_instance()` aufruft, wartet er auf `cls._lock`
- Aber Thread A wartet möglicherweise auf etwas, das Thread B initialisieren müsste

---

## 5. Nicht-Determinismus: Warum es manchmal funktioniert

Der Deadlock ist **import-order-abhängig**:

| Einstiegspunkt | Import-Reihenfolge | Ergebnis |
|----------------|--------------------|----------|
| `python -m kb sync` | `__main__.py` → `KBLogger` → Commands → Library | ✅ Meistens OK (KBConfig wird vor Library importiert) |
| `from kb.library.knowledge_base import HybridSearch` | Direkt in Library → `KBConfig.get_instance()` bei Import | ⚠️ Race Condition möglich |
| Pytest mit mehreren Test-Dateien | Parallele Imports → Konkurrierende `get_instance()` | ❌ Häufiger Deadlock |
| Jupyter/IPython | Cell-basierte Imports → Verschiedene Ausführungsreihen | ⚠️ Nicht-deterministisch |

**Der Schlüssel:** Wenn `KBConfig.get_instance()` zum **ersten Mal** aufgerufen wird, während der Python-Import-Lock gehalten wird, und gleichzeitig ein anderer Thread versucht, ein Modul zu importieren, das ebenfalls `KBConfig.get_instance()` benötigt, entsteht ein klassischer **Lock-Ordering-Deadlock**:

```
Thread 1: [Python Import Lock] → waiting for [KBConfig._lock]
Thread 2: [KBConfig._lock] → waiting for [Python Import Lock]
```

---

## 6. Minimaler Reproducer

```python
"""
Deadlock Reproducer for kb-framework
Run with: python3 reproduce_deadlock.py
"""
import threading
import sys
from pathlib import Path

# Setup path like the real code does
sys.path.insert(0, str(Path(__file__).parent))

def thread1_import_library():
    """Simulates importing from library path"""
    # This triggers: chroma_integration → KBConfig.get_instance() at module level
    from kb.library.knowledge_base import ChromaIntegration

def thread2_import_config():
    """Simulates importing config from another thread"""
    # This also calls KBConfig.get_instance()
    from kb.base.config import KBConfig
    config = KBConfig.get_instance()
    print(f"Thread 2 got config: {config}")

# Race: both threads try to initialize KBConfig simultaneously
t1 = threading.Thread(target=thread1_import_library, name="Library-Importer")
t2 = threading.Thread(target=thread2_import_config, name="Config-Importer")

t1.start()
t2.start()

t1.join(timeout=5)
t2.join(timeout=5)

if t1.is_alive() or t2.is_alive():
    print("❌ DEADLOCK DETECTED!")
else:
    print("✅ No deadlock this time (non-deterministic)")
```

**Einfacherer Reproducer (ohne Threading, zeigt das Grundproblem):**

```python
"""
Shows that module-level get_instance() creates ordering dependency.
"""
# This works:
from kb.base.config import KBConfig
config = KBConfig.get_instance()  # OK, first call
from kb.library.knowledge_base import ChromaIntegration  # OK, config exists

# This might fail (if KBConfig not yet initialized):
# from kb.library.knowledge_base import ChromaIntegration  # ← KBConfig.get_instance() at import
```

---

## 7. FIX-PLAN

### Priorität 1: Module-Level Side Effects entfernen (Kritisch)

**Problem:** `KBConfig.get_instance()` wird bei Import aufgerufen.

**Fix:** Lazy initialization statt Module-Level-Konstanten.

#### `chroma_plugin.py` — Zeile 35-36
```python
# VORHER (BROKEN):
from kb.base.config import KBConfig
_default_chroma_path = str(KBConfig.get_instance().chroma_path)

# NACHHER (FIXED):
from kb.base.config import KBConfig

def _get_default_chroma_path() -> str:
    """Lazy-resolve default chroma path."""
    return str(KBConfig.get_instance().chroma_path)
```

Dann alle Verwendungen von `_default_chroma_path` durch `_get_default_chroma_path()` ersetzen.

**Gleiches Pattern für:**
- `embedding_pipeline.py` Zeile 31-32
- `chroma_integration.py` Zeile 26-27

### Priorität 2: sys.path.insert() entfernen (Wichtig)

**Problem:** `sys.path.insert(0, ...)` bei jedem Import.

**Fix:** Proper Package-Struktur statt Path-Hacks.

Wenn das Package korrekt installiert ist (`pip install -e .`), sind die `sys.path.insert()` Aufrufe überflüssig. Wenn nicht, sollten sie durch ein einziges Setup in `__main__.py` ersetzt werden.

```python
# VORHER (in 3 Dateien):
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# NACHHER: Garbage in __init__.py of kb.library:
# (entfernen — korrekte Package-Struktur vorausgesetzt)
```

### Priorität 3: KBConfig.get_instance() Race Condition fixen (Wichtig)

**Problem:** `elif base_path is not None`-Zweig wird ohne Lock ausgeführt.

```python
# VORHER (BROKEN):
@classmethod
def get_instance(cls, base_path: Optional[Path] = None) -> 'KBConfig':
    if cls._instance is None:
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(base_path)
    elif base_path is not None:
        existing = cls._instance._base_path.resolve()
        requested = Path(base_path).resolve()
        if existing != requested:
            cls._instance = cls(base_path)  # ← KEIN LOCK!
    return cls._instance

# NACHHER (FIXED):
@classmethod
def get_instance(cls, base_path: Optional[Path] = None) -> 'KBConfig':
    if cls._instance is not None and base_path is None:
        return cls._instance  # Fast path: no lock needed
    
    with cls._lock:
        if cls._instance is None:
            cls._instance = cls(base_path)
        elif base_path is not None:
            existing = cls._instance._base_path.resolve()
            requested = Path(base_path).resolve()
            if existing != requested:
                old = cls._instance
                cls._instance = None
                cls._initialized = False
                try:
                    cls._instance = cls(base_path)
                except KBConfigError:
                    cls._instance = old  # Restore on failure
                    cls._initialized = True
                    raise
        return cls._instance
```

### Priorität 4: KBLogger.get_logger() Double-Lock-Acquisition (Niedrig, aber lästig)

**Problem in `logger.py` Zeile 119-122:**
```python
# Check cache first
with cls._cache_lock:
    if name in cls._logger_cache:
        cached = cls._logger_cache[name]
        ...
        return cached

# Create new logger (no lock!)
logger = logging.getLogger(name)
...
# Cache the logger
with cls._cache_lock:  # ← Zweites Mal acquired
    cls._logger_cache[name] = logger
```

Dies ist kein Deadlock (es sind keine verschachtelten Locks), aber es gibt eine Race Condition: Zwei Threads können gleichzeitig dasselbe Logger-Objekt erstellen. Harmlos, aber ineffizient.

**Fix:** Alles unter `_cache_lock`:
```python
with cls._cache_lock:
    if name in cls._logger_cache:
        return cls._logger_cache[name]
    logger = logging.getLogger(name)
    # ... setup ...
    cls._logger_cache[name] = logger
    return logger
```

---

## 8. Zusammenfassung

| # | Problem | Schwere | Datei:Zeile | Fix-Aufwand |
|---|---------|---------|-------------|-------------|
| 1 | Module-Level `KBConfig.get_instance()` | 🔴 Kritisch | chroma_plugin.py:36, embedding_pipeline.py:32, chroma_integration.py:27 | 30 min |
| 2 | `sys.path.insert()` bei Import | 🟠 Wichtig | 3 Dateien | 15 min |
| 3 | Race Condition in `get_instance()` | 🟠 Wichtig | config.py:97-101 | 20 min |
| 4 | Logger-Cache Race Condition | 🟡 Niedrig | logger.py:119-137 | 10 min |

**Root Cause ist Problem #1:** Module-Level Side Effects erzwingen eine Import-Reihenfolge, die bei parallelen Imports (Threading, Testing, IPython) zu Deadlocks führt. Der Python-Import-Lock und die Application-Locks (`KBConfig._lock`) können sich gegenseitig blockieren.

**Gesamtaufwand für alle Fixes:** ~75 Minuten

---

## 9. Test-Plan

Nach dem Fix:

1. **Single-Thread Test:** `python -m kb sync` muss funktionieren
2. **Multi-Thread Test:** Reproducer von Abschnitt 6 muss 100× ohne Deadlock laufen
3. **Pytest:** Alle Tests müssen parallel laufen können
4. **Import Order Test:** Alle Permutationen von `import kb.base`, `import kb.library.knowledge_base`, `import kb.llm` müssen funktionieren
5. **Regression Test:** `KBConfig.get_instance()` darf keine Locks mehr bei Import halten

```python
# test_import_order.py
import itertools
import importlib
import sys

modules = ['kb.base', 'kb.base.config', 'kb.library.knowledge_base', 'kb.llm']

for perm in itertools.permutations(modules):
    # Clear all kb modules from sys.modules
    for key in list(sys.modules.keys()):
        if key.startswith('kb'):
            del sys.modules[key]
    KBConfig.reset()  # Reset singleton
    
    # Import in this order
    for mod in perm:
        importlib.import_module(mod)
    
    assert KBConfig._instance is not None
    print(f"✅ Order: {' → '.join(perm)}")
```

---

*Erstellt von Sir Stern 🔍 — Qualitätssicherung ist keine Option, es ist eine Pflicht.*