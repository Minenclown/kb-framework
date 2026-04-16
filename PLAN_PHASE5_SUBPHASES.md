# Phase 5 — Sub-Phasen Plan

**Erstellt:** 2026-04-16
**Status:** Bereit zur Ausführung

---

## Aktueller Status

| Komponente | Status | Datei |
|---|---|---|
| TransformersEngine | ✅ Kompiliert | `kb/llm/engine/transformers_engine.py` (~600 Zeilen) |
| Engine Factory | ✅ Existiert | `kb/llm/engine/factory.py` |
| Engine `__init__.py` | ✅ Exportiert | `kb/llm/engine/__init__.py` |
| OllamaEngine Tests | ✅ Existiert | `tests/test_llm/test_engine.py` (~250 Zeilen) |
| Conftest (Ollama) | ✅ Existiert | `tests/test_llm/conftest.py` (~180 Zeilen) |
| TransformersEngine Tests | ❌ Fehlt | — |
| Dokumentation | ❌ Fehlt | — |
| CLI Engine-Commands | ❌ Fehlt | — |
| Version | ❌ 1.1.1 | `kb/version.py`, `kb/__init__.py` |

---

## Sub-Phase 5a: Tests

**Dauer:** 15–20 Minuten
**Abhängigkeiten:** Keine (TransformersEngine existiert bereits)
**Kontext-Fenster:** ~3.500 Tokens (Quellcode) + ~1.500 Tokens (neue Tests) = **~5.000 Tokens**

### Neue Datei: `tests/test_llm/test_transformers_engine.py`

**~300 Zeilen**

```python
# Struktur:
# - Imports + Fixtures (oben, nutzt conftest.py)
# - 7 Test-Klassen mit je 1–3 Methoden
```

#### Test-Klassen und Methoden

| # | Klasse | Methode | Was wird getestet | Mocking |
|---|--------|---------|-------------------|---------|
| 1 | `TestTransformersEngineInit` | `test_init_defaults` | Konstruktor ohne Config nutzt get_llm_config() | `patch(get_llm_config)` |
| 2 | `TestTransformersEngineInit` | `test_init_with_config` | Konstruktor mit explizitem LLMConfig | — |
| 3 | `TestTransformersEngineInit` | `test_model_not_loaded_at_init` | `_model_loaded` ist False nach __init__ | — |
| 4 | `TestAvailability` | `test_is_available_with_deps` | torch+transformers importierbar → True | `patch(imports)` |
| 5 | `TestAvailability` | `test_is_available_without_torch` | torch fehlt → False | `patch.dict(sys.modules, {"torch": None})` |
| 6 | `TestAvailability` | `test_is_available_without_transformers` | transformers fehlt → False | `patch.dict(sys.modules)` |
| 7 | `TestProviderAndName` | `test_get_provider` | `get_provider()` == `LLMProvider.HUGGINGFACE` | — |
| 8 | `TestProviderAndName` | `test_get_model_name` | `get_model_name()` == config.hf_model_name | — |
| 9 | `TestProviderAndName` | `test_supports_streaming` | `supports_streaming` == True | — |
| 10 | `TestProviderAndName` | `test_supports_async` | `supports_async` == True | — |
| 11 | `TestLoadModel` | `test_load_model_calls_do_load` | load_model() ruft _do_load_model() | `patch(_do_load_model)` |
| 12 | `TestLoadModel` | `test_load_model_thread_safe` | 2× load_model → _do_load_model nur 1× | Threading-Test |
| 13 | `TestLoadModel` | `test_load_model_already_loaded_skip` | _model_loaded=True → skip | — |
| 14 | `TestGenerate` | `test_generate_success` | generate() mit gemocktem Model → LLMResponse | `patch(_ensure_model_loaded)`, Mock-Model |
| 15 | `TestGenerate` | `test_generate_respects_temperature` | temperature=0 → do_sample=False | Mock-Model |
| 16 | `TestGenerate` | `test_generate_oom_raises` | OOM → TransformersGenerationError | Mock-Model wirft OOM |
| 17 | `TestGenerateAsync` | `test_generate_async_returns_response` | generate_async() → LLMResponse | `patch(generate)` |
| 18 | `TestUnloadModel` | `test_unload_clears_state` | unload_model() → _model=None, _model_loaded=False | — |
| 19 | `TestUnloadModel` | `test_unload_calls_empty_cache` | unload_model() ruft torch.cuda.empty_cache | `patch(torch.cuda)` |
| 20 | `TestRepr` | `test_repr_not_loaded` | `repr()` zeigt "not loaded" | — |
| 21 | `TestRepr` | `test_repr_loaded` | `repr()` zeigt "loaded" | `_model_loaded=True` |

