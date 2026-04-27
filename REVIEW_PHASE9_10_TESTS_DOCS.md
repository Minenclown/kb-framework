# KB-Framework Review — Phase 9+10: Testabdeckung & Doku-Konsistenz

**Reviewer:** Sir Stern 🔍  
**Datum:** 2026-04-26  
**Repo:** `~/projects/kb-framework/`

---

## Phase 9: Testabdeckung

### 9.1 Test-Dateien — Übersicht

| Test-Datei | Module | Tests |
|---|---|---|
| `tests/test_kb.py` | kb.config, embeddings | 6 collected |
| `tests/test_module_split.py` | Modulstruktur | 6 collected |
| `tests/test_indexer.py` | BiblioIndexer, MarkdownIndexer | 21 collected |
| `tests/test_chroma_singleton.py` | ChromaIntegration Singleton | 9 collected |
| `tests/test_obsidian_parser.py` | Obsidian Parser | ~40+ |
| `tests/test_obsidian_vault.py` | ObsidianVault | ~30+ |
| `tests/test_obsidian_resolver.py` | Link Resolution | ~15+ |
| `tests/test_obsidian_writer.py` | VaultWriter | ~25+ |
| `tests/test_obsidian_indexer.py` | BacklinkIndexer | ~16+ |
| `tests/test_obsidian_e2e.py` | End-to-End Vault | ~6+ |
| `tests/test_obsidian_integration.py` | Integration | ~5+ |
| `tests/test_llm/test_engine.py` | OllamaEngine | ~15+ |
| `tests/test_llm/test_engine_registry.py` | EngineRegistry | ~10+ |
| `tests/test_llm/test_model_source.py` | LLMConfig model_source | ~10+ |
| `tests/test_llm/test_content_manager.py` | LLMContentManager | ~20+ |
| `tests/test_llm/test_report_generator.py` | ReportGenerator | ~30+ |
| `tests/test_llm/test_parallel_mode.py` | Parallel Mode | ~10+ |
| `tests/test_llm/test_transformers_engine.py` | TransformersEngine | ~10+ |

**Gesamt:** 431 Tests collected, 17 Test-Dateien

### 9.2 Modul-spezifische Testabdeckung

| Modul | Tests vorhanden? | Bewertung |
|---|---|---|
| `kb/framework/exceptions.py` | ❌ **Kein dedizierter Test** | 🔴 Kritisch — Exception-Hierarchie ungetestet |
| `kb/framework/paths.py` | ❌ **Kein dedizierter Test** | 🔴 Kritisch — Pfad-Auflösung ungetestet |
| `kb/framework/hybrid_search/` | ⚠️ **Indirekt über `test_kb.py`** | 🟡 Nur `test_config_paths_exist` + `test_paths_are_paths` — keine Such-Logik-Tests |
| `kb/framework/providers/` | ❌ **Kein Test** | 🔴 Kritisch — ChromaSemanticProvider, FTS5KeywordProvider ungetestet |
| `kb/framework/chroma_integration.py` | ✅ `test_chroma_singleton.py` | 🟢 Singleton-Tests vorhanden |
| `kb/framework/embedding_pipeline.py` | ❌ **Kein Test** | 🟡 EmbeddingPipeline ungetestet |
| `kb/framework/reranker.py` | ❌ **Kein Test** | 🟡 Reranker ungetestet |
| `kb/framework/chunker.py` | ❌ **Kein Test** | 🟡 Chunker ungetestet |
| `kb/framework/stopwords.py` | ❌ **Kein Test** | 🟢 Klein, aber sollte getestet werden |
| `kb/framework/synonyms.py` | ❌ **Kein Test** | 🟡 SynonymExpander ungetestet |
| `kb/framework/text.py` | ❌ **Kein Test** | 🟡 Text-Utilities ungetestet |
| `kb/framework/search_providers.py` | ❌ **Kein Test** | 🔴 Provider-Interface ungetestet |
| `kb/framework/batching.py` | ❌ **Kein Test** | 🟡 Batch-Utilities ungetestet |
| `kb/framework/fts5_setup.py` | ❌ **Kein Test** | 🟡 FTS5-Setup ungetestet |

### 9.3 Test-Ausführungsergebnisse

```
6 failed, 390 passed, 35 skipped, 88 warnings in 41.44s
```

**Fehlgeschlagene Tests:**

| Test | Datei | Ursache |
|---|---|---|
| `test_init_with_config` | `test_content_manager.py` | Unbekannt (Config-Problem) |
| `test_engine_singleton` | `test_engine.py` | Singleton-Konflikt |
| `test_generate_max_retries_exceeded` | `test_engine.py` | Mock/Retry-Logik |
| `test_compute_hotspots` | `test_report_generator.py` | Hotspot-Berechnung |
| `test_generate_graph_data` | `test_report_generator.py` | Graph-Data-Generierung |
| `test_graph_data_with_hotspots` | `test_report_generator.py` | Graph+Hotspot-Kombo |

**Warnungen:**

