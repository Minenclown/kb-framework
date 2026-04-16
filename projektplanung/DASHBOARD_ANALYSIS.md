# DASHBOARD_ANALYSIS.md – HTML Dashboard Interface für kb-framework

> **Datum:** 2026-04-16
> **Status:** Analyse abgeschlossen

---

## 1. CLI/API Übersicht (alle Commands)

### 1.1 Verfügbare CLI-Befehle

```
kb sync [--stats] [--dry-run] [--delta] [--full] [--file-id ID] [--delete-orphans] [--batch-size N]
kb audit [--output-dir PATH] [--skip-chroma] [--skip-files] [-v] [--export-csv PATH] [--checks LIST]
kb ghost [--scan-dirs DIR] [--extensions EXT] [--output-dir PATH]
kb search QUERY [--limit N] [--semantic-only] [--keyword-only] [--format short|full] [--file-type EXT] [--date-from YYYY-MM-DD] [--date-to YYYY-MM-DD] [--debug]
kb warmup [--verbose] [--timeout N] [--model NAME] [--check] [--force]
kb llm status|generate essence|generate report|watch start|stop|status|scheduler list|trigger|config|engine status|engine switch|engine test|list essences|list reports
kb engine-list [-v]
kb engine-info ollama|huggingface|transformers
kb backup [--library-only] [--full] [--output PATH]
```

### 1.2 Python-API (direkt importierbar)

| Komponente | Import | Verwendung |
|---|---|---|
| `KBConfig` | `from kb.base.config import KBConfig` | `KBConfig.get_instance()` – Singleton Config |
| `KBConnection` | `from kb.base.db import KBConnection` | Context Manager für SQLite |
| `HybridSearch` | `from kb.library.knowledge_base.hybrid_search import HybridSearch` | Hybrid Search (semantic + keyword) |
| `BaseCommand` | `from kb.base.command import BaseCommand` | Abstract Base für Commands |
| `KBLogger` | `from kb.base.logger import KBLogger` | Logging Singleton |

### 1.3 Welche Funktionen brauchen Echtzeit-Updates?

| Funktion | Echtzeit? | Begründung |
|---|---|---|
| **Suche (Search)** | ⚡ **Ja** | User erwartet sofortige Results |
| **Sync-Status** | ⚡ **Ja** | Progress-Updates während Sync |
| **Audit-Results** | ⚡ **Ja** (wenn laufend) | Langlaufende Operation |
| **Ghost-Scan** | ⚡ **Ja** | Progress während Scan |
| **LLM Watcher** | ⚡ **Ja** | Live-Status File-Watcher |
| **LLM Scheduler** | ⚡ **Ja** | Job-Queue Status |
| **Essenzen/Reports auflisten** | 🐢 Nein | Read-only, kann gecached werden |
| **Backup** | ⚡ **Ja** (Progress) | Backup läuft evtl. lange |
| **Engine-Status** | 🐢 Nein | Statischer Status, seltener Wechsel |
| **Config-Anzeige** | 🐢 Nein | Read-only |

---

## 2. Datenquellen

### 2.1 SQLite (`knowledge.db`)

**Pfad:** `~/.openclaw/kb/knowledge.db` (oder `KB_DB_PATH`)

**Tabellen:**
```sql
files           -- Alle indexierten Dateien
file_sections   -- Dateiabschnitte mit Embeddings
embeddings      -- Vektor-Embeddings (ChromaDB-Metadaten)
```

**Direkter Zugriff via:**
```python
from kb.base.db import KBConnection, get_db

# Context Manager
with get_db(config.db_path) as conn:
    rows = conn.fetchall("SELECT * FROM files LIMIT 10")
    conn.commit()
```

### 2.2 ChromaDB

**Pfad:** `~/.openclaw/kb/chroma_db/` (oder `KB_CHROMA_PATH`)

**Struktur:** Standard ChromaDB Persistence (SQLite-basiert + Embeddings)

**Zugriff:**
- Über `HybridSearch` in `kb.library.knowledge_base.hybrid_search`
- Direkt über `chromadb` Python-Paket

### 2.3 Dateisystem (`kb/library/`)

```
kb/library/
├── biblio.db              -- BibTeX/DOI-Datenbank
├── essences/              -- Generierte Essenzen (LLM)
│   └── *.md
├── reports/                -- Tages-/Wochen-/Monatsberichte
│   └── *.md
├── graph/                  -- Wissensgraph-Daten
└── incoming/              -- Unverarbeitete eingehende Daten
```

