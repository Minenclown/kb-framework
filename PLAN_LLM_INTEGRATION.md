# LLM-Integration Implementierungsplan

**Datum:** 2026-04-15  
**Basierend auf:** `ANALYSIS_LLM_INTEGRATION.md`  
**Modell:** Gemma4:e2b via Ollama/e2b  
**Status:** ⏳ Geplant

---

## 1. Überblick

Dieser Plan beschreibt die Integration eines LLM-gestützten Knowledge-Management-Systems in das kb-framework. Das System besteht aus vier Hauptkomponenten:

| Komponente | Intervall | Beschreibung |
|------------|-----------|--------------|
| **File-Watcher** | Alle 20 Min | Überwacht Library-Ordner auf neue Dateien |
| **KB-Validator** | Alle 12h | Vollständige Integritätsprüfung der Knowledge Base |
| **Essence-Generator** | Bei neuem Content | Sofortige Essenz-Extraktion aus neuen Dokumenten |
| **Gemma4-Integration** | On-Demand | Ollama-Client für LLM-Kommunikation |

---

## 2. Dateistruktur

### 2.1 System-Code (`kb/llm/`)

```
kb/llm/
├── __init__.py                 # Package-Init mit Exports
├── config.py                   # LLM-spezifische Konfiguration
├── engine.py                   # Ollama/Gemma4 Client (Singleton)
├── models.py                   # Pydantic-Modelle für Request/Response
├── generator.py                # EssenceExtractor, ReportGenerator
├── watcher.py                  # FileSystemWatcher mit 20min Interval
├── scheduler.py                # Cron-Job Verwaltung
└── validators/
    ├── __init__.py
    ├── integrity.py            # Integritätsprüfung
    └── consistency.py          # Konsistenzprüfung zwischen Content
```

### 2.2 Generierter Content (`kb/library/llm/`)

```
kb/library/llm/
├── __init__.py                 # Leer (kein Python-Code)
├── essences/                    # Extrahierte Essenzen
│   └── [file_hash]/
│       ├── essence.json        # Strukturierte Essence
│       ├── source.txt          # Extrahieter Originaltext
│       └── metadata.json       # Quellen-Metadaten
├── reports/                     # Generierte Berichte
│   └── [timestamp]/
│       ├── report.md           # Hauptbericht
│       └── metadata.json       # Query, Quellen, Zeitstempel
└── graph/                       # Wissensgraph
    └── knowledge_graph.json    # Graph-JSON mit Entitäten
```

### 2.3 Vollständige Struktur (Deltas zum Bestand)

```
kb-framework/
├── kb/
│   └── llm/                    # ★ NEU
│       ├── __init__.py
│       ├── config.py
│       ├── engine.py
│       ├── models.py
│       ├── generator.py
│       ├── watcher.py
│       ├── scheduler.py
│       └── validators/
│           ├── __init__.py
│           ├── integrity.py
│           └── consistency.py
│   └── library/
│       └── llm/                # ★ NEU
│           ├── __init__.py
│           ├── essences/
│           ├── reports/
│           └── graph/
```

---

## 3. Phasenplan

### Phase 1: Grundinfrastruktur (Tag 1-2)

| Task | Datei | Abhängigkeit | Aufwand |
|------|------|--------------|---------|
| 1.1 | `kb/llm/__init__.py` erstellen | - | 15 Min |
| 1.2 | `kb/llm/config.py` erstellen | - | 30 Min |
| 1.3 | `kb/llm/models.py` mit Pydantic-Modellen | 1.2 | 1h |
| 1.4 | `kb/llm/engine.py` - OllamaClient Singleton | 1.2, 1.3 | 2h |
| 1.5 | `kb/llm/engine.py` - Connection Pooling | 1.4 | 1h |
| 1.6 | Unit-Tests für Engine | 1.4 | 1h |

**Deliverable:** `OllamaEngine` ist importierbar und funktionsfähig.

