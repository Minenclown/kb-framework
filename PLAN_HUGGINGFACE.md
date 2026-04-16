# PLAN_HUGGINGFACE.md — TransformersEngine Implementierungsplan

> Erstellt: 2026-04-16 | Status: DRAFT
> Ziel: Alternative zu OllamaEngine — direktes Laden von Modellen via HuggingFace Transformers

---

## Überblick

| Aspekt | Detail |
|--------|--------|
| **Ziel** | `TransformersEngine` als zweite `BaseLLMEngine`-Implementation |
| **Vorbild** | `kb/llm/engine/ollama_engine.py` (455 Zeilen) |
| **Interface** | `kb/llm/engine/base.py` — `BaseLLMEngine` ABC |
| **Neue Dateien** | 5 (Engine, Config-Erweiterung, Exceptions, Tests, Docs) |
| **Geänderte Dateien** | 3 (`base.py`, `config.py`, `engine/__init__.py`) |
| **Geschätzter Gesamtaufwand** | ~1.200–1.500 LOC neu, ~150 LOC geändert |

---

## Phase 1: Grundstruktur (Engine, Config, Provider)

**Ziel:** Projekt kann `TransformersEngine` instanziieren, `is_available()` und `get_model_name()` funktionieren. Noch kein echtes Model-Loading.

### 1.1 `LLMProvider` erweitern

**Datei:** `kb/llm/engine/base.py` (~3 Zeilen Änderung)

```python
class LLMProvider(Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    HUGGINGFACE = "huggingface"   # ← NEU
    MOCK = "mock"
```

### 1.2 `LLMConfig` erweitern

**Datei:** `kb/llm/config.py` (~50 Zeilen Änderung)

Neue Felder (mit Env-Var-Overrides):

| Feld | Typ | Default | Env-Var |
|------|-----|---------|---------|
| `model_source` | `str` | `"ollama"` | `KB_LLM_MODEL_SOURCE` |
| `hf_model_name` | `str` | `"google/gemma-2-2b-it"` | `KB_LLM_HF_MODEL` |
| `hf_revision` | `str` | `"main"` | `KB_LLM_HF_REVISION` |
| `hf_token` | `Optional[str]` | `None` | `HF_TOKEN` |
| `hf_cache_dir` | `Optional[str]` | `None` | `HF_HOME` / `KB_LLM_HF_CACHE` |
| `hf_quantization` | `Optional[str]` | `None` | `KB_LLM_HF_QUANT` |
| `hf_device` | `str` | `"auto"` | `KB_LLM_HF_DEVICE` |
| `hf_dtype` | `str` | `"auto"` | `KB_LLM_HF_DTYPE` |

**Wichtige Designentscheidungen:**

- `model_source` steuert, welche Engine der Factory zurückgibt (`"ollama"` → `OllamaEngine`, `"huggingface"` → `TransformersEngine`)
- `hf_quantization` Werte: `None` (FP32/FP16), `"4bit"`, `"8bit"`
- `hf_device` Werte: `"auto"`, `"cuda"`, `"cuda:0"`, `"cuda:1"`, `"mps"`, `"cpu"`
- `hf_dtype` Werte: `"auto"`, `"float16"`, `"bfloat16"`, `"float32"`

**Validierung hinzufügen:**

```python
def _validate_hf_config(self) -> None:
    if self.model_source == "huggingface":
        if not self.hf_model_name:
            raise LLMConfigError("hf_model_name required when model_source=huggingface")
        if self.hf_quantization not in (None, "4bit", "8bit"):
            raise LLMConfigError(f"Invalid quantization: {self.hf_quantization}")
        if self.hf_device not in ("auto", "cpu", "cuda", "mps") and not self.hf_device.startswith("cuda:"):
            raise LLMConfigError(f"Invalid device: {self.hf_device}")
```

### 1.3 `TransformersEngine` Skeleton

**Datei:** `kb/llm/engine/transformers_engine.py` (~120 Zeilen)

```python
class TransformersEngineError(Exception): ...
class TransformersModelLoadError(TransformersEngineError): ...
class TransformersGenerationError(TransformersEngineError): ...

class TransformersEngine(BaseLLMEngine):
    """
    HuggingFace Transformers LLM Engine.
    
    Loads models directly via transformers library.
    No external server required — model runs in-process.
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        self._config = config or get_llm_config()
        self._model = None          # transformers.PreTrainedModel
        self._tokenizer = None      # transformers.PreTrainedTokenizer
        self._executor = None       # ThreadPoolExecutor
        self._device = None         # torch.device
        self._model_loaded = False
    
    def get_model_name(self) -> str:
        return self._config.hf_model_name
    
    def get_provider(self) -> LLMProvider:
        return LLMProvider.HUGGINGFACE
    
    def is_available(self) -> bool:
        # Check: transformers installed? Model loaded or loadable? Device available?
        ...
    
    @property
    def supports_streaming(self) -> bool:
        return True  # via TextIteratorStreamer
    
    @property
    def supports_async(self) -> bool:
        return True  # via ThreadPoolExecutor
```

