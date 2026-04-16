# Architektur-Analyse kb-framework

**Datum:** 2026-04-16  
**Analyst:** Sir Stern (Code Review Agent)  
**Fokus:** Strukturverbesserung, nicht Fehlerfindung

---

## Zusammenfassung

Das kb-framework ist ein komplexes System mit klaren Stärken (Plugin-Architektur, Lazy Loading, async-first Design) aber signifikanten Schwächen bei Modularisierung und Kopplung. Die Hauptprobleme sind:

1. **Überdimensionierte Module** (5 Module >500 Zeilen)
2. **Enge Kopplung** zwischen Suchlogik und DB-Schicht
3. **Redundanzen** bei Cache/Hashing
4. **Inkonsistente Muster** (Singletons vs Factories)

---

## 1. Modularisierung

### 1.1 Module über 500 Zeilen

| Datei | Zeilen | Hauptprobleme |
|-------|--------|---------------|
| `kb/biblio/generator/report_generator.py` | 1242 | Violation of Single Responsibility: Prompt Building + Report Generation + Data Collection + Retry Logic |
| `kb/biblio/scheduler/task_scheduler.py` | 1222 | Cron-Parsing + Job-Registry + Execution + DB-Logging vermischt |
| `kb/biblio/engine/transformers_engine.py` | 1162 | Akzeptabel als Engine-Wrapper, aber Broadcasting + Generation + Quantization in einer Klasse |
| `src/library/hybrid_search.py` | 997 | Search Logic + Scoring + Caching + FTS5-Fallback + Reranking in einer Klasse |
| `kb/biblio/generator/essence_generator.py` | 906 | Template Loading + Collection + Hotspot Scoring + Generation vermischt |

### 1.2 Zu viele Verantwortlichkeiten

**`report_generator.py`** - Mische responsibilities:
- `_collect_essences_for_period()` - Data Collection
- `_compute_hotspots()` - Analytics
- `_build_daily/weekly/monthly_prompt()` - Prompt Engineering (3 separate Methoden!)
- `_generate_graph_data()` - Graph-Generierung
- `generate_report()` - Orchestration
- `_save_graph_data()` - Persistence

**`task_scheduler.py`** - Mische responsibilities:
- Cron-Parsing (`_parse_cron()`)
- Job-Registry (`register_job()`, `_jobs` dict)
- Execution Loop (`start()`, `should_run()`)
- DB-Logging (`_log_execution()`, `_update_job_state()`)
- Retry-Logic (in `run_job()`)

**`hybrid_search.py`** - Mische responsibilities:
- Semantic Search (ChromaDB)
- Keyword Search (SQLite LIKE + FTS5)
- Score Merging + Normalization
- Query Cache (LRU, manuell implementiert)
- Synonym Expansion
- Re-Ranking Integration

### 1.3 Wo fehlt klare Separation of Concerns?

1. **Such-Layer Kopplung:** `HybridSearch` koppelt ChromaDB + SQLite + Scoring. Für Cluster-Analyse müsste entweder ChromaDB oder SQLite ersetzt werden → geht nicht ohne Rewrite.

2. **Config Singleton:** `KBConfig.get_instance()` und `LLMConfig.get_instance()` überall verwendet. Keine DI-Möglichkeit → Tests brauchen globale State.

3. **DB-Verwaltung:** `task_scheduler.py` hat eigene SQLite-Verbindung für Scheduler-State. `content_manager.py` nutzt `KBConnection` für DB-Tracking. Zwei verschiedene DB-APIs für verwandte Daten.

---

## 2. Template-Kompatibilität

### 2.1 Abschnitte die nicht ins 80%-Kontext-Template passen

**Problem: Enge Kopplung blockiert Cluster-Analyse**

```
HybridSearch → ChromaIntegration → ChromaDB (hardcoded)
                → SQLite FTS5 → knowledge.db (hardcoded)
                → SynonymExpander (lazy, aber singleton)
                → Reranker (lazy, aber singleton)
```