```python
# Verwendung nach Phase 1
from kb.llm import OllamaEngine, LLMConfig

config = LLMConfig(
    model="gemma4:e2b",
    ollama_url="http://localhost:11434",
    temperature=0.7,
    timeout=120
)
engine = OllamaEngine(config)
```

---

### Phase 2: Content-Verzeichnis (Tag 2)

| Task | Datei | Abhängigkeit | Aufwand |
|------|------|--------------|---------|
| 2.1 | `kb/library/llm/__init__.py` | - | 5 Min |
| 2.2 | `kb/library/llm/essences/` anlegen | - | 5 Min |
| 2.3 | `kb/library/llm/reports/` anlegen | - | 5 Min |
| 2.4 | `kb/library/llm/graph/` anlegen | - | 5 Min |
| 2.5 | `.gitkeep` Dateien hinzufügen | 2.2-2.4 | 5 Min |

**Deliverable:** Content-Verzeichnis existiert mit korrekter Struktur.

---

### Phase 3: Essence-Generierung (Tag 3-5)

| Task | Datei | Abhängigkeit | Aufwand |
|------|------|--------------|---------|
| 3.1 | `EssenceExtractor` Klasse in `generator.py` | Phase 1 | 2h |
| 3.2 | Prompts für Essence-Extraktion definieren | 3.1 | 1h |
| 3.3 | File-to-Hash Funktionalität | 3.1 | 1h |
| 3.4 | JSON-Schema für `essence.json` definieren | 3.1 | 1h |
| 3.5 | Write-Logik für `essences/[hash]/` | 3.3, 3.4 | 1h |
| 3.6 | Integration mit OllamaEngine | 3.1, Phase 1 | 2h |
| 3.7 | Unit-Tests für EssenceExtractor | 3.6 | 1h |

**Deliverable:** Neue Dateien können automatisch zu Essenzen verarbeitet werden.

```python
# Verwendung nach Phase 3
from kb.llm import OllamaEngine, EssenceExtractor

engine = OllamaEngine()
extractor = EssenceExtractor(engine)

# Neue Datei wird automatisch verarbeitet
essence_path = extractor.extract("/path/to/doc.pdf")
# → kb/library/llm/essences/{hash}/essence.json
```

**essence.json Schema:**

```json
{
  "version": "1.0",
  "source_hash": "sha256:abc123...",
  "source_path": "/path/to/doc.pdf",
  "extracted_at": "2026-04-15T20:00:00Z",
  "model": "gemma4:e2b",
  "essence": {
    "title": "Kern Aussage / Titel",
    "summary": "1-2 Sätze Zusammenfassung",
    "key_points": ["Punkt 1", "Punkt 2", "..."],
    "entities": ["Entität 1", "Entität 2"],
    "relationships": [
      {"from": "Entität 1", "to": "Entität 2", "type": "related_to"}
    ],
    "keywords": ["keyword1", "keyword2"],
    "confidence": 0.85
  }
}
```

---

### Phase 4: Report-Generierung (Tag 5-7)

| Task | Datei | Abhängigkeit | Aufwand |
|------|------|--------------|---------|
| 4.1 | `ReportGenerator` Klasse in `generator.py` | Phase 3 | 2h |
| 4.2 | Multi-Essence Aggregation | 4.1 | 2h |
| 4.3 | Query-basierte Report-Generierung | 4.1 | 2h |
| 4.4 | Write-Logik für `reports/[timestamp]/` | 4.1 | 1h |
| 4.5 | Template-System für Reports | 4.1 | 1h |
| 4.6 | Unit-Tests | 4.5 | 1h |

**Deliverable:** Berichte können aus mehreren Essenzen aggregiert werden.

