# CONFIG_SWITCH_PLAN.md — LLM Model Source Switch

**Erstellt:** 2026-04-16
**Status:** Planung abgeschlossen
**Version:** 1.0

---

## 1. Aktuelle Analyse (Ist-Zustand)

### 1.1 Config-Struktur (`kb/biblio/config.py`)

`LLMConfig` ist ein Singleton mit folgender Architektur:

- **`model_source`** (string, Default: `"ollama"`):
  - Unterstützt Werte: `"ollama"` | `"huggingface"`
  - Validierung in `_validate_hf_config()`: schlägt bei unbekannten Werten fehl
  - `DEFAULT_MODEL_SOURCE = "ollama"`

- **`model`** (string): Ollama-Modellname (z.B. `"gemma4:e2b"`)

- **`ollama_url`** (string): Ollama-Server-URL

- **HuggingFace-Parameter:**
  - `hf_model_name`, `hf_device`, `hf_quantization`, `hf_dtype`, `hf_cache_dir`, `hf_token`, `hf_revision`, `hf_trust_remote_code`, `hf_torch_dtype`, `hf_offload_folder`

### 1.2 Engine-Factory Pattern (`kb/biblio/engine/factory.py`)

```python
def create_engine(config: Optional[LLMConfig] = None) -> BaseLLMEngine:
    if config is None:
        config = get_llm_config()
    
    if config.model_source == "ollama":
        return OllamaEngine.get_instance(config)
    elif config.model_source == "huggingface":
        return TransformersEngine.get_instance(config)
    else:
        raise LLMConfigError(f"Unknown model_source: ...")
```

**Entscheidungslogik:** Ein einfaches `if/elif/else` in `create_engine()` dispatcht basierend auf `model_source`. Das ist die **einzige** Stelle, an der entschieden wird, welcher Engine läuft.

### 1.3 Aktuelle Nutzung

- **`kb llm status`** (llm.py:259): Erstellt **ausschließlich** `OllamaEngine.get_instance()` — kein `create_engine()`, kein `model_source`-Check
- **Generatoren** (essenc\_, report\_generator): Nutzen `create_engine()` über `get_llm_config()` → korrektes Dispatching
- **FileWatcher, TaskScheduler**: Nutzen ebenfalls `create_engine()`

### 1.4 Problem

1. **`kb llm status` ignoriert `model_source`** — zeigt immer Ollama-Status, auch wenn HF konfiguriert ist
2. **Kein paralleler Modus** — `model_source` ist ein einzelner String, kein paralleler Betrieb beider Engines
3. **Kein expliziter Switch-Befehl** — kein CLI-Kommando um zwischen Quellen zu wechseln
4. **Kein Auto-Modus** — kein Fallback von HF → Ollama wenn HF nicht verfügbar (oder umgekehrt)

---

## 2. Ziel-Architektur (Soll-Zustand)

### 2.1 Neue Config-Optionen

```python
# Haupt-Modus
model_source: "huggingface" | "ollama" | "auto"
# "auto" = versuche HF zuerst, fallback auf Ollama

# Explizite Modellnamen pro Quelle
ollama_model: str          # überschreibt .model wenn source=ollama/auto
ollama_url: str            # bleibt wie bisher
hf_model_name: str        # bereits vorhanden

# Parallel-Modus
parallel_mode: bool = False  # beide Engines parallel
parallel_strategy: "primary_first" | "aggregate" | "compare"
# primary_first: primärer Engine zuerst, sekundär nur bei Fehler
# aggregate: beide, kombiniere Ergebnisse
# compare: beide, zeige Vergleich

# Ollama-spezifisch
ollama_timeout: int        # separat von HF
ollama_temperature: float  # separat von HF
```

### 2.2 Engine Registry (neue Abstraktion)

 statt einem einzelnen `create_engine()`:

```python
class EngineRegistry:
    """Zentrales Register für alle LLM Engines."""
    
    def get_engine(self, source: str) -> BaseLLMEngine: ...
    def get_primary(self) -> BaseLLMEngine: ...   # basierend auf model_source
    def get_secondary(self) -> BaseLLMEngine: ...  # die andere Engine
    def get_both(self) -> tuple[BaseLLMEngine, BaseLLMEngine]: ...  # für parallel
```

### 2.3 CLI-Erweiterung

```
kb llm config set model_source <ollama|huggingface|auto>
kb llm config set parallel_mode <true|false>

kb llm engine status       # zeigt Status beider Engines
kb llm engine switch <ollama|huggingface|auto>
kb llm engine test         # testet beide Engines
```

### 2.4 Generator-Änderungen

Generatoren bekommen `parallel_mode` Unterstützung:
- `parallel_strategy="primary_first"`: Primärer Engine läuft, bei Fehler sekundärer
- `parallel_strategy="aggregate"`: Beide generieren, Ergebnisse werden kombiniert
- `parallel_strategy="compare"`: Beide generieren, Ergebnisse verglichen (nur für Essenzen sinnvoll)

---

## 3. Migrations-Plan

### Phase 1: Config-Erweiterung

**Dateien:** `kb/biblio/config.py`

1. Neues Feld `model_source` erweitern (bereits vorhanden)
2. `"auto"` als neuen gültigen Wert hinzufügen
3. Neue Felder: `parallel_mode`, `parallel_strategy`
4. Ollama-spezifische Overrides: `ollama_timeout`, `ollama_temperature`, `ollama_model`
5. Validierung für neue Felder