**Zugriff:** Direkter Dateisystem-Zugriff (Pathlib)

### 2.4 Logs

**Log-Verzeichnis:** `~/.openclaw/kb/logs/` (konfigurierbar via `KBLogger`)

**Formate:** Text-Logs, potentiell JSON-Logs bei Debug-Modus

---

## 3. Technologie-Optionen

### 3.1 Empfehlung: FastAPI

| Kriterium | Bewertung |
|---|---|
| **Performance** | ✅ Asynchron, gut für I/O-lastige KB-Operationen |
| **Python-Nativ** | ✅ Direkte Integration mit kb-framework |
| **WebSocket** | ✅ Native Unterstützung für Echtzeit |
| **OpenAPI/Swagger** | ✅ Auto-Dokumentation |
| **Starlette** | ✅ Basiert auf performanter ASGI-Library |

**Alternativen verworfen:**
- **Flask:** Keine native async/WebSocket-Unterstützung
- **Django:** Zu schwergewichtig für Dashboard
- **React/Vue Frontend:** Zu komplex – Plain HTML/JS reicht

### 3.2 Echtzeit: WebSockets (FastAPI native)

```python
from fastapi import WebSocket

@router.websocket("/ws/sync")
async def websocket_sync(websocket: WebSocket):
    # Progressive Updates während kb sync
    await websocket.send_json({"progress": 50, "status": "indexing"})
```

### 3.3 Frontend: Plain HTML + Vanilla JS

**Begründung:**
- Kein Build-Prozess nötig
- Schnell zu entwickeln
- CSS Framework (Tailwind oder Pico.css) für Styling
- Keine komplexe Client-Logik

### 3.4 Embedded vs. Externer Webserver

| Option | Vorteil | Nachteil |
|---|---|---|
| **Eingebettet** (`kb dashboard`) | Startet mit `kb` Command, kein Extra-Port | Vermischt sich mit CLI-Logik |
| **Extern** (`uvicorn/fastapi`) | Sauber getrennt, besser skalierbar | Extra Prozess |
| **Hybrid** ✅ | **Empfohlen:** `kb dashboard` startet intern uvicorn | Beste Balance |

**Hybrid-Ansatz:**
```
kb dashboard --port 8765   # Startet embedded FastAPI
kb dashboard --stop        # Stoppt den Server
kb dashboard --restart     # Restart
```

---

## 4. Verzeichnis-Struktur

### 4.1 Vorgeschlagene Struktur

```
~/projects/kb-framework/kb/dashboard/
├── __init__.py                 # Dashboard-Modul
├── server.py                   # FastAPI Application + WebSocket
├── commands.py                 # Dashboard-spezifische CLI-Commands
├── api/
│   ├── __init__.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── search.py           # /api/search
│   │   ├── sync.py             # /api/sync
│   │   ├── audit.py            # /api/audit
│   │   ├── ghost.py            # /api/ghost
│   │   ├── llm.py              # /api/llm/*
│   │   ├── config.py           # /api/config
│   │   └── stats.py            # /api/stats (DB/ChromaDB-Stats)
│   └── models.py               # Pydantic Models
├── web/
│   ├── index.html              # Single Page Dashboard
│   ├── css/
│   │   └── dashboard.css       # Custom styles (oder Pico.css CDN)
│   └── js/
│       ├── app.js              # Main application logic
│       ├── api-client.js       # API calls + WebSocket handler
│       └── components/
│           ├── search.js       # Search component
│           ├── sync.js          # Sync component
│           └── llm.js          # LLM components
└── templates/
    └── dashboard.html          # Alternative: Jinja2 templates
```

### 4.2 Alternative: Minimal-Approach (MVP)

Falls schnelle Iteration gewünscht, erst mal:

```
kb/dashboard/
├── server.py                   # FastAPI + alles drin
├── static/
│   ├── index.html
│   └── dashboard.js
└── api/
    └── (in server.py integriert)
```

---

## 5. Empfohlene Anbindungs-Strategie

### 5.1 Architektur