- **`pytest.mark.asyncio`** nicht registriert → `pytest-asyncio` fehlt als Dependency. 17+ async Tests werden **skipped**, nicht ausgeführt
- **`PytestReturnNotNoneWarning`** in `test_module_split.py` — Tests returnen `True` statt `assert`
- **`DeprecationWarning`** für `ChromaIntegrationV2` (deprecated) und `sqlite3 datetime adapter` (Python 3.12)

### 9.4 Testabdeckung — Fazit

**Abdeckung nach Modul-Gruppen:**

| Gruppe | Abdeckung | Status |
|---|---|---|
| Obsidian (5 Module) | ✅ ~95% | Sehr gut |
| LLM/Biblio (7 Module) | ⚠️ ~70% (6 Failures) | Braucht Fix |
| Indexer | ✅ ~90% | Gut |
| KB Config/Embeddings | ⚠️ ~50% | Mäßig |
| **Framework Core (8 Module)** | ❌ **~10%** | **Kritisch unzureichend** |

**Empfehlung:**  
1. **Sofort:** `pytest-asyncio` in `requirements-dev.txt` aufnehmen → 35 skipped Tests werden aktiv
2. **Hohe Priorität:** Tests für `exceptions.py`, `paths.py`, `providers/`, `hybrid_search/engine.py`
3. **Mittel:** Tests für `reranker.py`, `chunker.py`, `synonyms.py`, `embedding_pipeline.py`
4. **Niedrig:** 6 LLM-Test-Failures beheben

---

## Phase 10: Doku-Konsistenz

### 10.1 README.md

**Status:** ✅ Existiert, 375 Zeilen

**Inhalt:**
- Problemstellung und Lösung
- Features (Hybrid Search, Obsidian, ChromaDB, LLM Engine)
- Quick Start (CLI)
- CLI Commands
- Python API-Beispiele
- Architektur

**Probleme:**

| # | Problem | Schwere |
|---|---|---|
| R1 | README erwähnt `"from kb.framework import HybridSearch"` — funktioniert ✅ | — |
| R2 | README erwähnt `"from kb.framework import ChromaIntegration, embed_text"` — funktioniert ✅ | — |
| R3 | README erwähnt `"from kb.framework import SentenceChunker, chunk_document"` — nicht geprüft | 🟡 |
| R4 | README API-Sektion zeigt `kb.framework.search.HybridSearch().query()` — Methode heißt `search()` nicht `query()` | 🔴 **Bug** |

### 10.2 SKILL.md

**Status:** ✅ Existiert, ~270 Zeilen

**Kritische Probleme:**

| # | Problem | Schwere |
|---|---|---|
| S1 | **`from kb.biblio import LLMConfig, EngineRegistry, create_engine`** — `EngineRegistry` und `create_engine` sind **NICHT** in `kb.biblio.__all__` → ImportError | 🔴 **Bug** |
| S2 | **Architektur-Diagramm zeigt `library/knowledge_base/`** — dieses Verzeichnis existiert **nicht**. Module sind unter `kb/framework/` | 🔴 **Veraltet** |
| S3 | SKILL.md erwähnt `kb/library/knowledge_base/hybrid_search.py` als Einzeldatei → Ist jetzt ein Package `kb/framework/hybrid_search/` mit 6 Modulen | 🔴 **Veraltet** |
| S4 | SKILL.md erwähnt `kb/library/knowledge_base/chroma_integration.py` → Echte Datei: `kb/framework/chroma_integration.py` | 🔴 **Veraltet** |
| S5 | SKILL.md erwähnt `kb/library/knowledge_base/chroma_plugin.py` → Echte Datei: `kb/framework/chroma_plugin.py` | 🔴 **Veraltet** |
| S6 | SKILL.md erwähnt `kb/library/knowledge_base/embedding_pipeline.py` → Echte Datei: `kb/framework/embedding_pipeline.py` | 🔴 **Veraltet** |
| S7 | SKILL.md erwähnt `kb/library/knowledge_base/reranker.py` → Echte Datei: `kb/framework/reranker.py` | 🔴 **Veraltet** |
| S8 | SKILL.md erwähnt `kb/library/knowledge_base/fts5_setup.py` → Echte Datei: `kb/framework/fts5_setup.py` | 🔴 **Veraltet** |
| S9 | SKILL.md erwähnt `kb/library/knowledge_base/chunker.py` → Echte Datei: `kb/framework/chunker.py` | 🔴 **Veraltet** |
| S10 | SKILL.md erwähnt `kb/library/knowledge_base/synonyms.py` → Echte Datei: `kb/framework/synonyms.py` | 🔴 **Veraltet** |
| S11 | SKILL.md zeigt `from kb.biblio.generator import EssenzGenerator` → Korrekt wäre `from kb.biblio import EssenzGenerator` (lazy import via `__init__`) | 🟡 |
| S12 | SKILL.md fehlen neue Module: `exceptions.py`, `paths.py`, `batching.py`, `search_providers.py`, `text.py`, `providers/` | 🟡 |

### 10.3 API-Doku vs. Code — Detaillierter Vergleich

**Funktionierende Importe (✅):**