```python
# Verwendung nach Phase 4
from kb.llm import OllamaEngine, ReportGenerator, EssenceExtractor

engine = OllamaEngine()
report_gen = ReportGenerator(engine)

# Report aus mehreren Essenzen generieren
report_path = report_gen.generate(
    query="Was sind die Haupterkenntnisse zu Topic X?",
    essence_paths=["path/to/essence1.json", "path/to/essence2.json"]
)
# → kb/library/llm/reports/{timestamp}/report.md
```

---

### Phase 5: File-Watcher + Scheduler (Tag 8-10)

| Task | Datei | Abhängigkeit | Aufwand |
|------|------|--------------|---------|
| 5.1 | `FileWatcher` Klasse in `watcher.py` | Phase 3 | 2h |
| 5.2 | 20min Interval Konfiguration | 5.1 | 30 Min |
| 5.3 | Recursive Directory Watching | 5.1 | 1h |
| 5.4 | Change-Detection (hash-basiert) | 5.1 | 1h |
| 5.5 | `Scheduler` Klasse in `scheduler.py` | Phase 4 | 2h |
| 5.6 | Cron-Expression Parser | 5.5 | 1h |
| 5.7 | Job-Queue mit Prioritäten | 5.5 | 2h |
| 5.8 | Integration Watcher → Generator | 5.1, Phase 3 | 1h |
| 5.9 | Unit-Tests | 5.8 | 1h |

**Deliverable:** File-Watcher läuft als Hintergrundprozess.

```bash
# Start File-Watcher
python -m kb llm watch --interval 20m --library /path/to/library

# Mit Cron
python -m kb llm scheduler add --name "hourly-check" --interval "0 * * * *"
```

---

### Phase 6: KB-Validator (Tag 10-12)

| Task | Datei | Abhängigkeit | Aufwand |
|------|------|--------------|---------|
| 6.1 | `IntegrityValidator` in `validators/integrity.py` | Phase 5 | 2h |
| 6.2 | Orphan Detection (Essences ohne Quell-Datei) | 6.1 | 1h |
| 6.3 | Hash-Verifikation (veränderte Quelldateien) | 6.1 | 1h |
| 6.4 | `ConsistencyValidator` in `validators/consistency.py` | 6.1 | 2h |
| 6.5 | Cross-Reference Validation | 6.4 | 1h |
| 6.6 | Graph-Konsistenzprüfung | 6.4 | 1h |
| 6.7 | 12h Cron-Job Konfiguration | 6.1 | 30 Min |
| 6.8 | Validator-Report Generierung | 6.1 | 1h |
| 6.9 | Unit-Tests | 6.8 | 1h |

**Deliverable:** KB-Validator läuft alle 12h und reportet Inkonsistenzen.

```python
# Verwendung nach Phase 6
from kb.llm import IntegrityValidator

validator = IntegrityValidator()
report = validator.run_full_check()
# → Listet fehlende Quellen, veränderte Dateien, etc.
```

---

### Phase 7: CLI-Integration (Tag 12-13)

| Task | Datei | Abhängigkeit | Aufwand |
|------|------|--------------|---------|
| 7.1 | `kb/commands/llm.py` Command Group | Phase 5 | 2h |
| 7.2 | `llm extract` - Einzelne Datei extrahieren | 7.1 | 1h |
| 7.3 | `llm report` - Report generieren | 7.2 | 1h |
| 7.4 | `llm validate` - Validator starten | 7.3 | 1h |
| 7.5 | `llm watch` - Watcher starten | 7.4 | 1h |
| 7.6 | `llm status` - Systemstatus anzeigen | 7.5 | 30 Min |
| 7.7 | Integrationstests | 7.6 | 1h |

**CLI-Nutzung:**

```bash
# Einzelne Datei zu Essence verarbeiten
kb llm extract /path/to/document.pdf

# Report aus allen Essenzen generieren
kb llm report --query "Zusammenfassung aller Erkenntnisse"

# Integritätsprüfung starten
kb llm validate

# Watcher starten
kb llm watch --interval 20m

# Status anzeigen
kb llm status
```