```
┌─────────────────────────────────────────────────────────┐
│                    Browser (HTML/JS)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Search UI  │  │   Sync UI    │  │   LLM UI     │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                 │                 │           │
│         └─────────────────┼─────────────────┘           │
│                           │                             │
│                    api-client.js                        │
│                    (fetch + ws)                         │
└───────────────────────────┼─────────────────────────────┘
                            │ HTTP / WebSocket
┌───────────────────────────┼─────────────────────────────┐
│                    FastAPI Server                        │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  /api/search  /api/sync  /api/llm/*  /ws/sync      │ │
│  └─────────────────────────────────────────────────────┘ │
│                           │                             │
│         ┌─────────────────┼─────────────────┐          │
│         │                 │                 │          │
│   kb.base.db        kb.library       kb.commands       │
│  (SQLite direct)   (ChromaDB)       (CLI wrapper)       │
└─────────────────────────────────────────────────────────┘
```

### 5.2 Anbindungs-Matrix

| Dashboard-Feature | Anbindung | Begründung |
|---|---|---|
| **Suche** | Python API (`HybridSearch`) | Besser als CLI-Parsen, direkter Return |
| **Sync Status** | Python API + WebSocket | Echtzeit-Progress nötig |
| **Audit** | Python API + WebSocket | Echtzeit-Progress |
| **Ghost-Scan** | Python API + WebSocket | Echtzeit-Progress |
| **LLM Status** | Python API | Read-only, polling ok |
| **LLM Generate** | Python API + WebSocket | Langlaufend, braucht Progress |
| **LLM Watch/Scheduler** | Python API + WebSocket | Echtzeit-Status |
| **Config anzeigen** | Python API | `KBConfig.get_instance()` |
| **Config ändern** | Python API + Datei | Config-Datei schreiben |
| **Backup** | CLI (`kb backup`) | Bereits stabil, stdout parsen |
| **Essenzen/Reports** | Direkter FS-Zugriff | Dateien in `kb/library/` |
| **Stats (DB/Chroma)** | SQL + ChromaDB API | Direkte Queries |

### 5.3 WebSocket-Protokoll (Vorschlag)

```javascript
// Client → Server
{ "action": "start_sync", "params": { "delta": true } }
{ "action": "start_audit", "params": {} }
{ "action": "subscribe", "topics": ["sync", "llm_watcher"] }

// Server → Client
{ "type": "progress", "action": "sync", "percent": 45, "message": "Indexing files..." }
{ "type": "progress", "action": "sync", "percent": 100, "message": "Done", "result": {...} }
{ "type": "error", "action": "sync", "message": "ChromaDB unavailable" }
{ "type": "status", "topic": "llm_watcher", "data": { "running": true, "files_watched": 12 } }
```

---

## 6. Tech-Stack Empfehlung (Zusammenfassung)

| Layer | Technologie | Version |
|---|---|---|
| **Backend** | FastAPI | 0.109+ |
| **Server** | Uvicorn | (mit FastAPI gebündelt) |
| **Python** | 3.10+ | (bereits verwendet) |
| **Frontend** | Plain HTML5 + Vanilla JS | – |
| **CSS** | Pico.css (CDN) oder Tailwind CDN | – |
| **Real-time** | FastAPI WebSockets | – |
| **Pydantic** | Für API-Response-Models | – |

**Warum nicht React/Vue:**
- Dashboard ist relativ statisch
- Kein komplexes State-Management nötig
- Schnellere Entwicklung ohne Build
- Leichter zu integrieren

---

## 7. Nächste Schritte (Implementierung)

1. **MVP erstellen** (`kb/dashboard/server.py`)
   - FastAPI mit `/api/search` und `/api/stats`
   - Minimal HTML mit Suchfeld

2. **WebSocket für Sync**
   - `/ws/sync` Endpoint
   - Progress-Updates

3. **LLM-Section**
   - `/api/llm/status`
   - `/api/llm/generate` mit WebSocket

4. **Vollständiges UI**
   - Tab-Navigation (Suche, Sync, Audit, LLM, Stats)
   - Responsive Design

---

## Anhang: CLI-Command-Metadaten

| Command | Kategorie | Echtzeit | Importierbar |
|---|---|---|---|
| `sync` | data | ⚡ Ja | ✅ |
| `audit` | data | ⚡ Ja | ✅ |
| `ghost` | data | ⚡ Ja | ✅ |
| `search` | query | ⚡ Ja | ✅ |
| `warmup` | system | 🐢 Nein | ✅ |
| `llm` | llm | ⚡ Ja | ✅ |
| `engine-list` | llm | 🐢 Nein | ✅ |
| `engine-info` | llm | 🐢 Nein | ✅ |
| `backup` | system | ⚡ Ja | ✅ |
