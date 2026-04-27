# Phase 9+10: Dokumentation Aktualisieren

## Metadaten
- **Review-Datum:** 2026-04-27
- **Agent:** Softaware (Folge-Agent)
- **Status:** 📋 Zu erledigen

---

## Ausgangslage

| Metrik | Wert |
|--------|------|
| Doku-Aktualität | 🔴 Veraltet |
| Haupt-Problem | SKILL.md zeigt nicht-existierende Pfade |
| Fehlende Sektionen | Workflows, API-Referenz, Konfiguration |

---

## Was muss aktualisiert werden

### 1. SKILL.md (KRITISCH)
**Problem:** Existierende Pfade werden nicht gefunden

| Ding | Sollte sein | Ist |
|------|-------------|-----|
| Pfad zur KB | `~/.openclaw/kb/` | Dokumentiert als `/opt/kb/` |
| Scripts | `kb/scripts/` | Dokumentiert als `bin/` |
| Config | `kb/base/config.py` | Dokumentiert als `config/kb.py` |

### 2. README.md (mittel)
- Letztes Update Datum prüfen
- Features aktualisieren die neu sind
- Installation-Anleitung prüfen

### 3. ARCHITECTURE.md (falls vorhanden)
- Architektur-Diagramme aktualisieren
- Neue Module eintragen

### 4. API-Doku (falls vorhanden)
- Endpunkte die in Phase 2 gefunden wurden

---

## Schritt-für-Schritt Plan

### Schritt 1: Bestandsaufnahme (20 min)
```bash
# Was existiert wirklich?
find ~/.openclaw/kb -type f -name "*.md" | head -20
find ~/.openclaw/kb -type d | head -20

# Was ist dokumentiert?
cat ~/.openclaw/kb/SKILL.md
```

### Schritt 2: SKILL.md rebuild (45 min)
```markdown
# KB Framework SKILL.md

## Überblick
[Beschreibung des Systems - aus Phase 1]

## Pfade
- KB Root: `~/.openclaw/kb/`
- Config: `~/.openclaw/kb/kb/base/config.py`
- Scripts: `~/.openclaw/kb/kb/scripts/`
- Library: `~/.openclaw/kb/library/`

## Commands
[Alle CLI-Commands aus Phase 2]

## Konfiguration
[Aus config.py]

## Troubleshooting
[Common Issues]
```

### Schritt 3: README.md prüfen (15 min)
- Aktualität-Check (Datum + Content)
- Fehlende Features nachtragen
- TODOs entfernen die erledigt sind

### Schritt 4: Konfiguration-Doku (30 min)
- `config.py` dokumentieren
- Alle Settings mit Default-Werten
- Environment-Variablen auflisten

---

## Fehlerhafte Pfade identifiziert

| Dokumentiert | Existiert | Korrektur |
|--------------|-----------|-----------|
| `/opt/kb/` | `~/.openclaw/kb/` | Pfad ersetzen |
| `bin/` | `kb/scripts/` | Pfad ersetzen |
| `config/kb.py` | `kb/base/config.py` | Pfad ersetzen |
| `docs/API.md` | existiert nicht | Entfernen oder erstellen |

---

## Checkliste für Softaware

- [ ] SKILL.md komplett neu geschrieben mit korrekten Pfaden
- [ ] README.md Datum + Content aktualisiert
- [ ] Konfiguration in config.py dokumentiert
- [ ] Alle dokumentierten Pfade verifiziert (existieren wirklich)
- [ ] CLI-Commands dokumentiert
- [ ] Troubleshooting-Sektion hinzugefügt

---

## Tool-Tipp

```bash
# Validate alle dokumentierten Pfade
cd ~/.openclaw/kb
# Für jeden Pfad in Doku:
ls -la <dokumentierter_pfad>  # sollte existieren
```

## Risiken

| Risiko | Mitigation |
|--------|------------|
| Doku wieder veraltet | Regelmäßige Reviews einplanen (Quartal) |
| Neue Pfade nicht dokumentiert | PR-Requirement: Doku-Update bei Pfad-Änderungen |
