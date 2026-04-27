# Workflow Template - System Review

## Metadaten
- **Projekt:** {PROJEKT_NAME}
- **Datum:** {DATUM}
- **Agent:** Specialista
- **Status:** 🟡 In Arbeit

---

## Phase 1: Kontext & Ziele
**Ziel:** Verstehen was das System macht und warum

### Checkliste
- [ ] README lesen
- [ ] Haupt-Module identifizieren
- [ ] Einstiegspunkte finden (CLI, API, Scripts)
- [ ] "Warum existiert das?" beantworten

### Output
- 3-5 Bullet Points: Was macht das System?
- Liste der Haupt-Module
- Bewertung: Wie viel fehlt? (%)

---

## Phase 2: Funktionen
**Ziel:** Alle implementierten Funktionen dokumentieren

### Checkliste
- [ ] Alle Python-Dateien scannen
- [ ] Öffentliche Funktionen/Methoden identifizieren
- [ ] CLI-Kommandos dokumentieren
- [ ] API-Endpunkte finden (falls vorhanden)

### Output
| # | Funktion | Status | Datei |
|---|----------|--------|-------|

---

## Phase 3: Architektur
**Ziel:** Code-Qualität und Struktur bewerten

### Kriterien
- ✅ Gut | 🟡 Mittel | ❌ Kritisch

### Output
| Bereich | Bewertung | Begründung |
|---------|-----------|------------|
| Modulstruktur | | |
| Klassen-Design | | |
| Funktionslänge | | |
| Wiederverwendbarkeit | | |
| Komplexität | | |

---

## Phase 4: Verbindungen (Dependencies)
**Ziel:** Interne und externe Abhängigkeiten analysieren

### Output
| Typ | Name | Status | Begründung |
|-----|------|--------|------------|
| Intern | | | |
| Extern | | | |

---

## Phase 5: Optimierungen
**Ziel:** Schnelle Wins identifizieren

### Kategorien
- 🔴 Sofort umsetzbar (< 1h)
- 🟡 Mittelfristig (1-4h)
- 🔵 Langfristig (> 4h)

### Output
| # | Task | Aufwand | Impact |
|---|------|---------|--------|

---

## Phase 6: Hardcoded Pfade
**Ziel:** Nicht-portable Pfade finden

### Output
| Datei | Zeile | Pfad | Kritikalität |
|-------|-------|------|--------------|

---

## Phase 7: Performance
**Ziel:** Bottlenecks und N+1-Probleme finden

### Output
| Datei | Zeile | Problem | Schwere |
|-------|-------|---------|---------|

---

## Phase 8: Sicherheit
**Ziel:** Risiken identifizieren

### Output
| Datei | Zeile | Risiko | Level |
|-------|-------|--------|-------|

---

## Phase 9: Tests
**Ziel:** Testabdeckung und Qualität prüfen

### Output
- Gesamt-Tests: X
- Failed: X
- Coverage: X%
- Fehlende Tests: Liste

---

## Phase 10: Dokumentation
**Ziel:** Doku-Qualität und Aktualität prüfen

### Output
- Aktualität: 🟢/🟡/🔴
- Fehlende Abschnitte: Liste
- Veraltete Informationen: Liste

---

## Zusammenfassung

### Top 5 Probleme
| Rang | Problem | Fund | Phase |
|------|---------|------|-------|

### Sofort umsetzbar
| # | Task | Aufwand |
|---|------|---------|

### Nächste Schritte
1. ...
2. ...
3. ...