---

## 4. Komponenten-Abhängigkeiten

```
┌─────────────────────────────────────────────────────────────────┐
│                        kb/llm/                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   config.py  │───▶│   models.py  │    │  scheduler.py│      │
│  └──────────────┘    └──────────────┘    └──────┬───────┘      │
│         │                   │                   │              │
│         │                   ▼                   ▼              │
│         │            ┌──────────────┐    ┌──────────────┐      │
│         │            │  engine.py   │◀───│  watcher.py  │      │
│         │            │ (OllamaClient)│    └──────┬───────┘      │
│         │            └──────┬───────┘           │              │
│         │                   │                   │              │
│         │                   ▼                   │              │
│         │            ┌──────────────┐           │              │
│         │            │ generator.py │◀──────────┘              │
│         │            │ (EssenceExtractor, ReportGenerator)      │
│         │            └──────┬───────┘                         │
│         │                   │                                 │
│         │                   ▼                                 │
│         │            ┌──────────────┐                         │
│         │            │validators/  │                          │
│         │            │integrity.py │                          │
│         │            │consistency.py                         │
│         │            └──────────────┘                         │
│         │                   │                                 │
│         ▼                   ▼                                 │
│  ┌──────────────┐    ┌──────────────┐                         │
│  │kb/library/  │    │kb/library/   │                         │
│  │llm/essences/│    │llm/reports/  │                         │
│  └──────────────┘    └──────────────┘                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Abhängigkeits-Matrix

| Komponente | Abhängig von | Gibt Output an |
|------------|--------------|----------------|
| `config.py` | - | engine, models |
| `models.py` | config | engine, generator |
| `engine.py` | config, models | generator, watcher |
| `generator.py` | engine, models | essences/, reports/ |
| `watcher.py` | engine | generator (Trigger) |
| `scheduler.py` | - | watcher, validators |
| `validators/` | generator | reports/ (Validation Reports) |

---

## 5. Cron/Scheduler-Konfiguration

### 5.1 Cron-Job Definitionen

| Job | Intervall | Cron-Expression | Aufruf |
|-----|-----------|-----------------|--------|
| **File-Watcher** | 20 Min | - ( kontinuierlich) | `python -m kb llm watch --daemon` |
| **KB-Validator** | 12h | `0 */12 * * *` | `python -m kb llm validate --cron` |
| **Essence-GC** | 1x täglich | `0 3 * * *` | Löscht verwaiste Essences |
| **Graph-Rebuild** | 1x wöchentlich | `0 4 * * 0` | Rebuild des Wissensgraphs |

### 5.2 Scheduler-Konfiguration (JSON)

```json
{
  "scheduler": {
    "enabled": true,
    "jobs": [
      {
        "id": "kb-validator-12h",
        "name": "KB-Validator",
        "schedule": "0 */12 * * *",
        "command": ["python", "-m", "kb", "llm", "validate"],
        "timeout": 3600,
        "priority": "high",
        "notify_on_failure": true
      },
      {
        "id": "essence-gc-daily",
        "name": "Essence Garbage Collection",
        "schedule": "0 3 * * *",
        "command": ["python", "-m", "kb", "llm", "gc", "--type", "essences"],
        "timeout": 600,
        "priority": "low"
      },
      {
        "id": "graph-rebuild-weekly",
        "name": "Knowledge Graph Rebuild",
        "schedule": "0 4 * * 0",
        "command": ["python", "-m", "kb", "llm", "graph", "rebuild"],
        "timeout": 7200,
        "priority": "medium"
      }
    ]
  },
  "watcher": {
    "enabled": true,
    "interval_minutes": 20,
    "library_paths": [
      "/home/lumen/projects/kb-framework/library/content"
    ],
    "file_extensions": [".pdf", ".txt", ".md", ".docx"],
    "exclude_patterns": ["*.tmp", ".*", "__pycache__"]
  }
}
```

### 5.3 Systemd-Timer (Alternative zu Cron)

```ini
# /etc/systemd/system/kb-llm-validator.timer
[Unit]
Description=KB LLM Validator (12h)