#### Fixtures (in `conftest.py` erweitern)

Neue Fixtures am Ende der existierenden `tests/test_llm/conftest.py`:

```python
@pytest.fixture
def hf_config(llm_config):
    """Create LLMConfig with model_source=huggingface."""
    LLMConfig.reset()
    config = LLMConfig(
        model_source="huggingface",
        hf_model_name="test-model/tiny-model",
        hf_device="cpu",
        hf_quantization=None,
        skip_validation=True,
    )
    return config

@pytest.fixture
def transformers_engine(hf_config):
    """Create TransformersEngine with mocked dependencies."""
    from kb.llm.engine.transformers_engine import TransformersEngine
    engine = TransformersEngine(config=hf_config)
    return engine

@pytest.fixture
def mock_torch():
    """Mock torch module for dependency tests."""
    mock = MagicMock()
    mock.__version__ = "2.4.0"
    mock.cuda.is_available.return_value = False
    mock.cuda.is_bf16_supported.return_value = False
    mock.backends.mps.is_available.return_value = False
    return mock

@pytest.fixture
def mock_transformers():
    """Mock transformers module for dependency tests."""
    mock = MagicMock()
    mock.__version__ = "4.44.0"
    return mock

@pytest.fixture
def loaded_engine(transformers_engine):
    """Create TransformersEngine with fake-loaded model for generate tests."""
    mock_model = MagicMock()
    mock_model.generate.return_value = [[1, 2, 3, 4, 5]]  # fake token ids
    mock_tokenizer = MagicMock()
    mock_tokenizer.return_value = {"input_ids": MagicMock(shape=MagicMock(return_value=(1, 3)))}
    mock_tokenizer.decode.return_value = "Generated text"
    mock_tokenizer.pad_token = None
    mock_tokenizer.eos_token = "<eos>"
    
    transformers_engine._model = mock_model
    transformers_engine._tokenizer = mock_tokenizer
    transformers_engine._model_loaded = True
    transformers_engine._device = MagicMock()
    transformers_engine._device.type = "cpu"
    return transformers_engine
```

**Zeilen-Schätzung conftest.py:** +45 Zeilen (insgesamt ~225)

### Ausführung

1. `tests/test_llm/conftest.py` — 4 neue Fixtures anhängen
2. `tests/test_llm/test_transformers_engine.py` — Neue Datei erstellen
3. `pytest tests/test_llm/test_transformers_engine.py -v` — Validierung

### Validierung

```bash
pytest tests/test_llm/test_transformers_engine.py -v
# Erwartet: 15–21 Tests bestanden
```

---

## Sub-Phase 5b: Dokumentation

**Dauer:** 15–20 Minuten
**Abhängigkeiten:** Sub-Phase 5a sollte abgeschlossen sein (Doku referenziert Test-Struktur)
**Kontext-Fenster:** ~2.000 Tokens (README-Input) + ~2.000 Tokens (neuer Content) = **~4.000 Tokens**

### Neue Datei: `TRANSFORMERS_ENGINE.md`

**~150 Zeilen**

