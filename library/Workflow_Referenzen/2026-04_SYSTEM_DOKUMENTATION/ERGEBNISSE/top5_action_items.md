# Top 5 Action Items - KB Framework

## Priorisiert nach Impact / Aufwand

**Erstellt:** 2026-04-27  
**Agent:** Softaware (Ausführung)  
**Grundlage:** 10-Phasen-Review durch FuClaWork

---

## Rang 1: Hardcoded Pfade fixen

| Attribut | Wert |
|----------|------|
| **Impact** | 🔴 Hoch |
| **Aufwand** | 🟡 Mittel (2-3h) |
| **Dateien** | 8 |
| **Fundstellen** | 21 |

### Was
Alle `"/home/lumen/..."` Pfade durch `pathlib` + relative Pfade ersetzen.

### Wie
1. `kb/base/config.py` → zentrale Path-Konstanten mit `Path(__file__).parent`
2. Scripts in `kb/scripts/` → referenzieren config.py
3. Test mit Smoke-Test

### Warum P1
- Fundament für alles andere
- Andere Fixes scheitern sonst
- 21 Stellen, aber mechanisch zu fixen

---

## Rang 2: Dokumentation komplett neu schreiben

| Attribut | Wert |
|----------|------|
| **Impact** | 🔴 Hoch |
| **Aufwand** | 🟡 Mittel (2-3h) |
| **Haupt-Problem** | SKILL.md zeigt falsche Pfade |

### Was
`SKILL.md` komplett neu schreiben mit:
- Korrekten Pfaden (existierende verifizieren)
- Alle CLI-Commands (aus Phase 2)
- Konfiguration (aus config.py)
- Troubleshooting-Sektion

### Wie
1. Bestandsaufnahme: `find ~/.openclaw/kb -type f`
2. SKILL.md aus Vorlage neu schreiben
3. README.md Datum + Content prüfen
4. Jeden Pfad verifizieren

### Warum P2
- Dokumentation treibt Entwickler in den Wahnsinn
- Drittel der Features nicht auffindbar
- Muss vor anderem Work gemacht werden

---

## Rang 3: N+1 Queries fixen (keyword.py)

| Attribut | Wert |
|----------|------|
| **Impact** | 🔴 Hoch |
| **Aufwand** | 🟡 Mittel (1-2h) |
| **Betroffene Dateien** | `keyword.py`, `filters.py` |

### Was
Loop-über-DB-Queries durch Bulk-JOIN-Queries ersetzen.

### Wie
```python
# Vorher: for item_id in item_ids: query(item_id)
# Nachher: query("SELECT ... WHERE item_id IN (...)", item_ids)
```

### Warum P3
- 18 Performance-Issues, davon 3 kritisch
- Skaliert nicht mit Datenmenge
- Einfacher als gedacht

---

## Rang 4: Exception-Handling spezifizieren

| Attribut | Wert |
|----------|------|
| **Impact** | 🟡 Mittel |
| **Aufwand** | 🟡 Mittel (2-3h) |
| **Fundstellen** | ~27 breite `except Exception` |

### Was
`except Exception as e:` ersetzen durch spezifische Exceptions.

### Wie
```python
# Vorher:
except Exception:
    pass

# Nachher:
except ConnectionError as e:
    logger.error(f"DB connection failed: {e}")
    raise
except ValueError as e:
    logger.warning(f"Invalid input: {e}")
    raise
```

### Warum P4
- Bugs werden still verschluckt
- Debugging ist fast unmöglich
- Wartbarkeit leidet

---

## Rang 5: Tests fixen (pytest-asyncio)

| Attribut | Wert |
|----------|------|
| **Impact** | 🟡 Mittel |
| **Aufwand** | 🟡 Mittel (1-2h) |
| **Failed Tests** | 6 |

### Was
1. `pytest-asyncio` installieren falls fehlend
2. 6 failed Tests analysieren
3. Fixtures für Async korrekt setzen

### Wie
```bash
# Prüfen was fehlt
pytest --collect-only 2>&1 | grep "asyncio"

# Fixture hinzufügen falls nötig
# conftest.py: pytest_plugins = ['pytest_asyncio']
```

### Warum P5
- CI/CD ist rot
- Refactoring riskant ohne Tests
- Fix ist mechanisch

---

## Zusammenfassung

| Rang | Task | Impact | Aufwand | Zeit |
|------|------|--------|---------|------|
| 1 | Hardcoded Pfade | 🔴 | 🟡 | 2-3h |
| 2 | Doku neu schreiben | 🔴 | 🟡 | 2-3h |
| 3 | N+1 Queries | 🔴 | 🟡 | 1-2h |
| 4 | Exception-Handling | 🟡 | 🟡 | 2-3h |
| 5 | Tests fixen | 🟡 | 🟡 | 1-2h |

**Gesamt: ~10-13 Stunden**  
**Critical Path:** 1 → 2 → 3 → 4 → 5

---

## Sofort umsetzbar (< 1h pro Item)

1. **ChromaIntegrationV2 entfernen** (FuClaWork identifiziert)
2. **config.py Pfade fixen** (Teil von Action Item 1)
3. **Redundante Funktionen zusammenführen** (katalogisiert von FuClaWork)
4. **README.md Datum aktualisieren** (trivial)

Diese 4 können parallel zu obiger Liste gemacht werden.