### 1.4 Engine-Package Update

**Datei:** `kb/llm/engine/__init__.py` (~5 Zeilen Änderung)

```python
from kb.llm.engine.transformers_engine import (
    TransformersEngine,
    TransformersEngineError,
    TransformersModelLoadError,
)
```

### 1.5 Engine-Factory (optional, aber empfohlen)

**Datei:** `kb/llm/engine/factory.py` (~30 Zeilen neu)

```python
def create_engine(config: Optional[LLMConfig] = None) -> BaseLLMEngine:
    config = config or get_llm_config()
    if config.model_source == "ollama":
        return OllamaEngine(config)
    elif config.model_source == "huggingface":
        return TransformersEngine(config)
    else:
        raise LLMConfigError(f"Unknown model_source: {config.model_source}")
```

### Phase 1 Deliverables

| Datei | Typ | LOC |
|-------|-----|-----|
| `kb/llm/engine/base.py` | Geändert | ~3 |
| `kb/llm/config.py` | Geändert | ~50 |
| `kb/llm/engine/transformers_engine.py` | Neu | ~120 |
| `kb/llm/engine/__init__.py` | Geändert | ~5 |
| `kb/llm/engine/factory.py` | Neu | ~30 |
| **Summe** | | **~208** |

### Phase 1 Abhängigkeiten

- Keine neuen Python-Packages (nur Skeleton)
- `torch` und `transformers` werden importiert mit Lazy-Import / optionalem Import

### Phase 1 Test-Kriterien

- [ ] `TransformersEngine()` instanziierbar (ohne dass transformers installiert ist)
- [ ] `LLMConfig(model_source="huggingface")` funktioniert
- [ ] `LLMConfig`-Validierung schlägt fehl bei ungültigen hf_-Werten
- [ ] `factory.create_engine()` liefert korrekte Engine je nach `model_source`
- [ ] `is_available()` gibt `False` wenn transformers nicht installiert

---

## Phase 2: Model-Loading + Caching

**Ziel:** `TransformersEngine` lädt Modelle von HuggingFace Hub, cached lokal, unterstützt Quantization.

### 2.1 Lazy Imports + Dependency Check

In `transformers_engine.py`:

```python
def _check_dependencies(self) -> None:
    """Check if required packages are installed."""
    try:
        import torch
        import transformers
        self._torch_version = torch.__version__
        self._transformers_version = transformers.__version__
    except ImportError as e:
        raise TransformersEngineError(
            f"Missing dependency: {e}. "
            f"Install with: pip install torch transformers"
        )
```

### 2.2 Device-Erkennung

```python
def _detect_device(self) -> "torch.device":
    """
    Auto-detect best available device.
    Priority: CUDA > MPS > CPU
    """
    import torch
    
    device_str = self._config.hf_device
    
    if device_str == "auto":
        if torch.cuda.is_available():
            return torch.device("cuda")
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return torch.device("mps")
        else:
            return torch.device("cpu")
    
    return torch.device(device_str)
```

### 2.3 Model-Loading

```python
def _load_model(self) -> None:
    """
    Load model and tokenizer from HuggingFace Hub.
    
    Features:
    - Auto-download on first use (HF Hub caching)
    - Revision pinning for reproducibility
    - Quantization (4-bit/8-bit via bitsandbytes)
    - Device placement (auto/cuda/cpu/mps)
    - dtype selection (float16/bfloat16/auto)
    """
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    
    if self._model_loaded:
        return
    
    # Device & dtype
    self._device = self._detect_device()
    dtype = self._resolve_dtype()
    
    # Quantization config
    quantization_config = self._build_quantization_config()
    
    # Load tokenizer
    tokenizer_kwargs = {
        "revision": self._config.hf_revision,
        "token": self._config.hf_token,
    }
    if self._config.hf_cache_dir:
        tokenizer_kwargs["cache_dir"] = self._config.hf_cache_dir
    
    self._tokenizer = AutoTokenizer.from_pretrained(
        self._config.hf_model_name,
        **tokenizer_kwargs
    )
    
    # Ensure pad token exists
    if self._tokenizer.pad_token is None:
        self._tokenizer.pad_token = self._tokenizer.eos_token
    
    # Load model
    model_kwargs = {
        "revision": self._config.hf_revision,
        "token": self._config.hf_token,
        "torch_dtype": dtype,
        "device_map": "auto" if self._config.hf_device == "auto" else None,
    }
    if self._config.hf_cache_dir:
        model_kwargs["cache_dir"] = self._config.hf_cache_dir
    if quantization_config:
        model_kwargs["quantization_config"] = quantization_config
    
    self._model = AutoModelForCausalLM.from_pretrained(
        self._config.hf_model_name,
        **model_kwargs
    )
    
    # Place on device if not using device_map
    if self._config.hf_device != "auto" and quantization_config is None:
        self._model = self._model.to(self._device)
    
    self._model.eval()  # Inference mode
    self._model_loaded = True
```