```markdown
# TransformersEngine — HuggingFace In-Process LLM

## Overview
- Was ist TransformersEngine?
- Vergleich: OllamaEngine vs TransformersEngine

## Quick Start
- Installation (requirements-transformers.txt)
- Konfiguration (LLMConfig mit model_source="huggingface")
- Erster generate()-Aufruf

## Konfiguration
- LLMConfig HF-Parameter (hf_model_name, hf_device, hf_quantization, etc.)
- Tabelle aller Parameter mit Defaults

## Features
- Auto Device Detection (CUDA > MPS > CPU)
- Quantization (4-bit NF4, 8-bit)
- Streaming (TextIteratorStreamer)
- Async (ThreadPoolExecutor)
- OOM Fallback (GPU → CPU)
- Batch Processing
- Chat Templates

## API Reference
- TransformersEngine Methoden (generate, generate_async, generate_stream, etc.)
- LLMResponse / LLMStreamChunk
- Exceptions

## CLI Usage
- `kb llm engine list`
- `kb llm engine info <name>`

## Testing
- Test-Struktur (test_transformers_engine.py)
- Mock-Only, keine echten Modelle

## Troubleshooting
- OOM-Fehler → Quantization oder kleineres Modell
- ImportError → pip install torch transformers
- Langsam auf CPU → Normal, Quantization hilft nicht auf CPU
```

### README.md Erweiterung

**+50 Zeilen** — Neuer Abschnitt nach "Quick Start":

```markdown
### 🤗 HuggingFace Transformers (In-Process)

KB Framework supports loading HuggingFace models directly in-process —
no external server needed.

```bash
# Install HuggingFace dependencies
pip install -r requirements-transformers.txt

# Configure
export KB_LLM_MODEL_SOURCE=huggingface
export KB_LLM_HF_MODEL_NAME=google/gemma-2-2b-it
export KB_LLM_HF_QUANTIZATION=4bit

# Use
kb llm generate essence "My Topic"
```

Supported features:
- **Auto device detection**: CUDA → MPS → CPU
- **Quantization**: 4-bit (NF4) and 8-bit via bitsandbytes
- **Streaming**: Token-by-token generation
- **OOM fallback**: Automatic GPU → CPU on out-of-memory

See [TRANSFORMERS_ENGINE.md](TRANSFORMERS_ENGINE.md) for full documentation.
```

### CHANGELOG.md — Neuer Eintrag

**+20 Zeilen** am Anfang der Datei (vor `[1.1.1]`):

```markdown
## [1.2.0] - 2026-04-16

### Features
- **TransformersEngine**: HuggingFace in-process LLM engine with quantization, streaming, and OOM fallback
- **Engine Factory**: Unified `create_engine()` factory for OllamaEngine / TransformersEngine
- **CLI Engine Commands**: `kb llm engine list` and `kb llm engine info <name>`
- **Comprehensive Tests**: 21 mock-based tests for TransformersEngine

### Changed
- Version bump: 1.1.1 → 1.2.0
- LLMConfig: Added HuggingFace parameters (hf_model_name, hf_device, hf_quantization, etc.)
- `kb/llm/engine/__init__.py`: Exports TransformersEngine and exceptions
```

### Ausführung

1. `TRANSFORMERS_ENGINE.md` — Neue Datei (~150 Zeilen)
2. `README.md` — HuggingFace-Abschnitt nach "Quick Start" einfügen
3. `CHANGELOG.md` — v1.2.0 Eintrag am Anfang
4. Badge in README.md: `version-1.1.1` → `version-1.2.0`

---

## Sub-Phase 5c: CLI + Version

**Dauer:** 10–15 Minuten
**Abhängigkeiten:** Sub-Phase 5b (CHANGELOG referenziert v1.2.0)
**Kontext-Fenster:** ~5.000 Tokens (llm.py-Input) + ~1.500 Tokens (neuer Code) = **~6.500 Tokens**

### CLI: `kb/commands/llm.py` Erweiterung

**+80 Zeilen** — Neuer Subcommand `engine`

#### Neuer Subparser in `add_arguments()`:

```python
# 7. engine list|info
eng = sub.add_parser("engine", help="Verfügbare LLM-Engines anzeigen")
eng_sub = eng.add_subparsers(dest="engine_action", help="Engine-Aktionen")

# engine list
eng_sub.add_parser("list", help="Alle verfügbaren Engines auflisten")

# engine info <name>
eng_info = eng_sub.add_parser("info", help="Details zu einem Engine")
eng_info.add_argument("engine_name", choices=["ollama", "huggingface"],
                       help="Engine-Name")
```

#### Neue Methoden in `LLMCommand`:

```python
def _cmd_engine(self) -> int:
    """Engine-Info anzeigen."""
    action = getattr(self._args, "engine_action", None)
    if action == "list":
        return self._engine_list()
    elif action == "info":
        return self._engine_info()
    else:
        self.print_error("engine-Aktion: list | info <name>")
        return self.EXIT_VALIDATION_ERROR

def _engine_list(self) -> int:
    """Alle verfügbaren Engines auflisten."""
    from kb.llm.engine import OllamaEngine, TransformersEngine
    
    engines = [
        {"name": "ollama", "class": "OllamaEngine", "module": "kb.llm.engine.ollama_engine"},
        {"name": "huggingface", "class": "TransformersEngine", "module": "kb.llm.engine.transformers_engine"},
    ]
    
    print("\n  🔧  Verfügbare LLM-Engines\n")
    for e in engines:
        # Check availability
        try:
            if e["name"] == "ollama":
                available = OllamaEngine.get_instance().is_available()
            else:
                engine = TransformersEngine()
                available = engine.is_available()
        except Exception:
            available = False
        
        icon = "✅" if available else "❌"
        print(f"  {icon}  {e['name']:15s}  ({e['class']})")
        print(f"     Module: {e['module']}")
    
    active = self._get_active_engine_name()
    print(f"\n  Aktiver Engine: {active}\n")
    return self.EXIT_SUCCESS

def _engine_info(self) -> int:
    """Details zu einem Engine anzeigen."""
    name = self._args.engine_name
    
    print(f"\n  🔧  Engine: {name}\n")
    print("  " + "-" * 40)
    
    if name == "ollama":
        from kb.llm.engine import OllamaEngine
        try:
            engine = OllamaEngine.get_instance()
            print(f"  Klasse:       OllamaEngine")
            print(f"  Verfügbar:    {'✅' if engine.is_available() else '❌'}")
            print(f"  Modell:       {engine.get_model_name()}")
            print(f"  Provider:     {engine.get_provider().value}")
            print(f"  Streaming:    {'✅' if engine.supports_streaming else '❌'}")
            print(f"  Async:        {'✅' if engine.supports_async else '❌'}")
        except Exception as e:
            print(f"  ❌ Engine nicht verfügbar: {e}")
    
    elif name == "huggingface":
        from kb.llm.engine import TransformersEngine
        try:
            engine = TransformersEngine()
            config = engine._config
            print(f"  Klasse:       TransformersEngine")
            print(f"  Verfügbar:    {'✅' if engine.is_available() else '❌'}")
            print(f"  Modell:       {engine.get_model_name()}")
            print(f"  Provider:     {engine.get_provider().value}")
            print(f"  Device:       {config.hf_device}")
            print(f"  Quantization: {config.hf_quantization or 'Keine'}")
            print(f"  Dtype:        {config.hf_torch_dtype}")
            print(f"  Revision:     {config.hf_revision}")
            print(f"  Streaming:    {'✅' if engine.supports_streaming else '❌'}")
            print(f"  Async:        {'✅' if engine.supports_async else '❌'}")
            
            # GPU Stats
            gpu = engine.get_gpu_stats()
            if gpu.get("available"):
                print(f"\n  🖥️  GPU Stats:")
                for dev in gpu["devices"]:
                    print(f"     [{dev['index']}] {dev['name']}")
                    print(f"         Allocated: {dev['allocated_gb']} GiB / {dev['total_gb']} GiB")
                    print(f"         Free:      {dev['free_gb']} GiB")
            else:
                print(f"\n  🖥️  GPU: Nicht verfügbar (CPU-Modus)")
        except Exception as e:
            print(f"  ❌ Engine nicht verfügbar: {e}")
    
    print()
    return self.EXIT_SUCCESS

def _get_active_engine_name(self) -> str:
    """Aktiven Engine-Namen aus Config ermitteln."""
    try:
        from kb.llm.config import LLMConfig
        config = LLMConfig.get_instance()
        return config.model_source
    except Exception:
        return "unbekannt"
```

#### Dispatch erweitern:

In `_execute()` den `dispatch` dict erweitern:

```python
dispatch = {
    "status": self._cmd_status,
    "generate": self._cmd_generate,
    "watch": self._cmd_watch,
    "scheduler": self._cmd_scheduler,
    "list": self._cmd_list,
    "config": self._cmd_config,
    "engine": self._cmd_engine,   # ← NEU
}
```

