# BIBLIO_STRUCTURE_ANALYSIS.md

## Analyse: Welche Unterordner in `kb/library/biblio/` werden benötigt?

### Ausgangsverzeichnis
```
kb/library/biblio/
├── essences/      ← SHA256-Hash-Ordner mit essence.md + essence.json
├── graph/         ← knowledge_graph.json + Backups
├── incoming/      ← Warteschlange für neue Dateien
└── reports/
    ├── daily/
    ├── weekly/
    └── monthly/
```

---

## 1. Hardcodierte Pfade im Code

Alle Pfade werden über `LLMConfig` in `kb/biblio/config.py` zentral definiert:

| Property | Pfad | Verwendung in |
|---|---|---|
| `essences_path` | `kb/library/biblio/essences` | `content_manager.py`, `essence_generator.py`, `task_scheduler.py` |
| `reports_path` | `kb/library/biblio/reports` | `content_manager.py`, `task_scheduler.py` |
| `graph_path` | `kb/library/biblio/graph` | `content_manager.py`, `task_scheduler.py` |
| `incoming_path` | `kb/library/biblio/incoming` | `content_manager.py`, `task_scheduler.py` |
| `templates_path` | `kb/biblio/templates` | ⚠️ **NICHT** in `kb/library/biblio/` (sondern im Source-Code) |

### Reports: Zusätzliche Unterordner
`content_manager.py` erstellt bei `ensure_dirs()` automatisch:
```
reports/
├── daily/
├── weekly/
└── monthly/
```
Diese sind in `LLMContentManager._ensure_directories()` hardcodiert.

---

## 2. Welche Unterordner werden erwartet und warum?

### ✅ `essences/` — **BENÖTIGT**
**Begründung:**
- `content_manager.py` speichert Essenzen als `essences/[hash]/essence.md` + `essence.json`
- `task_scheduler.py` liest dort für `kb-validator`, `graph-rebuild`, `essenz-gc`
- `file_watcher.py` (indirekt via `EssenzGenerator`) erstellt dort Essenzen
- Dateien werden **nie** direkt in den Ordner gelegt, sondern in Hash-Unterordner

**Inhalt zur Laufzeit:**
- `essences/[16-char-sha256-hash]/essence.md`
- `essences/[16-char-sha256-hash]/essence.json`

---

### ✅ `graph/` — **BENÖTIGT**
**Begründung:**
- `task_scheduler.py` (`_job_graph_rebuild`) schreibt `graph/knowledge_graph.json`
- Backups werden erstellt als `graph/knowledge_graph_[timestamp].json.bak`
- Der Ordner muss existieren, sonst schlägt `graph-rebuild` fehl

**Inhalt zur Laufzeit:**
- `graph/knowledge_graph.json` (Hauptgraph)
- `graph/knowledge_graph_[YYYYMMDD_HHMMSS].json.bak` (Backups)

---

### ✅ `incoming/` — **BENÖTIGT**
**Begründung:**
- `content_manager.py` bietet `add_incoming()`, `list_incoming()`, `clear_incoming()`
- `task_scheduler.py` (`_job_essenz_gc`) räumt alte Dateien aus `incoming/` auf (files older than 90 days)
- Wird als Warteschlange für unprozessierte Dateien genutzt

**Inhalt zur Laufzeit:**
- Eingehende Dateien mit Timestamp-Präfix: `incoming/[YYYYMMDD_HHmmss]_[original_name]`

---

### ✅ `reports/` — **BENÖTIGT**
**Begründung:**
- `content_manager.py` speichert Reports in `reports/[type]/[timestamp]_report.md`
- `task_scheduler.py` (`kb-validator`) scannt `reports/` rekursiv nach `*_report.md`
- ReportGenerator nutzt `daily`, `weekly`, `monthly` als Unterordner

**Unterordner (automatisch erstellt):**
```
reports/daily/     ← täglich generierte Berichte
reports/weekly/    ← wöchentlich generierte Berichte
reports/monthly/   ← monatlich generierte Berichte
```

---

### ⚠️ `essences_archive/` — **NICHT in `kb/library/biblio/`**
**Begründung:**
- `task_scheduler.py` (`_job_essenz_gc`) archiviert nach: `essences_path.parent / "essences_archive"`
- Das ist `kb/library/essences_archive/` (eine Ebene **über** `biblio/`)
- Wird **nicht** direkt in `kb/library/biblio/` erwartet