### 2.4 Quantization Support

```python
def _build_quantization_config(self) -> Optional["BitsAndBytesConfig"]:
    """
    Build quantization config based on settings.
    
    Supports:
    - "4bit": NF4 quantization with double quantization
    - "8bit": LLM.int8() quantization
    """
    if self._config.hf_quantization is None:
        return None
    
    try:
        from transformers import BitsAndBytesConfig
    except ImportError:
        raise TransformersEngineError(
            "Quantization requires bitsandbytes. "
            "Install with: pip install bitsandbytes"
        )
    
    if self._config.hf_quantization == "4bit":
        return BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=self._resolve_dtype(),
            bnb_4bit_use_double_quantization=True,
        )
    elif self._config.hf_quantization == "8bit":
        return BitsAndBytesConfig(load_in_8bit=True)
    
    return None
```

### 2.5 dtype Resolution

```python
def _resolve_dtype(self) -> "torch.dtype":
    """Resolve torch dtype from config string."""
    import torch
    
    dtype_str = self._config.hf_dtype
    if dtype_str == "auto":
        if torch.cuda.is_available() and torch.cuda.is_bf16_supported():
            return torch.bfloat16
        elif torch.cuda.is_available():
            return torch.float16
        return torch.float32
    
    dtype_map = {
        "float16": torch.float16,
        "bfloat16": torch.bfloat16,
        "float32": torch.float32,
    }
    if dtype_str not in dtype_map:
        raise TransformersEngineError(f"Invalid dtype: {dtype_str}")
    return dtype_map[dtype_str]
```

### 2.6 Model Unload (Memory Management)

```python
def unload_model(self) -> None:
    """Unload model from memory. Important for resource management."""
    import gc
    import torch
    
    if self._model is not None:
        del self._model
        self._model = None
    if self._tokenizer is not None:
        del self._tokenizer
        self._tokenizer = None
    
    self._model_loaded = False
    
    # Force GPU memory cleanup
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    
    gc.collect()
```

### 2.7 ThreadPoolExecutor für Async

```python
def _get_executor(self) -> "ThreadPoolExecutor":
    """Get or create thread pool for async operations."""
    from concurrent.futures import ThreadPoolExecutor
    
    if self._executor is None:
        max_workers = 1  # Model inference is sequential per model
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="hf_engine"
        )
    return self._executor
```

### Phase 2 Deliverables

| Datei | Typ | LOC |
|-------|-----|-----|
| `kb/llm/engine/transformers_engine.py` | Erweitert | ~250 |
| **Summe** | | **~250** |

### Phase 2 Abhängigkeiten

- `torch` (PyTorch) — CPU-only oder CUDA
- `transformers` (HuggingFace Transformers >= 4.36)
- `bitsandbytes` — optional, nur bei Quantization
- `accelerate` — optional, für `device_map="auto"` und Multi-GPU

### Phase 2 Risiken

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|------------|
| Erster Download sehr langsam (>10 GB) | Hoch | Mittel | Progress-Logging, HF_CACHE_DIR für geteiltes Caching |
| VRAM reicht nicht | Mittel | Hoch | Quantization als Default für Consumer-GPUs, CPU-Fallback |
| bitsandbytes nur Linux/CUDA | Mittel | Niedrig | Graceful Fallback: Quantization → Warnung → FP16/FP32 |
| Tokenizer-Inkompatibilität | Niedrig | Mittel | `trust_remote_code=False` als Default, Whitelist für bekannte Modelle |

### Phase 2 Test-Kriterien

- [ ] Modell lädt erfolgreich (ohne Quantization, CPU)
- [ ] Modell lädt mit 4-bit Quantization (CUDA)
- [ ] Automatischer Download bei fehlendem Cache funktioniert
- [ ] `unload_model()` gibt Speicher frei (`nvidia-smi` Check)
- [ ] `is_available()` korrekt nach Ladestatus
- [ ] HF_TOKEN wird für gated models berücksichtigt
- [ ] Ungültige model_name → klarer Error

---

## Phase 3: Generation + Streaming

**Ziel:** `generate()`, `generate_async()`, `generate_stream()`, `generate_stream_async()` funktionieren.

### 3.1 Text Generation (Sync)