[Timer]
OnCalendar=*-*/12:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

```ini
# /etc/systemd/system/kb-llm-validator.service
[Unit]
Description=KB LLM Validator
After=network.target

[Service]
Type=oneshot
WorkingDirectory=/home/lumen/projects/kb-framework
ExecStart=/home/lumen/.venv/kb/bin/python -m kb llm validate
```

---

## 6. Testing-Strategie

### 6.1 Test-Struktur

```
tests/
├── llm/
│   ├── __init__.py
│   ├── test_engine.py         # OllamaClient Tests
│   ├── test_generator.py      # Essence/Report Generator Tests
│   ├── test_watcher.py        # FileWatcher Tests
│   ├── test_scheduler.py       # Scheduler Tests
│   ├── test_validators/
│   │   ├── __init__.py
│   │   ├── test_integrity.py
│   │   └── test_consistency.py
│   └── conftest.py            # Fixtures
```

### 6.2 Test-Fixtures (`conftest.py`)

```python
import pytest
from unittest.mock import Mock, MagicMock
from kb.llm import OllamaEngine, LLMConfig

@pytest.fixture
def mock_ollama_response():
    return {
        "model": "gemma4:e2b",
        "response": "Mocked LLM response",
        "done": True
    }

@pytest.fixture
def ollama_engine():
    config = LLMConfig(
        model="gemma4:e2b",
        ollama_url="http://localhost:11434",
        timeout=30
    )
    return OllamaEngine(config)

@pytest.fixture
def temp_content_dir(tmp_path):
    content = tmp_path / "library" / "llm"
    content.mkdir(parents=True)
    return content

@pytest.fixture
def sample_pdf(tmp_path):
    pdf = tmp_path / "test.pdf"
    pdf.write_text("Sample PDF content for testing")
    return pdf
```

### 6.3 Test-Kategorien

#### 6.3.1 Unit-Tests (schnell, isoliert)

| Test | Beschreibung | Mocks |
|------|--------------|-------|
| `test_engine_generate` | LLM-Antwort-Parsing | HTTP responses |
| `test_engine_timeout` | Timeout-Handling | HTTP responses |
| `test_generator_essence_schema` | JSON-Schema Validation | OllamaEngine |
| `test_watcher_hash_detection` | Hash-Änderungs-Erkennung | FileSystem |
| `test_scheduler_cron_parse` | Cron-Parsing | - |

#### 6.3.2 Integration-Tests (langsam, mit e2b)

| Test | Beschreibung | Anforderung |
|------|--------------|-------------|
| `test_full_essence_extraction` | Vollständige Extraktion mit e2b | Ollama mit gemma4:e2b |
| `test_report_aggregation` | Multi-Essence Aggregation | Ollama mit gemma4:e2b |
| `test_watcher_new_file` | Neue Datei → Essence | Laufender Watcher |
| `test_validator_orphan_detection` | Orphan-Erkennung | Bestehende Essences |

#### 6.3.3 End-to-End Tests (vollständiger Flow)

```bash
# E2E Test: Neue Datei → Essence → Report
$ echo "Test Content" > /tmp/test_doc.txt
$ python -m kb llm extract /tmp/test_doc.txt
$ python -m kb llm report --query "Was enthält das Dokument?"
# → Report sollte "Test Content" referenzieren
```

### 6.4 Mock-Strategie

| Komponente | Mock-Tool | Wann |
|------------|-----------|------|
| Ollama API | `responses` library | Immer bei Unit-Tests |
| FileSystem | `tmp_path` fixture | Bei Watcher-Tests |
| Config | `@pytest.fixture` | Bei allen Tests |

### 6.5 CI/CD Pipeline