Für 80%-Kontext müsste das Semantic Loading via ChromaDB ersetzbar sein. Aktuell geht das nur durch Komplett-Rewrite von `HybridSearch._semantic_search()`.

**Kritische Kopplungspunkte:**

1. `hybrid_search.py` Zeile 18-24:
   ```python
   from .chroma_integration import ChromaIntegration, get_chroma
   from .fts5_setup import check_fts5_available
   from .synonyms import SynonymExpander, get_expander
   from .reranker import Reranker, get_reranker
   ```
   All diese Abhängigkeiten sind zur Kompilierzeit eingefroren.

2. `ChromaIntegration` ist fest mit ChromaDB verbunden. Für reinen SQLite-Betrieb (ohne Vector-Search) gibt es keinen abstrakten Layer.

3. Die Module-Redirects in `kb/knowledge_base/` sind ein Migration-Pattern, kein Design-Pattern. Können bei Neuentwicklung entfernt werden.

### 2.2 Refactor-Empfehlungen für Semantisches Loading

**Option A: Interface-Extraktion (empfohlen)**
```python
class SearchProvider(Protocol):
    async def search_semantic(query: str, limit: int) -> list[SearchResult]: ...
    async def search_keyword(query: str, limit: int) -> list[SearchResult]: ...

class ChromaSearchProvider(SearchProvider): ...
class SQLiteSearchProvider(SearchProvider): ...  # Für Cluster ohne ChromaDB
```

**Option B: Strategy-Pattern in HybridSearch**
```python
class HybridSearch:
    def __init__(self, semantic_provider: SearchProvider, keyword_provider: SearchProvider):
        self._semantic = semantic_provider
        self._keyword = keyword_provider
```

---

## 3. Effizienz-Optimierungen

### 3.1 Redundante Berechnungen

1. **File Hashing doppelt:**
   - `embedding_pipeline.py` hat `_get_default_chroma_path()` das `KBConfig.get_instance()` aufruft
   - `chroma_integration.py` hat die gleiche Funktion duplicated
   - `content_manager.py` hat `_compute_file_hash()` (SHA256)
   - `file_watcher.py` hat eigenes Hashing

2. **essences_path Iterierung:**
   ```python
   # report_generator.py _collect_essences_for_period()
   for essence in all_essences:  # Liest alle 1000
       # Dann für jede essence nochmal:
       json_path = self._config.essences_path / hash_val / "essence.json"
       data = json.loads(json_path.read_text())  # Nochmaliges Lesen!
   ```
   Besser: Batch-Load aller essence.json beim Start.

3. **hotspot-Berechnung in report_generator.py:**
   Für jede essence wird die JSON-Datei erneut gelesen, statt die Daten aus `list_essences()` wiederzuverwenden.

### 3.2 Unnötige Zwischenschritte

1. **report_generator.py:_build_daily_prompt()**
   ```
   essences[:15] → für jede essence nochmal JSON lesen → Prompts bauen
   ```
   Könnte direkt die gecachten Daten aus `list_essences()` verwenden.

2. **task_scheduler.py:_ran_recently()**
   Checkt DB bei jedem Job-Loop-Tick (alle 60s). Könnte in-memory mit TTL-Cache ersetzt werden.

### 3.3 Batching-Möglichkeiten

1. **embedding_pipeline.py** hat `batch_size` Parameter, aber `chroma_integration.py:embed_batch()` ist nicht optimal:
   - Kein async-Batching
   - Keine GPU-Memory-Optimierung

2. **hybrid_search.py:_keyword_search()** macht N einzelne Queries für file_path Lookup:
   ```python
   for row in cursor.fetchall():
       # Für JEDE row:
       cursor2 = self.db_conn.execute("SELECT file_path FROM files WHERE id = ?", (file_id,))
   ```
   Könnte mit JOIN oder Batch-Lookup optimiert werden.

### 3.4 Caching-Potenzial

1. **Query-Cache in hybrid_search.py** ist manuelles LRU (100 Einträge):
   - Kein TTL
   - Keine Serialisierung (verloren bei Restart)
   - Nicht distributed-ready