```python
def generate(
    self,
    prompt: str,
    *,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    **kwargs
) -> LLMResponse:
    """
    Generate text synchronously.
    
    Pipeline:
    1. Tokenize input
    2. Forward pass through model
    3. Decode output tokens
    4. Return LLMResponse
    """
    import torch
    
    self._ensure_model_loaded()
    
    temp = temperature if temperature is not None else self._config.temperature
    max_new = max_tokens if max_tokens is not None else self._config.max_tokens
    
    # Tokenize
    inputs = self._tokenizer(prompt, return_tensors="pt")
    if self._device.type != "cpu":
        inputs = {k: v.to(self._device) for k, v in inputs.items()}
    
    # Generate
    start_time = time.time()
    
    gen_kwargs = {
        "max_new_tokens": max_new,
        "temperature": temp if temp > 0 else None,
        "do_sample": temp > 0,
    }
    
    # Handle greedy decoding (temperature=0)
    if temp == 0:
        gen_kwargs["do_sample"] = False
        gen_kwargs.pop("temperature", None)
    else:
        gen_kwargs["top_p"] = kwargs.get("top_p", 0.95)
    
    # Additional kwargs (repetition_penalty, etc.)
    for key in ("repetition_penalty", "top_k", "top_p"):
        if key in kwargs:
            gen_kwargs[key] = kwargs[key]
    
    with torch.no_grad():
        outputs = self._model.generate(**inputs, **gen_kwargs)
    
    # Decode (skip input tokens)
    input_len = inputs["input_ids"].shape[1]
    generated_tokens = outputs[0][input_len:]
    content = self._tokenizer.decode(generated_tokens, skip_special_tokens=True)
    
    duration_ns = int((time.time() - start_time) * 1e9)
    output_len = len(generated_tokens)
    
    return LLMResponse(
        content=content,
        model=self._config.hf_model_name,
        provider=LLMProvider.HUGGINGFACE,
        done=True,
        total_duration=duration_ns,
        tokens=output_len,
        context=input_len + output_len,
    )
```

### 3.2 Async Generation

```python
async def generate_async(
    self,
    prompt: str,
    *,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    **kwargs
) -> LLMResponse:
    """
    Async generation via ThreadPoolExecutor.
    Model inference is CPU/GPU-bound — offload to thread pool.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        self._get_executor(),
        functools.partial(
            self.generate,
            prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
    )
```

### 3.3 Streaming Generation

```python
def generate_stream(
    self,
    prompt: str,
    *,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    **kwargs
) -> Iterator[LLMStreamChunk]:
    """
    Stream tokens chunk-by-chunk using TextIteratorStreamer.
    """
    import torch
    from threading import Thread
    from transformers import TextIteratorStreamer
    
    self._ensure_model_loaded()
    
    temp = temperature if temperature is not None else self._config.temperature
    max_new = max_tokens if max_tokens is not None else self._config.max_tokens
    
    inputs = self._tokenizer(prompt, return_tensors="pt")
    if self._device.type != "cpu":
        inputs = {k: v.to(self._device) for k, v in inputs.items()}
    
    # Setup streamer
    streamer = TextIteratorStreamer(
        self._tokenizer,
        skip_prompt=True,
        skip_special_tokens=True,
    )
    
    gen_kwargs = {
        **inputs,
        "streamer": streamer,
        "max_new_tokens": max_new,
        "temperature": temp if temp > 0 else None,
        "do_sample": temp > 0,
    }
    
    if temp == 0:
        gen_kwargs["do_sample"] = False
        gen_kwargs.pop("temperature", None)
    
    # Run generation in background thread
    generation_thread = Thread(target=self._model.generate, kwargs=gen_kwargs)
    generation_thread.start()
    
    # Yield tokens as they arrive
    try:
        for text in streamer:
            if text:
                yield LLMStreamChunk(content=text, done=False)
    finally:
        generation_thread.join(timeout=30)
    
    yield LLMStreamChunk(content="", done=True)
```

### 3.4 Async Streaming

```python
async def generate_stream_async(
    self,
    prompt: str,
    *,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    **kwargs
) -> AsyncIterator[LLMStreamChunk]:
    """
    Async streaming — wraps sync stream via asyncio bridge.
    """
    loop = asyncio.get_event_loop()
    queue = asyncio.Queue()
    
    def run_stream():
        try:
            for chunk in self.generate_stream(
                prompt, temperature=temperature, max_tokens=max_tokens, **kwargs
            ):
                loop.call_soon_threadsafe(queue.put_nowait, chunk)
            loop.call_soon_threadsafe(queue.put_nowait, None)  # Signal done
        except Exception as e:
            loop.call_soon_threadsafe(queue.put_nowait, e)
    
    await loop.run_in_executor(self._get_executor(), run_stream)
    
    while True:
        chunk = await queue.get()
        if chunk is None:
            break
        if isinstance(chunk, Exception):
            raise chunk
        yield chunk
```

### 3.5 Helper: _ensure_model_loaded

```python
def _ensure_model_loaded(self) -> None:
    """Lazy-load model if not already loaded."""
    if not self._model_loaded:
        logger.info(f"Loading model {self._config.hf_model_name}...")
        self._load_model()
        logger.info(f"Model loaded on {self._device}")
```

