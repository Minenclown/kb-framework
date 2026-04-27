# Phase 6: Versteckte Hardcoded Pfade — Review

**Datum:** 2026-04-26  
**Prüfer:** Sir Stern 🔍  
**Ziel:** Alle hardcoded Pfade finden, die Standalone-Nutzung verhindern

---

## Zusammenfassung

`kb/framework/paths.py` ist **NICHT** der einzige Ort mit `~/.openclaw`-Referenzen. Es gibt **21 Fundstellen** in 8 Dateien außerhalb von `paths.py`, die hardcoded Pfade enthalten. Zusätzlich gibt es **inkonsistente Fallback-Pfade** (`.knowledge` vs `.openclaw`), ein **veraltetes Legacy-Config-Modul** (`kb/config.py`), und **hardcoded Pfade in Tests**.

---

## 1. Hardcoded Pfade außerhalb von `paths.py`

### ❌ `kb/__main__.py:47` — `Path.home() / ".openclaw" / "kb"`
- **Was ist falsch:** Hardcoded `.openclaw/kb` im CLI-Entrypoint, bevor KBConfig initialisiert wird. Setzt auch `os.environ.setdefault`.
- **Empfohlener Fix:** `from kb.framework.paths import get_default_library_path; KB_BASE_PATH = os.getenv("KB_BASE_PATH", str(get_default_library_path().parent))` — oder `KBConfig.get_instance().base_path` nutzen.

### ❌ `kb/base/config.py:50` — `DEFAULT_BASE = Path.home() / ".openclaw" / "kb"`
- **Was ist falsch:** Der Klassen-Default ist hardcoded, obwohl `paths.py` bereits existiert.
- **Empfohlener Fix:** `from kb.framework.paths import get_default_base_path; DEFAULT_BASE = get_default_base_path()` — oder `paths.py` als *einzige* Quelle nutzen und `DEFAULT_BASE` aus `paths.py` importieren.

### ❌ `kb/base/config.py:184` — `Path.home() / ".openclaw" / "kb" / "library"`
- **Was ist falsch:** `library_path` Property hat hardcoded Fallback, obwohl `paths.py::get_default_library_path()` existiert.
- **Empfohlener Fix:** `return self._base_path / "library"` (relative Ableitung vom `base_path`), was bereits korrekt für `db_path` und `chroma_path` gemacht wird.

### ❌ `kb/base/config.py:201` — `Path.home() / ".openclaw" / "workspace"`
- **Was ist falsch:** `workspace_path` hat hardcoded Fallback statt `paths.py` zu nutzen.
- **Empfohlener Fix:** `from kb.framework.paths import get_default_workspace_path` als Fallback nutzen, oder `self._base_path.parent / "workspace"`.

### ❌ `kb/base/config.py:208` — `Path.home() / ".knowledge" / "ghost_cache.json"`
- **Was ist falsch:** `ghost_cache_path` nutzt `.knowledge` statt `.openclaw` — **inkonsistenter Pfad**! Und hardcoded statt via `paths.py`.
- **Empfohlener Fix:** Konsistent machen: `self._base_path / "ghost_cache.json"` oder via `paths.py`.

### ❌ `kb/base/config.py:215` — `Path.home() / ".knowledge" / "backup"`
- **Was ist falsch:** `backup_dir` nutzt auch `.knowledge` statt `.openclaw` — **inkonsistenter Pfad**! Und hardcoded.
- **Empfohlener Fix:** Konsistent machen: `self._base_path / "backup"` oder via `paths.py`.

### ❌ `kb/scripts/kb_ghost_scanner.py:31-35` — 4 hardcoded Pfade
- **Zeile 31:** `DB_PATH = Path.home() / ".openclaw" / "kb" / "library" / "biblio.db"` — im `except ImportError` Fallback
- **Zeile 32:** `LIBRARY_PATH = Path.home() / "knowledge" / "library"` — **inkonsistenter Pfad** (`knowledge` statt `.openclaw/kb/library`)
- **Zeile 33:** `OUTPUT_DIR = Path.home() / "knowledge" / "library" / "audit"` — dito
- **Zeile 34:** `CACHE_FILE = Path.home() / ".knowledge" / "ghost_cache.json"` — `.knowledge`!
- **Zeile 35:** `_WORKSPACE = Path.home() / ".openclaw" / "workspace"` — im Fallback
- **Was ist falsch:** Mehrere inkonsistente Fallback-Pfade (`.openclaw` vs `knowledge` vs `.knowledge`). Die `try/except ImportError` Struktur ist gut, aber die Fallbacks sind falsch/inkonsistent.
- **Empfohlener Fix:** Fallbacks konsistent mit `paths.py` machen, oder `paths.py` direkt importieren (ohne try/except, da `paths.py` keine externen Dependencies hat).