2. **essences_path** wird bei jedem Report komplett gescannt:
   - Könnte einmal laden + in-memory index

3. **Config-Singleton** hat kein Caching der aufgelösten Werte:
   - `get_instance()` resolved bei jedem Aufruf Env-Vars neu

---

## 4. Architektur-Muster

### 4.1 Singletons vs Factories - Status Quo

**Singletons (verwendet):**
- `KBConfig.get_instance()` - Thread-safe Singleton
- `LLMConfig.get_instance()` - Thread-safe Singleton  
- `OllamaEngine.get_instance()` - Singleton via Engine itself
- `_global_search` in hybrid_search.py - Modul-Level Singleton
- `get_chroma()`, `get_expander()`, `get_reranker()` - Lazy Singletons

**Factories (vorhanden):**
- `kb/biblio/engine/factory.py:create_engine()` - Factory-Function

**Problem:** Singletons sind dominant, aber Factory-Pattern existiert. Mischung führt zu Verwirrung.

### 4.2 Dependency Injection Möglichkeiten

**Aktuell:** Nirgends DI verwendet. Alles nutzt `get_instance()` oder erstellt eigene Instanzen.

**Empfehlung:** Factory-Function Pattern erweitern:
```python
# Statt:
engine = OllamaEngine.get_instance()

# Besser:
engine = create_engine(config)  # aus factory.py
```

### 4.3 Interface-Extraktion

**Vorhandene Interfaces:**
- `BaseLLMEngine` - Abstraktion für LLM-Engines ✓
- `SearchProvider` - FEHLT (würde HybridSearch entkoppeln)

**Fehlende Interfaces:**
- `SearchProvider` (semantic vs keyword)
- `ContentStore` (für essences/reports)
- `SchedulerBackend` (für Task-Scheduling)

### 4.4 Plugin-Architektur

**Vorhanden:**
- `ChromaDBPlugin` + `EmbeddingTask` in `chroma_plugin.py`
- Module-Redirects für Migration

**Problem:** Plugin-System ist nur für ChromaDB. Für echte Erweiterbarkeit wäre ein Registry-Pattern besser:
```python
class PluginRegistry:
    @classmethod
    def register(cls, name: str, handler: type): ...
    
    @classmethod  
    def get(cls, name: str) -> type: ...
```

---

## 5. Lesbarkeit & Wartbarkeit

### 5.1 Komplexe verschachtelte Logik

**Worst Offender: task_scheduler.py:run_job()**
- ~150 Zeilen, 4-fach verschachtelt (for-loop mit retry + try/except + timeout + callback)
- Sollte in kleinere Methoden aufgeteilt werden

**hybrid_search.py:_keyword_search_fts()**
- ~80 Zeilen mit Fallback-Logik (FTS5 → LIKE)
- BM25-Score-Berechnung mit Kommentaren über Kommentaren

**report_generator.py:_generate_with_retry()**
- Retry-Loop mit Exponential-Backoff
- Fehlerbehandlung vermischt Logging + sleeping + exception

### 5.2 Undokumentierte Annahmen

1. **hybrid_search.py:CHROMA_PATH** - nicht definiert, sollte im Config sein
   ```python
   try:
       self.chroma_path = Path(CHROMA_PATH)
   except NameError:
       self.chroma_path = Path(_default_chroma_path)
   ```

2. **task_scheduler.py** - cron使用的是 6 für Sonntag (ISO: 0=Montag):
   ```python
   "0 4 * * 6"  # 6 = Sunday (0=Mon convention)  <-- Kommentar stimmt nicht!
   ```

3. **essences_path** wird als bestehend angenommen ohne Check in vielen Generatoren.

### 5.3 Kryptische Namen

| Name | Bedeutung |
|------|-----------|
| `chroma` | Lokale Variable überschreibt Class-Name `ChromaIntegration` |
| `_fts5_checked` | Boolean-Flag für Cache |
| `_query_cache` | Dict mit Cache-Key als key |
| `hs` | Hotspot-Kurzform |
| `essence_hash` | 16-Zeichen SHA prefix, nicht voller Hash |
| `_global_search` | Modul-Level Singleton |