### Phase 3 Deliverables

| Datei | Typ | LOC |
|-------|-----|-----|
| `kb/llm/engine/transformers_engine.py` | Erweitert | ~200 |
| **Summe** | | **~200** |

### Phase 3 Risiken

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|------------|
| Streaming-Thread hängt | Niedrig | Mittel | Timeout (30s) + Thread-Interrupt |
| `TextIteratorStreamer` nicht für alle Modelle verfügbar | Niedrig | Mittel | Fallback: non-streaming + chunked yield |
| Temperatur=0 nicht für alle Modelle | Niedrig | Niedrig | `do_sample=False` + `num_beams=1` |
| Tokenizer decode-Fehler | Niedrig | Niedrig | `skip_special_tokens=True` + `errors="replace"` |

### Phase 3 Test-Kriterien

- [ ] `generate()` liefert korrekten `LLMResponse`
- [ ] `generate_async()` funktioniert ohne Blocking
- [ ] `generate_stream()` liefert Chunks incrementally
- [ ] `generate_stream_async()` funktioniert in async Context
- [ ] Temperature=0 → deterministische Ausgabe
- [ ] `max_tokens` wird respektiert
- [ ] `LLMResponse.tokens` stimmt mit tatsächlicher Output-Länge überein
- [ ] Spezielle Token werden nicht im Output ausgegeben

---

## Phase 4: Batch Processing + Multi-GPU

**Ziel:** Effiziente Batch-Verarbeitung und Multi-GPU-Support.

### 4.1 Batch Generation

```python
def generate_batch(
    self,
    prompts: list[str],
    *,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    **kwargs
) -> list[LLMResponse]:
    """
    Generate responses for multiple prompts.
    
    Two strategies:
    1. Padded batch (if prompts are similar length)
    2. Sequential (fallback, safer for varying lengths)
    """
    self._ensure_model_loaded()
    
    # Strategy: Sequential for now (safer, memory-efficient)
    # Batch mode can be added later with padding + attention_mask
    results = []
    for prompt in prompts:
        response = self.generate(
            prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        results.append(response)
    
    return results
```

### 4.2 Multi-GPU Support

```python
def _get_device_map(self) -> Optional[dict]:
    """
    Build device_map for multi-GPU distribution.
    
    Options:
    - "auto" → transformers handles distribution via accelerate
    - "balanced" → evenly split across GPUs
    - "sequential" → fill GPU0, then GPU1, etc.
    - Custom dict → user-defined mapping
    """
    import torch
    
    if not torch.cuda.is_available():
        return None
    
    num_gpus = torch.cuda.device_count()
    if num_gpus <= 1:
        return None  # Single GPU, no need for device_map
    
    # Use accelerate's auto device map
    # This handles large models that don't fit on a single GPU
    if self._config.hf_device == "auto":
        return "auto"  # accelerate handles it
    
    # Specific multi-GPU config
    if self._config.hf_device == "balanced":
        return "balanced"
    
    return None
```

### 4.3 GPU Memory Monitoring

```python
def get_gpu_stats(self) -> dict:
    """Get current GPU memory usage for monitoring."""
    import torch
    
    if not torch.cuda.is_available():
        return {"available": False}
    
    stats = {"available": True, "devices": []}
    for i in range(torch.cuda.device_count()):
        allocated = torch.cuda.memory_allocated(i) / 1024**3  # GB
        reserved = torch.cuda.memory_reserved(i) / 1024**3    # GB
        total = torch.cuda.get_device_properties(i).total_memory / 1024**3
        
        stats["devices"].append({
            "index": i,
            "name": torch.cuda.get_device_name(i),
            "allocated_gb": round(allocated, 2),
            "reserved_gb": round(reserved, 2),
            "total_gb": round(total, 2),
            "free_gb": round(total - reserved, 2),
        })
    
    return stats
```

### 4.4 Chat Template Support

```python
def _apply_chat_template(
    self,
    messages: list[dict],
    **kwargs
) -> str:
    """
    Apply model's chat template to messages.
    
    Uses tokenizer.apply_chat_template if available.
    Falls back to manual formatting for models without templates.
    """
    self._ensure_model_loaded()
    
    if hasattr(self._tokenizer, 'apply_chat_template'):
        return self._tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            **kwargs
        )
    
    # Fallback: simple format
    formatted = ""
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        formatted += f"<|{role}|>\n{content}\n"
    formatted += "<|assistant|>\n"
    
    return formatted
```

### Phase 4 Deliverables

| Datei | Typ | LOC |
|-------|-----|-----|
| `kb/llm/engine/transformers_engine.py` | Erweitert | ~180 |
| **Summe** | | **~180** |

### Phase 4 Abhängigkeiten

