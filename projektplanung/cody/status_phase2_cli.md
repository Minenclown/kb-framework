# Cody Phase 2 Status: CLI Erweiterungen für LLM Model Source Switch

**Erstellt:** 2026-04-16
**Status:** ✅ Abgeschlossen

---

## Aufgaben & Ergebnisse

### 1. `kb llm engine <action>` — Neuer Subparser ✅

**Datei:** `kb/commands/llm.py`

Neue Subcommands implementiert:

| Befehl | Beschreibung | Status |
|--------|-------------|--------|
| `kb llm engine status` | Zeigt beide Engines, aktive model_source, parallel_mode | ✅ |
| `kb llm engine switch <source>` | Ändert model_source + reset Registry | ✅ |
| `kb llm engine test` | Testet beide Engines mit kurzem Prompt | ✅ |

**Implementierung:**
- Neuer Subparser `engine` mit 3 Sub-Subparsers: `status`, `switch`, `test`
- Dispatch-Tabelle in `_cmd_engine()` mit eigener Error-Handling
- `_engine_status()`: Nutzt `EngineRegistry.status()` für beide Engines, Fallback auf Einzel-Checks
- `_engine_switch()`: Reset EngineRegistry → LLMConfig.reload → Validierung, inkl. Rollback bei Fehler
- `_engine_test()`: Testet Primary + Secondary Engine, zeigt Antwort-Preview und Timing

### 2. `kb llm config set` Erweiterung ✅

Neue mutable Config-Keys:

| Key | Type | Env Variable |
|-----|------|-------------|
| `model_source` | str | KB_LLM_MODEL_SOURCE |
| `parallel_mode` | bool | KB_LLM_PARALLEL_MODE |
| `parallel_strategy` | str | KB_LLM_PARALLEL_STRATEGY |
| `ollama_model` | str | KB_LLM_OLLAMA_MODEL |
| `ollama_timeout` | int | KB_LLM_OLLAMA_TIMEOUT |
| `ollama_temperature` | float | KB_LLM_OLLAMA_TEMPERATURE |

**Bool-Parsing:** Akzeptiert `true/false/1/0/yes/no`

**Sonderlogik:** Wenn `model_source` geändert wird, wird automatisch `EngineRegistry.reset()` aufgerufen.

### 3. `_cmd_status()` Erweiterung ✅

**Änderungen:**
- Zeigt aktive `model_source` und `parallel_mode`
- Zeigt Primary + Secondary Engine Status (via `EngineRegistry.status()`)
- Fallback auf Einzel-Engine-Check wenn Registry fehlschlägt
- Ollama-only Fallback wenn Registry komplett unavailable

---

## Tests

```
✅ Alle argparse-Tests bestanden
✅ kb llm engine --help funktioniert
✅ kb llm engine status --help funktioniert
✅ kb llm engine switch --help funktioniert (choices: ollama|huggingface|auto|compare)
✅ kb llm engine test --help funktioniert
✅ kb llm status zeigt model_source und parallel_mode
✅ config set mit bool/str/int/float Typen funktioniert
✅ model_source switch löst EngineRegistry.reset() aus
```

## Datei-Änderungen

| Datei | Änderung |
|-------|----------|
| `kb/commands/llm.py` | +_cmd_engine(), +_engine_status(), +_engine_switch(), +_engine_test(), erweitert _cmd_status(), erweitert _config_set(), erweitert _MUTABLE_CONFIG_KEYS, erweitert _CONFIG_KEY_TO_ENV, erweitert add_arguments() |

## Bekannte Einschränkungen

- `engine status` und `engine test` können hängen, wenn Ollama-Server nicht erreichbar (kein Timeout auf CLI-Ebene)
- HF-Engine laden dauert lange beim ersten Aufruf (erwartetes Verhalten)
- `engine switch` ist in-memory only – für Persistenz muss `KB_LLM_MODEL_SOURCE` Env-Var gesetzt werden