### ❌ `kb/scripts/kb_warmup.py:11` — `sys.path.insert(0, str(Path.home() / ".openclaw" / "kb"))`
- **Was ist falsch:** Hardcoded `.openclaw/kb` für `sys.path`-Manipulation. Das funktioniert nicht in einer Standalone-Installation (z.B. pip-installiert).
- **Empfohlener Fix:** `sys.path.insert(0, str(Path(__file__).resolve().parent.parent))` — relativer Pfad zum eigenen Package.

### ❌ `kb/scripts/index_pdfs.py:741` — `Path.home() / ".openclaw" / "kb" / "library" / "biblio.db"`
- **Was ist falsch:** Hardcoded Fallback im `except Exception:`-Block.
- **Empfohlener Fix:** `from kb.framework.paths import get_default_db_path` nutzen.

### ❌ `kb/scripts/index_pdfs.py:337` — `Path.home() / "knowledge" / "kb" / "framework"`
- **Was ist falsch:** Hardcoded `knowledge/kb/framework` — völlig anderer Pfad als `.openclaw/kb/framework`!
- **Empfohlener Fix:** `from kb.framework.paths import get_default_library_path` und korrekt ableiten.

### ❌ `kb/scripts/kb_full_audit.py:26-27` — 2 hardcoded Pfade im `except ImportError` Block
- **Zeile 26:** `LIBRARY_PATH = Path.home() / "knowledge" / "library"` — **inkonsistenter Pfad**
- **Zeile 27:** `OUTPUT_DIR = Path.home() / "knowledge" / "library" / "audit"` — dito
- **Was ist falsch:** `knowledge` statt `.openclaw/kb/library`.
- **Empfohlener Fix:** Konsistente Fallbacks via `paths.py`.

### ❌ `kb/update.py:29` — `BACKUP_DIR = Path.home() / ".knowledge" / "backup"`
- **Was ist falsch:** Nutzt `.knowledge` statt `.openclaw/kb/backup`.
- **Empfohlener Fix:** `from kb.framework.paths import get_default_workspace_path` oder `from kb.base.config import KBConfig`.

### ❌ `kb/update.py:92,220` — `Path.home() / ".knowledge" / "knowledge.db"`
- **Was ist falsch:** 2× hardcoded `.knowledge/knowledge.db` — die DB heißt `biblio.db` und liegt in `.openclaw/kb/library/`.
- **Empfohlener Fix:** `KBConfig.get_instance().db_path` nutzen.

### ❌ `kb/commands/ghost.py:160` — `Path.home() / "knowledge" / "library" / "Gesundheit"`
- **Was ist falsch:** Hardcoded `knowledge/library/Gesundheit` als Scan-Verzeichnis. Sollte aus Config kommen.
- **Empfohlener Fix:** `config.library_path / "Gesundheit"` oder konfigurierbare Scan-Dirs via Config/Env.

### ❌ `kb/framework/providers/fts5_provider.py:14` — `Path("~/.openclaw/kb/library/biblio.db")`
- **Was ist falsch:** Docstring-Beispiel zeigt hardcoded Pfad. Das ist kein Code-Fehler, aber verwirrend als "offizielle" Usage-Doku.
- **Empfohlener Fix:** `Path("biblio.db")` oder `get_default_db_path()` im Beispiel zeigen.

### ❌ `kb/framework/embedding_pipeline.py:527` — `"library/biblio.db"`
- **Was ist falsch:** Default-Wert für `--db-path` CLI-Argument ist ein **relativer Pfad ohne Bezug zum Base-Verzeichnis**. Wird im aktuellen Arbeitsverzeichnis aufgelöst, nicht relativ zu KB-Base.
- **Empfohlener Fix:** `default=str(get_default_db_path())` oder zumindest `os.path.join(os.getenv("KB_BASE_PATH", str(Path.home() / ".openclaw" / "kb")), "library", "biblio.db")`.