**Breaking Changes:** Keine — bestehende Config bleibt funktional

### Phase 2: EngineRegistry

**Neue Datei:** `kb/biblio/engine/registry.py`

1. `EngineRegistry` Klasse erstellen
2. Singleton-Pattern wie andere Engines
3. `get_engine(source)`, `get_primary()`, `get_secondary()`, `get_both()`
4. `is_engine_available(source)` für Health-Checks
5. `list_engines()` für CLI-Status

**geändert:** `kb/biblio/engine/factory.py` → delegiert an Registry

### Phase 3: CLI-Erweiterung

**Datei:** `kb/commands/llm.py`

1. Neuer Subparser: `kb llm engine <action>`
   - `engine status` — zeigt beide Engines (vorhandene `status`-Logik erweitern)
   - `engine switch <source>` — ändert model_source + updated Engine Registry
   - `engine test` — testet beide Engines mit kurzer Prompt
2. `kb llm config set` erweitern um:
   - `parallel_mode`
   - `parallel_strategy`
   - `ollama_model`, `ollama_timeout`, `ollama_temperature`

### Phase 4: Parallel Generator Support

**Dateien:** `kb/biblio/generator/*.py`

1. Generator-Basisklasse bekommt `parallel_mode` Parameter
2. `EssenzGenerator` implementiert `aggregate` und `compare` Strategien
3. `ReportGenerator` unterstützt `primary_first`

### Phase 5: kb llm status Erweiterung

**Datei:** `kb/commands/llm.py`

`_cmd_status()` erweitern:
- Zeigt aktiven `model_source`
- Zeigt Status beider Engines (nicht nur Ollama)
- Zeigt ob `parallel_mode` aktiv

---

## 4. Cody-Phasen (Implementation)

### Cody Phase 1: Config & Registry
```
kb/biblio/config.py:
- "auto" als model_source zulassen
- parallel_mode, parallel_strategy Fields
- ollama_model, ollama_timeout, ollama_temperature

kb/biblio/engine/registry.py (NEU):
- EngineRegistry mit Singleton
- get_engine(source), get_primary(), get_secondary()
- Health-Checks pro Engine

kb/biblio/engine/factory.py:
- Delegation an Registry
```

### Cody Phase 2: CLI
```
kb/commands/llm.py:
- Neuer Subparser "engine"
- kb llm engine status|switch|test
- config set Erweiterungen
- _cmd_status erweitern für beide Engines
```

### Cody Phase 3: Generator Parallel Support
```
kb/biblio/generator/:
- parallel_mode in Generator-Interface
- EssenzGenerator: aggregate + compare
- ReportGenerator: primary_first
```

### Cody Phase 4: Testing & Documentation
```
kb/tests/:
- Test für EngineRegistry
- Test für model_source switching
- Test für parallel_mode

Dokumentation:
- README Updates
- Config-Beispiele
```

---

## 5. Risiken & Offene Fragen

### Offene Fragen

1. **"auto" Logik:** Soll `auto` bei HF-Initialisierung scheitern automatisch auf Ollama fallen, oder nur einmal beim Start?
   → **Empfehlung:** Einmalig beim Start; Runtime-Fallback nur bei expliziter Anforderung

2. **Token-Limit bei Parallel:** Zwei Engines benutzen = doppelte Token. Wer limitiert?
   → **Empfehlung:** Primärer Engine bestimmt Token-Budget

3. **compare Mode Output:** Wie formatiert man den Vergleich?
   → **Empfehlung:** Side-by-side für Essenzen

4. **Ollama Model Override:** Soll `ollama_model` explizit sein oder nur ein Override von `model`?
   → **Empfehlung:** Explizites Feld `ollama_model`, `model` bleibt Default für beide

### Risiken

1. **Singleton-Problem:** Beide Engines sind Singletons — parallel Mode könnte Konflikte haben
   → **Lösung:** EngineRegistry tracked aktive Instanzen, kein Konflikt da verschiedene Klassen
2. **Memory:** HF + Ollama parallel = mehr RAM. Ollama läuft im eigenen Prozess, kein Problem.
3. **Config-Reload:** Bei `model_source` Wechsel müssen aktive Engine-Instanzen zurückgesetzt werden
   → **Lösung:** `EngineRegistry.reset()` bei model_source-Wechsel

---

## 6. Datei-Änderungen Übersicht

| Datei | Aktion | Änderung |
|-------|--------|----------|
| `kb/biblio/config.py` | ÄNDERN | +auto, parallel_mode, parallel_strategy, ollama_* |
| `kb/biblio/engine/registry.py` | NEU | EngineRegistry Klasse |
| `kb/biblio/engine/factory.py` | ÄNDERN | Delegation an Registry |
| `kb/commands/llm.py` | ÄNDERN | +engine subparser, +config keys |
| `kb/biblio/generator/essence_generator.py` | ÄNDERN | parallel strategies |
| `kb/biblio/generator/report_generator.py` | ÄNDERN | parallel strategies |
| `kb/biblio/engine/__init__.py` | ÄNDERN | +EngineRegistry export |

---

## 7. Nächste Schritte

1. **Cody Phase 1 implementieren** (Config + Registry)
2. **Testen** dass bestehende Funktionalität nicht bricht
3. **Cody Phase 2** (CLI)
4. **Cody Phase 3** (Parallel)
5. **Dokumentation** vervollständigen