### Version Bump

#### `kb/version.py`:

```python
VERSION = "1.2.0"   # war: "1.1.1"
```

#### `kb/__init__.py`:

Falls `__version__` existiert: Aktualisieren auf `"1.2.0"`.
Falls nicht: `__version__ = "1.2.0"` hinzufügen.

### Ausführung

1. `kb/commands/llm.py` — `engine` Subparser + 4 Methoden + dispatch-Eintrag
2. `kb/version.py` — `VERSION = "1.2.0"`
3. `kb/__init__.py` — `__version__ = "1.2.0"` (prüfen ob schon vorhanden)
4. `kb llm engine list` — Manueller Test
5. `kb llm engine info ollama` — Manueller Test
6. `kb llm engine info huggingface` — Manueller Test

### Validierung

```bash
# Version
python -c "from kb.version import VERSION; assert VERSION == '1.2.0'"

# CLI
kb llm engine list
kb llm engine info ollama
kb llm engine info huggingface

# Alle Tests
pytest tests/test_llm/ -v
```

---

## Abhängigkeits-Graph

```
Sub-Phase 5a (Tests)
    ↓
Sub-Phase 5b (Doku) ← referenziert Test-Struktur
    ↓
Sub-Phase 5c (CLI + Version) ← CHANGELOG referenziert v1.2.0
```

- **5a → 5b**: Doku referenziert Test-Methoden und -Struktur
- **5b → 5c**: CHANGELOG und Version müssen konsistent sein
- **5a → 5c**: CLI `engine info` zeigt `is_available()` → Tests verifizieren dieses Verhalten

**Streng sequentiell ausführen.** Keine Parallelität.

---

## Gesamt-Zusammenfassung

| Sub-Phase | Neue Dateien | Geänderte Dateien | Neue Zeilen | Kontext |
|-----------|-------------|-------------------|-------------|---------|
| 5a | 1 (`test_transformers_engine.py`) | 1 (`conftest.py`) | ~345 | ~5.000 Tokens |
| 5b | 1 (`TRANSFORMERS_ENGINE.md`) | 3 (`README.md`, `CHANGELOG.md`, Badge) | ~220 | ~4.000 Tokens |
| 5c | 0 | 3 (`llm.py`, `version.py`, `__init__.py`) | ~85 | ~6.500 Tokens |
| **Total** | **2** | **7** | **~650** | **~15.500 Tokens** |

### Risiken

| Risiko | Wahrscheinlichkeit | Mitigation |
|--------|-------------------|------------|
| Mock-Setup für torch/transformers tricky | Mittel | `patch.dict(sys.modules)` statt `patch(import)` |
| `conftest.py` Fixtures kollidieren mit Ollama-Tests | Niedrig | Neue Fixtures nutzen `hf_config` (eigener Namespace) |
| `engine info` braucht echten Import | Niedrig | Try/except mit graceful fallback |
| `__version__` existiert noch nicht in `__init__.py` | Mittel | Prüfen, ggf. neu anlegen |

---

## Checkliste

- [ ] **5a.1** `tests/test_llm/conftest.py` — 4 neue Fixtures
- [ ] **5a.2** `tests/test_llm/test_transformers_engine.py` — Neue Datei
- [ ] **5a.3** `pytest tests/test_llm/test_transformers_engine.py -v` — Grün
- [ ] **5b.1** `TRANSFORMERS_ENGINE.md` — Neue Datei (~150 Zeilen)
- [ ] **5b.2** `README.md` — HuggingFace-Abschnitt + Badge-Update
- [ ] **5b.3** `CHANGELOG.md` — v1.2.0 Eintrag
- [ ] **5c.1** `kb/commands/llm.py` — `engine` Subcommand + Methoden
- [ ] **5c.2** `kb/version.py` — VERSION = "1.2.0"
- [ ] **5c.3** `kb/__init__.py` — __version__ = "1.2.0"
- [ ] **5c.4** `kb llm engine list` — Manueller Test
- [ ] **5c.5** `pytest tests/test_llm/ -v` — Alle Tests bestanden