```yaml
# .github/workflows/llm-tests.yml
name: LLM Integration Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install pytest pytest-mock
      - name: Run unit tests
        run: pytest tests/llm/test_*.py -v --ignore=tests/llm/test_*integration*
  
  integration-tests:
    runs-on: ubuntu-latest
    services:
      ollama:
        image: ollama/ollama:latest
        ports:
          - 11434:11434
    steps:
      - name: Pull Gemma4 model
        run: ollama pull gemma4:e2b
      - name: Run integration tests
        run: pytest tests/llm/test_*integration* -v
```

---

## 7. Fehlerbehandlung

### 7.1 Retry-Logik

```python
# engine.py
import time
from functools import wraps

def retry_on_failure(max_retries=3, delay=5):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except OllamaConnectionError as e:
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(delay * (attempt + 1))
        return wrapper
    return decorator
```

### 7.2 Fehler-Zustände

| Zustand | Erkennung | Aktion |
|---------|-----------|--------|
| Ollama nicht erreichbar | ConnectionError | Retry + Alert nach 3x |
| Modell nicht verfügbar | 404 from Ollama | Alert + Log |
| Content-Datei gelöscht | FileNotFoundError | Orphan-Markierung |
| Hash-Konflikt | Doppelter Hash | Neuer Hash mit Suffix |
| Timeout | Request timeout | Retry mit längerem Timeout |

### 7.3 Logging

```python
# KBLogger verwenden
from kb.base.logger import KBLogger

logger = KBLogger(__name__)

logger.info("Starting essence extraction", extra={
    "file": "/path/to/doc.pdf",
    "hash": "abc123"
})

logger.warning("Ollama timeout, retrying...", extra={
    "attempt": 2,
    "max_retries": 3
})

logger.error("Failed to extract essence", extra={
    "file": "/path/to/doc.pdf",
    "error": str(e)
})
```

---

## 8. Implementierungs-Reihenfolge (Zusammenfassung)

```
Woche 1:
├── Tag 1-2: Phase 1 - Grundinfrastruktur (engine, config, models)
├── Tag 2:   Phase 2 - Content-Verzeichnis
└── Tag 3-5: Phase 3 - Essence-Generierung

Woche 2:
├── Tag 5-7: Phase 4 - Report-Generierung
├── Tag 8-10: Phase 5 - File-Watcher + Scheduler
└── Tag 10-12: Phase 6 - KB-Validator

Woche 3:
└── Tag 12-13: Phase 7 - CLI-Integration
```

---

## 9. Risiken und Mitigation

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|------------|
| Ollama/e2b nicht verfügbar | Mittel | Hoch | Mock-Tests, Offline-Fallback |
| Performance bei großen Dateien | Niedrig | Mittel | Chunking, Streaming |
| Speicherüberlauf bei Batch | Niedrig | Hoch | Batch-Size Limits, Queue |
| Hash-Kollisionen | Sehr niedrig | Niedrig | SHA-256 + Suffix |

---

## 10. Maintenance

### 10.1 Regelmäßige Tasks

| Task | Frequenz | Verantwortlich |
|------|----------|----------------|
| Ollama-Image aktualisieren | Monatlich | System |
| Modell neu trainieren/updaten | Bei Bedarf | Mensch |
| Essence-Deduplizierung | Wöchentlich | Scheduler |
| Log-Rotation | Täglich | System |

### 10.2 Monitoring

```bash
# Status-Check
kb llm status

# Output-Beispiel:
# LLM Engine: ✓ Verbunden (gemma4:e2b)
# Watcher: ✓ Aktiv (20min Interval)
# Letzter Check: vor 15 Min
# Essences: 47 (542 KB)
# Reports: 12 (1.2 MB)
# Validator: ⏳ Nächste Prüfung in 6h
```

---

*Plan erstellt: 2026-04-15*  
*Basierend auf: ANALYSIS_LLM_INTEGRATION.md*