- `accelerate` — für `device_map="auto"` und Multi-GPU (optional)
- `bitsandbytes` — für Quantization auf Multi-GPU (optional)

### Phase 4 Risiken

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|------------|
| Multi-GPU OOM | Mittel | Hoch | `max_memory` Parameter, auto-sharding |
| Batch-Padding ineffizient | Mittel | Mittel | Sequential als Default, Batch optional |
| Chat-Template fehlt für exotische Modelle | Mittel | Niedrig | Fallback manuelles Format |
| accelerate nicht installiert | Mittel | Mittel | Graceful Degradation → Single GPU |

### Phase 4 Test-Kriterien

- [ ] `generate_batch()` verarbeitet mehrere Prompts korrekt
- [ ] Multi-GPU: Modell wird auf beide GPUs verteilt
- [ ] `get_gpu_stats()` liefert korrekte Speicher-Statistiken
- [ ] Chat-Template wird korrekt angewendet
- [ ] Fallback bei fehlendem Chat-Template funktioniert

---

## Phase 5: Tests + Dokumentation

**Ziel:** Vollständige Testabdeckung und Dokumentation.

### 5.1 Unit Tests

**Datei:** `kb/llm/engine/test_transformers_engine.py` (~250 Zeilen)

**Test-Kategorien:**

| Kategorie | Tests | Beschreibung |
|-----------|-------|-------------|
| **Config** | 5 | `LLMConfig` hf_-Felder, Validierung, Env-Var-Overrides |
| **Instantiation** | 3 | Engine erstellen, Abhängigkeiten prüfen |
| **Model Loading** | 4 | Load, Reload, Unload, Error-Handling |
| **Generation** | 5 | Sync, Async, Temperature, Max-Tokens, Edge Cases |
| **Streaming** | 4 | Sync-Stream, Async-Stream, Chunk-Integrität, Completion |
| **Batch** | 3 | Single, Multiple, Error-in-Batch |
| **Device** | 3 | Auto-Detection, CPU-Fallback, GPU-Stats |
| **Factory** | 2 | Ollama-Factory, HF-Factory |

**Test-Fixture:** Small model für Integration-Tests

```python
# Für Integration-Tests: kleines Modell
TEST_MODEL = "sshleifer/tiny-gpt2"  # ~50MB, ausreichend für Smoke Tests
```

### 5.2 Mock Tests (ohne GPU)

```python
class TestTransformersEngineMock:
    """Tests that don't require actual model loading."""
    
    def test_is_available_no_transformers(self):
        """Should return False if transformers not installed."""
        # Patch import
        ...
    
    def test_config_validation_hf(self):
        """Test HuggingFace-specific config validation."""
        ...
    
    def test_factory_creates_hf_engine(self):
        """Factory should create TransformersEngine for model_source=huggingface."""
        ...
```

### 5.3 Dokumentation

**Datei:** `kb/llm/engine/TRANSFORMERS_ENGINE.md` (~200 Zeilen)

Inhalt:
- Überblick und Architecture
- Quick-Start Guide
- Konfiguration-Referenz (alle hf_-Felder)
- Quantization-Optionen erklärt
- Multi-GPU Setup
- Memory-Management (unload_model)
- Troubleshooting
- Vergleich: OllamaEngine vs TransformersEngine

### 5.4 README-Update

**Datei:** `README.md` (kurzer Abschnitt)

```markdown
### HuggingFace Transformers Engine

Run models directly without Ollama server:

```bash
export KB_LLM_MODEL_SOURCE=huggingface
export KB_LLM_HF_MODEL=google/gemma-2-2b-it
export KB_LLM_HF_QUANT=4bit
kb llm generate "Explain quantum computing"
```
```

### Phase 5 Deliverables

| Datei | Typ | LOC |
|-------|-----|-----|
| `kb/llm/engine/test_transformers_engine.py` | Neu | ~250 |
| `kb/llm/engine/TRANSFORMERS_ENGINE.md` | Neu | ~200 |
| `README.md` | Geändert | ~15 |
| **Summe** | | **~465** |

### Phase 5 Test-Kriterien

- [ ] Alle Unit-Tests grün (Mock + Integration)
- [ ] Coverage > 80% für `transformers_engine.py`
- [ ] Dokumentation vollständig und aktuell
- [ ] Quick-Start im README funktioniert

---

## Gesamtübersicht

### LOC-Schätzung pro Phase

| Phase | Fokus | Neue LOC | Geänderte LOC | Gesamt |
|-------|-------|----------|---------------|--------|
| **1** | Grundstruktur | ~150 | ~58 | ~208 |
| **2** | Model-Loading | ~250 | 0 | ~250 |
| **3** | Generation + Streaming | ~200 | 0 | ~200 |
| **4** | Batch + Multi-GPU | ~180 | 0 | ~180 |
| **5** | Tests + Docs | ~450 | ~15 | ~465 |
| **Gesamt** | | **~1.230** | **~73** | **~1.303** |

