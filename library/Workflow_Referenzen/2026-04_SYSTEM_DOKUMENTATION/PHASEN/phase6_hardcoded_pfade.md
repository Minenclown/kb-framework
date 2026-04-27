# Phase 6: Hardcoded Pfade Fixen

## Metadaten
- **Review-Datum:** 2026-04-27
- **Agent:** Softaware (Folge-Agent)
- **Status:** 📋 Zu erledigen

---

## Ausgangslage

| Metrik | Wert |
|--------|------|
| Fundstellen gesamt | 21 |
| Betroffene Dateien | 8 |
| Haupt-Problem-Datei | `kb/base/config.py` |

---

## Priorisierung

### P1 - Kritisch (sofort fixen)
| Datei | Pfade | Grund |
|-------|-------|-------|
| `kb/base/config.py` | ~12 | Zentrale Konfiguration, alle anderen referenzieren diese |
| `kb/scripts/*.py` | ~6 | CLI-Scripts |

### P2 - Mittel (diese Woche)
| Datei | Pfade | Grund |
|-------|-------|-------|
| `kb/embeddings/*.py` | ~2 | Integrationen |
| `kb/storage/*.py` | ~1 | Storage-Handler |

---

## Schritt-für-Schritt Anleitung

### Schritt 1: config.py analysieren (30 min)
```bash
# Fundstellen in config.py finden
grep -n "os.path" kb/base/config.py
grep -n '".*/' kb/base/config.py
```

### Schritt 2: Durch Pathlib ersetzen (45 min)
```python
# VORHER (problematisch):
path = "/home/user/projects/kb/data"

# NACHHER (portabel):
from pathlib import Path
path = Path(__file__).parent.parent / "data"  # relativ zum Projekt
# Oder wenn absolut nötig:
path = Path.home() / ".config" / "kb" / "data"
```

### Schritt 3: In Scripts ersetzen (30 min)
```bash
# Alle Scripts durchgehen
grep -rn '".*/kb/' kb/scripts/
```

### Schritt 4: Testen (15 min)
```bash
# Sicherstellen dass alles noch läuft
cd /home/lumen/.openclaw/kb
python -c "from kb.base.config import settings; print(settings)"
```

---

## Erwartetes Ergebnis

| Vorher | Nachher |
|--------|---------|
| 21 hardcoded Pfade | 0 hardcoded Pfade |
| Nur auf spezifischen Host lauffähig | Lauffähig auf jedem System |
| Risiko: Pfad-Änderungen brechen alles | Pfad-Änderungen via config.py |

---

## Konkrete Ersetzungs-Muster

### Pattern 1: Projekt-Root
```python
# Statt:
"/home/lumen/.openclaw/kb/library"

# Nutze:
ROOT = Path(__file__).parent.parent.parent  # kb/ → project root
LIBRARY = ROOT / "library"
```

### Pattern 2: User-Home
```python
# Statt:
"/home/lumen/.config/kb"

# Nutze:
from pathlib import Path
CONFIG_DIR = Path.home() / ".config" / "kb"
```

### Pattern 3: Temp
```python
# Statt:
"/tmp/kb_cache"

# Nutze:
import tempfile
CACHE_DIR = Path(tempfile.gettempdir()) / "kb_cache"
```

---

## Risiken & Fallbacks

| Risiko | Mitigation |
|--------|------------|
| Pfad-Änderung bricht Integrationen | Erst alle referenzen finden, dann bulk-ersetzen |
| Falsche ROOT-Annahme | Test mit `python -c "from kb.base.config import ROOT; print(ROOT)"` |

---

## Checkliste für Softaware

- [ ] `kb/base/config.py` komplett durch Pathlib ersetzt
- [ ] Alle `kb/scripts/*.py` geprüft
- [ ] `kb/embeddings/*.py` geprüft
- [ ] `kb/storage/*.py` geprüft
- [ ] Smoke-Test bestanden
- [ ] Keine neuen hardcoded Pfade eingeführt