### ❌ `kb/biblio/generator/test_parallel.py:541-544,619-622` — `os.path.expanduser("~/projects/kb-framework/...")`
- **Was ist falsch:** 8 hardcoded Pfade zum Projektverzeichnis in Tests. Nicht standalone-fähig.
- **Empfohlener Fix:** `Path(__file__).resolve().parent / "parallel_mixin.py"` etc. nutzen, oder Tests relativ zum Package-Wurzelverzeichnis aufbauen.

---

## 2. Legacy-Config-Modul `kb/config.py`

### ❌ `kb/config.py:10` — `DB_PATH = "library/biblio.db"`
- **Was ist falsch:** Relativer Pfad ohne Bezug zur KB-Base. Wird von 3 Skripten importiert:
  - `kb/scripts/migrate_fts5.py:22`
  - `kb/scripts/kb_full_audit.py:17`
  - `kb/scripts/migrate.py:10`
- **Empfohlener Fix:** Diese Skripte auf `KBConfig.get_instance().db_path` migrieren und `kb/config.py` entfernen.

### ❌ `kb/framework/fts5_setup.py:233` — `from config import DB_PATH`
- **Was ist falsch:** Nutzt Legacy-Modul statt `kb.framework.paths` oder `KBConfig`.
- **Empfohlener Fix:** `from kb.framework.paths import get_default_db_path` nutzen.

---

## 3. Direkte `os.environ.get("KB_...")` ohne `paths.py`

Alle Properties in `kb/base/config.py` (Zeilen 176-215) prüfen selbstständig `os.getenv()` statt `paths.py` zu nutzen. Das ist nicht direkt falsch (Config hat Vorrang), aber die Fallback-Logik ist **dupliziert** zwischen `config.py` und `paths.py`:

| Pfad | `config.py` Fallback | `paths.py` Fallback |
|------|----------------------|---------------------|
| `library_path` | `Path.home() / ".openclaw" / "kb" / "library"` | `KBConfig.library_path` → `Path.home() / ".openclaw" / "kb" / "library"` |
| `workspace_path` | `Path.home() / ".openclaw" / "workspace"` | `KBConfig.workspace_path` → `Path.home() / ".openclaw" / "workspace"` |
| `ghost_cache_path` | `Path.home() / ".knowledge" / "ghost_cache.json"` | `KBConfig.ghost_cache_path` → `Path.home() / ".knowledge" / "ghost_cache.json"` |

**Empfehlung:** `paths.py` als alleinige Fallback-Quelle etablieren und `config.py` dorthin delegieren.

---

## 4. Fallback-Logik Analyse

### Was passiert, wenn `paths.py` keinen Pfad finden kann?

`paths.py` importiert `KBConfig` im `try`-Block:
```python
def get_default_db_path() -> Path:
    try:
        from kb.base.config import KBConfig
        return KBConfig.get_instance().db_path
    except Exception:
        return Path.home() / ".openclaw" / "kb" / "library" / "biblio.db"
```

**Probleme:**
1. **Zirkuläre Abhängigkeit möglich:** `paths.py` → `KBConfig` → `DEFAULT_BASE = Path.home() / ".openclaw" / "kb"` → wieder hardcoded
2. **Fallback ist hardcoded `.openclaw`:** Kein Standalone-Betrieb möglich, wenn `KBConfig` nicht initialisiert werden kann
3. **Kein Env-Variable-Fallback im `paths.py`:** Wenn `KBConfig` fehlschlägt, wird `KB_BASE_PATH` Env-Variable **nicht** geprüft

### Ist der Fallback standalone-fähig?

**Nein.** Alle Fallbacks in `paths.py` zeigen auf `Path.home() / ".openclaw" / ...`. Für Standalone-Betrieb bräuchte man:
- Erkennung der Package-Installation (z.B. via `__file__`-basierte Pfade)
- Oder `XDG_CONFIG_HOME` / `XDG_DATA_HOME` Konvention
- Oder konsistente Env-Variable-Fallbacks

---

## 5. Inkonsistente Pfad-Hierarchien

Es gibt **3 verschiedene Pfad-Schemata**, was extrem verwirrend ist:

| Schema | Pfad | Nutzungsorte |
|--------|------|-------------|
| `.openclaw/kb/...` | `~/.openclaw/kb/library/biblio.db` | `paths.py`, `config.py:50,184,201`, `__main__.py`, `kb_ghost_scanner.py`, `index_pdfs.py`, `kb_warmup.py` |
| `knowledge/...` | `~/knowledge/library/...` | `ghost.py:160`, `kb_ghost_scanner.py:32-33`, `index_pdfs.py:337`, `kb_full_audit.py:26-27` |
| `.knowledge/...` | `~/.knowledge/backup`, `~/.knowledge/ghost_cache.json`, `~/.knowledge/knowledge.db` | `config.py:208,215`, `update.py:29,92,220`, `kb_ghost_scanner.py:34` |

**Kritisch:** Die gleichen Konzepte (z.B. Ghost-Cache) werden in verschiedenen Dateien mit **unterschiedlichen Pfaden** referenziert. In einer Standalone-Installation würden diese Pfade auseinanderlaufen.

---

## 6. Prioritätsempfehlung

### 🔴 Kritisch (Standalone-Verhindernd)

1. **`kb/base/config.py` — Alle `Path.home()` Fallbacks** — Zentrale Config ist die wichtigste Stelle. `DEFAULT_BASE`, `library_path`, `workspace_path`, `ghost_cache_path`, `backup_dir` müssen via `paths.py` oder Package-relative Pfade funktionieren.

2. **`kb/scripts/*.py` — 5 Dateien mit hardcoded Fallbacks** — Scripts sind oft Entry-Points für Cron/CLI und müssen Standalone-fähig sein.

3. **`kb/config.py` — Legacy-Modul** — `DB_PATH = "library/biblio.db"` ist ein relativer Pfad, der je nach CWD unterschiedlich aufgelöst wird. Muss entfernt werden.

4. **`kb/__main__.py:47` — CLI-Entrypoint** — Setzt den Pfad bevor Config geladen wird.

### 🟡 Mittel (Inkonsistent aber nicht Blockierend)

5. **Inkonsistente Pfad-Schemata** — `.openclaw` vs `knowledge` vs `.knowledge` vereinheitlichen.

6. **`kb/framework/embedding_pipeline.py:527`** — CLI-Default ist CWD-relativ.

7. **`kb/commands/ghost.py:160`** — Hardcoded Scan-Dir.

### 🟢 Niedrig (Docs/Tests)

8. **`kb/framework/providers/fts5_provider.py:14`** — Docstring-Beispiel.

9. **`kb/biblio/generator/test_parallel.py`** — Test-Dateien mit hardcoded Pfaden.

---

## 7. Empfohlene Gesamt-Lösung

### Schritt 1: `paths.py` zur alleinigen Pfad-Quelle machen

```python
# kb/framework/paths.py — erweitern
def get_default_base_path() -> Path:
    """Resolve default KB base path."""
    env = os.getenv("KB_BASE_PATH")
    if env:
        return Path(env).resolve()
    # Package-relative fallback for standalone installations
    package_root = Path(__file__).resolve().parent.parent  # kb/
    if (package_root / "library").exists():
        return package_root
    # OpenClaw-managed installation
    return Path.home() / ".openclaw" / "kb"
```

### Schritt 2: `kb/base/config.py` delegiert an `paths.py`

```python
# Statt:
DEFAULT_BASE = Path.home() / ".openclaw" / "kb"
# →
from kb.framework.paths import get_default_base_path
DEFAULT_BASE = get_default_base_path()
```

### Schritt 3: Alle Scripts auf `paths.py` oder `KBConfig` umstellen

```python
# Statt:
except ImportError:
    DB_PATH = Path.home() / ".openclaw" / "kb" / "library" / "biblio.db"
# →
from kb.framework.paths import get_default_db_path
DB_PATH = get_default_db_path()
```

### Schritt 4: Pfad-Schemata vereinheitlichen

Entscheidung treffen: **Ein** Schema. Empfehlung: `.openclaw/kb/` (wie es `paths.py` bereits definiert), und alle `.knowledge`/`knowledge` Referenzen umstellen.

### Schritt 5: `kb/config.py` entfernen

Legacy-Modul durch `KBConfig` ersetzen, alle 3 Importe migrieren.

---

**Ergebnis:** 21 Fundstellen in 8 Dateien + 1 Legacy-Modul. Die Standalone-Fähigkeit ist aktuell **nicht gegeben** — es gibt 3 inkonsistente Pfad-Schemata und keine Package-relative Pfad-Erkennung.