### Dateien-Übersicht

| Datei | Typ | Phase | LOC |
|-------|-----|-------|-----|
| `kb/llm/engine/base.py` | Geändert | 1 | ~3 |
| `kb/llm/config.py` | Geändert | 1 | ~50 |
| `kb/llm/engine/transformers_engine.py` | **Neu** | 1-4 | ~750 |
| `kb/llm/engine/__init__.py` | Geändert | 1 | ~5 |
| `kb/llm/engine/factory.py` | **Neu** | 1 | ~30 |
| `kb/llm/engine/test_transformers_engine.py` | **Neu** | 5 | ~250 |
| `kb/llm/engine/TRANSFORMERS_ENGINE.md` | **Neu** | 5 | ~200 |
| `README.md` | Geändert | 5 | ~15 |

### Abhängigkeits-Graph (neue Dateien)

```
kb/llm/config.py  ──────────┐
                             │
kb/llm/engine/base.py  ──────┤
                             ▼
kb/llm/engine/transformers_engine.py  ←─── torch, transformers
                             │              (bitsandbytes, accelerate optional)
kb/llm/engine/factory.py ───┘
```

---

## Requirements (neue Python-Packages)

### Pflicht

| Package | Version | Zweck |
|---------|---------|-------|
| `torch` | >= 2.1 | PyTorch (CPU oder CUDA) |
| `transformers` | >= 4.36 | HuggingFace Transformers |

### Optional

| Package | Version | Zweck | Wann nötig |
|---------|---------|-------|------------|
| `bitsandbytes` | >= 0.41 | 4-bit/8-bit Quantization | Nur bei `hf_quantization` |
| `accelerate` | >= 0.25 | Multi-GPU, device_map="auto" | Nur bei Multi-GPU |
| `sentencepiece` | >= 0.1 | Tokenizer für einige Modelle | Modell-abhängig |
| `protobuf` | >= 3.20 | Tokenizer-Backend | Modell-abhängig |

### requirements-llm-hf.txt (neu)

```
# KB Framework - HuggingFace LLM Engine Dependencies
# Install: pip install -r requirements-llm-hf.txt

# Core (required)
torch>=2.1
transformers>=4.36

# Quantization (optional - Linux/CUDA only)
# bitsandbytes>=0.41

# Multi-GPU (optional)
# accelerate>=0.25

# Tokenizer backends (model-dependent)
# sentencepiece>=0.1
# protobuf>=3.20
```

---

## Vergleich: OllamaEngine vs TransformersEngine

| Aspekt | OllamaEngine | TransformersEngine |
|--------|-------------|-------------------|
| **Architektur** | Client → HTTP → Ollama Server | In-Process (direkt im Python-Prozess) |
| **Server nötig** | Ja (Ollama Daemon) | Nein |
| **Erster Start** | Sofort (Server läuft) | Langsam (Model-Download + Load) |
| **Folgende Starts** | Sofort | Langsam (Reload aus Cache) |
| **Memory** | Getrennter Prozess | Gleicher Prozess (~2-8 GB) |
| **Multi-Model** | Einfach (ollama pull) | Schwer (Speicher-Management) |
| **Quantization** | Ollama-intern | bitsandbytes (4-bit/8-bit) |
| **Streaming** | HTTP-Stream | TextIteratorStreamer |
| **Multi-GPU** | Ollama-intern | accelerate device_map |
| **Model-Auswahl** | Ollama-Registry | Alle HF Hub-Modelle |
| **Offline** | Nur vorgeladene Modelle | Cache + Offline-Modus |
| **Deployment** | Einfach (1 Prozess) | Komplexer (Dependencies) |

### Wann TransformersEngine wählen?

- **Kein Ollama** verfügbar (VPS, CI/CD, RESTRICTED-Umgebung)
- **Spezifische HF-Modelle** nötig, die Ollama nicht hat
- **Feinkontrolle** über Quantization, Device, dtype
- **Chat-Templates** direkt via Tokenizer

### Wann OllamaEngine wählen?

- **Einfaches Setup** (1 Binary, Docker-ready)
- **Multi-Model** gleichzeitig
- **Isolierte Prozesse** (Memory-Sicherheit)
- **Schnelles Wechseln** zwischen Modellen

---

## Risiken und Fallback-Strategien

### Risiko 1: Memory-Overflow (OOM)

**Wahrscheinlichkeit:** Hoch bei Consumer-Hardware
**Impact:** Crash des gesamten Prozesses

**Fallback-Strategien:**
1. **4-bit Quantization als Default** — reduziert VRAM von ~16 GB auf ~4 GB
2. **CPU-Offload** — `device_map="auto"` lagert Layer auf CPU aus
3. **`unload_model()` API** — explizites Freigeben bei Nicht-Verwendung
4. **Memory-Monitoring** — `get_gpu_stats()` für Pre-Flight-Check
5. **Graceful Degradation** — bei OOM: Warnung + Fallback auf CPU