---

## Empfohlene Refactors (Priorisiert)

### Priorität 1: Interface-Extraktion (Impact: Hoch, Aufwand: Mittel)

**Ziel:** HybridSearch von ChromaDB/SQLite entkoppeln für Cluster-Analyse

```python
# Neue Datei: src/library/search_providers.py
from abc import ABC, abstractmethod

class SemanticSearchProvider(ABC):
    @abstractmethod
    async def search(self, query: str, limit: int) -> list[dict]: ...

class KeywordSearchProvider(ABC):
    @abstractmethod
    async def search(self, query: str, limit: int) -> list[dict]: ...

# Implementations:
class ChromaSemanticProvider(SemanticSearchProvider): ...
class ChromaKeywordProvider(KeywordSearchProvider): ...
class SQLiteFTS5Provider(KeywordSearchProvider): ...
```

**Aufwand:** ~200 Zeilen neue Interfaces + Refactor von ~100 Zeilen in HybridSearch

### Priorität 2: Module Aufspalten (Impact: Hoch, Aufwand: Hoch)

**report_generator.py** (1242 → 400 + 400 + 200 + 200)
- `report_data_collector.py` - Data Collection + Hotspot Computation
- `report_prompt_builder.py` - Prompt Templates + Building
- `report_generator.py` - Orchestration only (dünn)
- `graph_data_generator.py` - Graph Generation

**task_scheduler.py** (1222 → 400 + 400 + 200 + 200)
- `cron_parser.py` - Cron Expression Parsing + should_run()
- `job_registry.py` - Job Registration + State Management
- `job_executor.py` - Execution + Retry Logic
- `task_scheduler.py` - Scheduler Loop + Signal Handling

**Aufwand:** ~2-3 Tage pro Modul

### Priorität 3: Dependency Injection einführen (Impact: Mittel, Aufwand: Niedrig)

**Ziel:** Config-Singleton durch Factory ersetzen

```python
# kb/biblio/config.py - Factory hinzufügen
def create_llm_config(**kwargs) -> LLMConfig:
    return LLMConfig(**kwargs)

def get_llm_config() -> LLMConfig:
    """Backward compatibility"""
    if LLMConfig._instance is None:
        LLMConfig._instance = LLMConfig()
    return LLMConfig._instance
```

Danach können Engine + ContentManager + Generator Config injiziert bekommen statt via Singleton zu greifen.

**Aufwand:** ~1 Tag

### Priorität 4: Redundanzen eliminieren (Impact: Niedrig, Aufwand: Niedrig)

- File Hashing in einer Utils-Funktion zusammenführen
- essences_path einmal laden + cache (statt反复 Lesen)
- Query Cache mit TTL versehen

**Aufwand:** ~4 Stunden

### Priorität 5: Dokumentation verbessern (Impact: Mittel, Aufwand: Niedrig)

- Kommentare für kryptische Variablen
- Cron-Weekday-Konvention dokumentieren
- CHROMA_PATH auflösen

**Aufwand:** ~2 Stunden

---

## Fazit

Das kb-framework hat eine solide Grundarchitektur mit async-first Design und Lazy Loading. Die Hauptprobleme sind:

1. **Zu große Module** - Single-Responsibility-Verletzungen in 5 kritischen Dateien
2. **Enge Kopplung** - ChromaDB/SQLite fest in HybridSearch verdrahtet
3. **Singletons überall** - erschwert Testbarkeit und Konfiguration

**Quick Wins:**
- Interface-Extraktion für SearchProvider (ermöglicht Cluster-Analyse)
- Config-Factory Pattern (verbessert Testbarkeit)
- Cron-Kommentar fixen (wartbarkeit)

**Langfristig:**
- Modul-Aufspaltung nach SRP
- Plugin-Registry für Erweiterbarkeit
- DI-Container Evaluation (z.B. `punq`, `dependency-injector`)

---

*Analyse erstellt von Sir Stern*  
*Feedback und Fragen gerne an den Main Agent*
