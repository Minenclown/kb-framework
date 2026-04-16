# Phase 3 - Teil 1: Generator Base Interface - Status

**Datum:** 2026-04-16
**Status:** ✅ ABGESCHLOSSEN

## Erstellte Datei
- `kb/biblio/generator/base.py`

## Inhalt
- `BaseGeneratorError` - Basis-Exception für Generatoren
- `BaseGenerator(ParallelMixin, ABC)` - Abstrakte Basisklasse
  - `__init__` mit LLMConfig, Engine, Registry
  - `_generate_with_retry()` - Retry-Logik mit Exponential Backoff
  - `_get_engine()` - Engine-Zugriff (Registry oder stored)
  - `parallel_mode`, `parallel_strategy`, `model_source` Properties
  - `primary_model_name`, `secondary_model_name` Properties
  - `get_status()` - Status-Information
- `generate()` - Abstrakte Methode (muss von Subklassen implementiert werden)

## Parallel-Unterstützung
- Erbt von `ParallelMixin` → `__init_parallel__()` wird aufgerufen
- `parallel_mode` Parameter in Config
- `parallel_strategy`: "primary_first", "aggregate", "compare"
- Engine-Registry für primären und sekundären Engine

## Syntax-Check
- ✅ `python3 -m py_compile kb/biblio/generator/base.py` → OK

## Import-Test
- ⏳ Noch nicht möglich (hängt an OllamaEngine-Import im Runtime-Umfeld)
- Syntax ist korrekt, Module lädt isoliert