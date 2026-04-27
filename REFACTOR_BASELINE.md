# REFACTOR BASELINE — 2026-04-26 12:58 UTC

## Test Results

```
7 failed, 388 passed, 35 skipped, 1 deselected, 85 warnings
Runtime: 45.10s
```

### Pre-existing Failures (NOT caused by refactor)

1. `tests/test_kb.py::TestConfig::test_registry_exists` — ImportError: `__registry__` missing from config
2. `tests/test_llm/test_content_manager.py::TestContentManagerInit::test_init_with_config` — Path mismatch (hardcoded vs temp dir)
3. `tests/test_llm/test_engine.py::TestOllamaEngine::test_engine_singleton` — Singleton not working
4. `tests/test_llm/test_engine.py::TestOllamaEngineGenerate::test_generate_max_retries_exceeded` — NameError: `llm_config` not defined
5. `tests/test_llm/test_report_generator.py::TestHotspotDetection::test_compute_hotspots` — Assert fail
6. `tests/test_llm/test_report_generator.py::TestGraphDataGeneration::test_generate_graph_data` — Assert fail
7. `tests/test_llm/test_report_generator.py::TestGraphDataGeneration::test_graph_data_with_hotspots` — Assert fail

All 7 failures are in test_llm/ or test_kb config — unrelated to the knowledge_base/framework refactor.

### Post-refactor success criteria:
- Same 7 failures acceptable (pre-existing)
- No NEW failures introduced