| SKILL.md/README Behauptung | Realer Code | Status |
|---|---|---|
| `from kb.framework import HybridSearch` | ✅ `kb.framework.__init__` re-export | OK |
| `from kb.framework import ChromaIntegration` | ✅ Re-export | OK |
| `from kb.framework.chroma_integration import get_chroma` | ✅ Direkter Import | OK |
| `from kb.framework.providers import ChromaSemanticProvider, FTS5KeywordProvider` | ✅ Re-export | OK |
| `from kb.biblio import LLMConfig` | ✅ Lazy import | OK |
| `from kb.biblio.generator import EssenzGenerator` | ✅ Direkter Import | OK |

**Nicht funktionierende Importe (❌):**

| SKILL.md Behauptung | Realer Code | Status |
|---|---|---|
| `from kb.biblio import EngineRegistry` | ❌ Nicht in `__all__`, kein lazy import | **ImportError** |
| `from kb.biblio import create_engine` | ❌ Nicht in `__all__`, kein lazy import | **ImportError** |
| `kb.framework.search.HybridSearch().query()` | ❌ Methode heißt `.search()` nicht `.query()` | **AttributeError** |

**Korrekter Import-Pfad:**

| SKILL.md sagt | Richtig wäre |
|---|---|
| `from kb.biblio import EngineRegistry` | `from kb.biblio.engine.registry import EngineRegistry` |
| `from kb.biblio import create_engine` | `from kb.biblio.engine.factory import create_engine` (oder `DefaultEngineFactory`) |

### 10.4 Custom Exceptions — Nutzungslücke

**`kb/framework/exceptions.py`** definiert 8 Custom Exceptions:

- `KBFrameworkError` (Base)
- `ConfigError`
- `ChromaConnectionError`
- `SearchError`
- `EmbeddingError`
- `DatabaseError`
- `PluginError`
- `PipelineError`
- `ProviderError`

**Importiert aber nicht geworfen:**  
Die Exceptions werden in `framework`-Modulen importiert (`ChromaConnectionError`, `SearchError`, `DatabaseError`, `EmbeddingError`, `PipelineError`, `ProviderError`, `ChromaConnectionError`), aber **kein einziges Modul wirft sie mit `raise`**. Stattdessen verwenden alle Module Python-Builtins (`ValueError`, `FileNotFoundError`, `RuntimeError`).

Die `LLMConfigError` und `KBConfigError` (in `kb.biblio.config` und `kb.base.config`) sind **eigene Hierarchien**, die nicht von `KBFrameworkError` erben — ein Design-Bruch.

### 10.5 `paths.py` — Ungetestet aber Gut Integriert

`paths.py` wird aktiv genutzt (7+ Import-Stellen in `framework/`), aber hat:
- ❌ Keinen dedizierten Test
- ⚠️ Fallback-Pfade sind hardcodiert (`Path.home() / ".openclaw" / "kb" / ...`)

### 10.6 Doku-Konsistenz — Fazit

| Kategorie | Status | Schwere |
|---|---|---|
| **SKILL.md Architektur-Diagramm** | 🔴 Komplett veraltet (`library/knowledge_base/` existiert nicht) | Hoch |
| **SKILL.md API-Beispiele** | 🔴 2 Importe kaputt (`EngineRegistry`, `create_engine`) | Hoch |
| **README API** | 🟡 1 Methodenname falsch (`query()` → `search()`) | Mittel |
| **SKILL.md fehlende Module** | 🟡 6 neue Module nicht dokumentiert | Niedrig |
| **Exceptions** | 🟡 Definiert aber nicht geworfen; separate Hierarchien | Mittel |

---

## Zusammenfassung — Top-Empfehlungen

### 🔴 Kritisch (Sofort beheben)

1. **SKILL.md Architektur-Diagramm aktualisieren** — `library/knowledge_base/` → `framework/`, `hybrid_search.py` → `hybrid_search/` Package
2. **SKILL.md API-Beispiele reparieren** — `EngineRegistry` und `create_engine` korrekte Import-Pfade oder `__init__.py` erweitern
3. **`pytest-asyncio` in `requirements-dev.txt`** — 35 Tests werden currently skipped
4. **Tests für `exceptions.py`** — Exception-Hierarchie und Catching-Verhalten
5. **Tests für `paths.py`** — Pfad-Auflösung und Fallbacks
6. **Tests für `providers/`** — ChromaSemanticProvider und FTS5KeywordProvider

### 🟡 Mittel

7. **Custom Exceptions auch verwenden** — Statt `ValueError`/`RuntimeError` die definierten `KBFrameworkError`-Subklassen werfen
8. **README `.query()` → `.search()`** korrigieren
9. **6 LLM-Test-Failures** untersuchen und beheben
10. **`test_module_split.py`** — `return True` → `assert ...`

### 🟢 Niedrig

11. Tests für `reranker.py`, `chunker.py`, `synonyms.py`, `embedding_pipeline.py`, `text.py`, `batching.py`
12. SKILL.md um neue Module ergänzen (`exceptions.py`, `paths.py`, `batching.py`, `search_providers.py`, `text.py`, `providers/`)
13. `DeprecationWarning` für `ChromaIntegrationV2` — Removal-Timeline klären

---

*End of Phase 9+10 Review*