---

## 3. Konfigurationsquellen

### Primär: `LLMConfig` in `kb/biblio/config.py`
```python
@property
def library_biblio_path(self) -> Path:
    return self._kb_config.base_path / "library" / "biblio"

@property
def essences_path(self) -> Path:
    return self.library_biblio_path / "essences"

@property
def reports_path(self) -> Path:
    return self.library_biblio_path / "reports"

@property
def graph_path(self) -> Path:
    return self.library_biblio_path / "graph"

@property
def incoming_path(self) -> Path:
    return self.library_biblio_path / "incoming"
```

### Datenbanken (in `kb/library/`):
- `watcher_state.db` → `kb/library/watcher_state.db`
- `scheduler_state.db` → `kb/library/scheduler_state.db`

---

## 4. Zusammenfassung: Benötigte Unterordner

| Unterordner | Status | .gitkeep nötig? | Begründung |
|---|---|---|---|
| `essences/` | ✅ Benötigt | **Ja** | Enthält Hash-Ordner mit Essenzen; muss existieren |
| `reports/` | ✅ Benötigt | **Ja** | Enthält daily/, weekly/, monthly/ Unterordner |
| `reports/daily/` | ✅ Automatisch erstellt | Nein | `ensure_dirs()` erstellt automatisch |
| `reports/weekly/` | ✅ Automatisch erstellt | Nein | `ensure_dirs()` erstellt automatisch |
| `reports/monthly/` | ✅ Automatisch erstellt | Nein | `ensure_dirs()` erstellt automatisch |
| `graph/` | ✅ Benötigt | **Ja** | Enthält knowledge_graph.json + Backups |
| `incoming/` | ✅ Benötigt | **Ja** | Warteschlange für neue Dateien |
| `essences_archive/` | ❌ Anderswo | — | Liegt in `kb/library/essences_archive/` |
| `templates/` | ❌ Im Source | — | Liegt in `kb/biblio/templates/` (nicht in library) |

---

## 5. Empfehlung: .gitkeep-Dateien

### Mindestens erforderlich für ein leeres Repository:
```
kb/library/biblio/
├── .gitkeep          ← Hauptordner in Git behalten
├── essences/
│   └── .gitkeep      ← Wird bei gc archiviert/erstellt
├── graph/
│   └── .gitkeep      ← Erstellt bei graph-rebuild
├── incoming/
│   └── .gitkeep      ← Manuell oder automatisch befüllt
└── reports/
    ├── .gitkeep      ← Hauptordner
    └── daily/
        └── .gitkeep  ←werden von ensure_dirs() angelegt
    └── weekly/
        └── .gitkeep
    └── monthly/
        └── .gitkeep
```

### Empfohlene `.gitkeep`-Strategie:
```bash
# Nur diese .gitkeep Dateien sind nötig:
touch kb/library/biblio/.gitkeep
touch kb/library/biblio/essences/.gitkeep
touch kb/library/biblio/graph/.gitkeep
touch kb/library/biblio/incoming/.gitkeep
touch kb/library/biblio/reports/.gitkeep
touch kb/library/biblio/reports/daily/.gitkeep
touch kb/library/biblio/reports/weekly/.gitkeep
touch kb/library/biblio/reports/monthly/.gitkeep
```

**Hinweis:** Die daily/weekly/monthly Unterordner werden von `LLMContentManager.ensure_dirs()` automatisch erstellt. Ein `.gitkeep` in jedem stellt sicher, dass die leeren Ordner in Git bleiben.

---

## 6. Wichtiger Hinweis zu `templates/`

Der Ordner `kb/biblio/templates/` ist Teil des **Source-Codes** (nicht der Daten):
```
kb/biblio/templates/
├── essence_template.md
└── report_template.md
```

Dieser Ordner gehört **nicht** nach `kb/library/biblio/`, sondern ist Teil der Codebasis und wird über `templates_path` in `LLMConfig` referenziert:
```python
@property
def templates_path(self) -> Path:
    return Path(__file__).parent / "templates"  # → kb/biblio/templates/
```