```python
try:
    self._load_model()
except torch.cuda.OutOfMemoryError:
    logger.warning("GPU OOM, falling back to CPU")
    self._config.hf_device = "cpu"
    self._config.hf_quantization = None
    self._load_model()
```

### Risiko 2: Ladezeit bei erstem Start

**Wahrscheinlichkeit:** Garantiert bei neuem Modell
**Impact:** Schlechte UX ("hängt")

**Fallback-Strategien:**
1. **Progress-Logging** — Download-Fortschritt sichtbar machen
2. **Pre-Download-CLI** — `kb llm hf-pull google/gemma-2-2b-it`
3. **Cache-Warming** — Model bei Setup/Init herunterladen
4. **Timeout + Abbruch** — Lade-Timeout mit klarer Fehlermeldung

### Risiko 3: Dependency-Hölle (torch + CUDA Versionen)

**Wahrscheinlichkeit:** Mittel
**Impact:** Installation schlägt fehl

**Fallback-Strategien:**
1. **CPU-only torch als Fallback** — `pip install torch --index-url CPU`
2. **Optionale Imports** — Alle torch/transformers Imports in try/except
3. **Klare Fehlermeldungen** — "Install torch-cuda for GPU support"
4. **requirements-llm-hf.txt** — Getrennte Requirements, nicht im Haupt-requirements.txt

### Risiko 4: Thread-Safety bei Concurrent Access

**Wahrscheinlichkeit:** Mittel
**Impact:** Falsche Ergebnisse oder Crash

**Fallback-Strategien:**
1. **ThreadPoolExecutor(max_workers=1)** — Serialisiert Inference
2. **Model-Lock** — `threading.Lock` für Model-Zugriff
3. **Request-Queue** — Bei Concurrent-Zugriff: Queue statt Parallelität
4. **Dokumentation** — Klar kommunizieren: 1 Request gleichzeitig

### Risiko 5: Modell-Inkompatibilität

**Wahrscheinlichkeit:** Mittel (nicht alle HF-Modelle sind Causal LM)
**Impact:** Load-Fehler

**Fallback-Strategien:**
1. **Model-Typ-Check** — Vorab prüfen ob `AutoModelForCausalLM` unterstützt
2. **Whitelist** — Bekannte funktionierende Modelle dokumentieren
3. **Klare Fehlermeldung** — "Model X ist kein Causal LM, versuche Seq2Seq"
4. **AutoModel-Dispatch** — Je nach Modell-Typ richtige Auto-Klasse wählen

---

## Implementierungs-Reihenfolge (Konkret)

```
Woche 1: Phase 1 + Phase 2
├── Tag 1-2: base.py (LLMProvider), config.py (hf_ Felder), factory.py
├── Tag 3-4: transformers_engine.py Skeleton + Model-Loading
└── Tag 5: Quantization, Device-Detection, Memory-Management

Woche 2: Phase 3 + Phase 4
├── Tag 1-2: generate(), generate_async()
├── Day 3: generate_stream(), generate_stream_async()
└── Tag 4-5: Batch, Multi-GPU, Chat-Template, GPU-Stats

Woche 3: Phase 5
├── Tag 1-2: Unit Tests (Mock)
├── Tag 3: Integration Tests (mit tiny-gpt2)
├── Tag 4: Dokumentation (TRANSFORMERS_ENGINE.md)
└── Tag 5: README-Update, Final Review
```

---

## Offene Fragen (vor Implementierung klären)

1. **Singleton-Pattern?** `OllamaEngine` ist Singleton. `TransformersEngine` auch?
   → Empfehlung: **Nein.** Mehrere Instanzen können verschiedene Modelle halten.
   → Aber: **Context-Manager** für Memory-Safety (`with TransformersEngine() as engine:`)

2. **Model-Preloading?** Soll das Modell bei `__init__` oder beim ersten `generate()` geladen werden?
   → Empfehlung: **Lazy Loading** (bei erstem generate), explizites `load_model()` für Preloading.

3. **`requirements.txt` Integration?** HF-Dependencies im Haupt-File oder separat?
   → Empfehlung: **Separat** (`requirements-llm-hf.txt`), nicht jeder braucht torch.

4. **Chat-Format?** Wie wird `messages=[{role, content}]` übergeben?
   → Empfehlung: **Neue Methode** `chat(messages)` → intern `apply_chat_template` + `generate`.

5. **Retry-Logic?** OllamaEngine hat Retry. TransformersEngine auch?
   → Empfehlung: **Nein.** Bei OOM/Crash ist Retry sinnlos. Besser: Error mit Klartext.

---

*Ende PLAN_HUGGINGFACE.md v1.0*