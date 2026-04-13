# KB Framework - Fix Plan & Roadmap

**Version:** 1.0  
**Erstellt:** 2026-04-13  
**Status:** Aktiv

---

## 🔥 Kritisch (Sofort)

| # | Feature | Problem | Lösung | Aufwand |
|---|---------|---------|--------|---------|
| 1 | **Multi-Format Indexierung** | PDFs, TXTs, DOCs werden ignoriert – nur .md ist searchable | Auto-Konvertierung: Nicht-MD → MD-Kopie mit Metadaten-Header | ~4h |
| 2 | Hybrid Search Modul | `kb.library.knowledge_base.hybrid_search` fehlt im aktuellen Stand | Modul aus Phase 3 Recovery reintegrieren | ~2h |

### 🔥 Multi-Format Indexierung (Detail)

**Anforderung:**
- PDFs, TXT, DOCX → Automatisch als `.md` Kopie in `library/content/[kategorie]/`
- Header mit Metadaten:
  ```markdown
  ---
  source: original.pdf
  type: pdf
  indexed_at: 2026-04-13
  extracted_by: [pymupdf/easyocr]
  ---
  
  [Extrahierter Text...]
  ```

**Vorteile:**
- Agenten können PDF-Inhalte direkt lesen (natives MD)
- Volltext-Suche über alle Formate
- Keine Duplikate (Hash-Check)

---

## 🟡 Hoch (Nächste Woche)

| # | Feature | Problem | Lösung | Aufwand |
|---|---------|---------|--------|---------|
| 3 | OCR GPU Support | EasyOCR ist langsam (~30s/PDF) | GPU-Flag in config.py, Tesseract-Alternative | ~1h |
| 4 | ChromaDB Warmup Script | Cold-Start 3.2s beim ersten Embedding | Automatisches Modell-Preloading bei Boot | ~30min |
| 5 | Delta-Indexierung | Re-Indexierung von allen Files bei Änderung | Timestamp-Check: nur geänderte Files | ~2h |

---

## 🟢 Mittel (Sprint)

| # | Feature | Problem | Lösung | Aufwand |
|---|---------|---------|--------|---------|
| 6 | Backup/Restore CLI | `kb backup` und `kb restore` fehlen | Wrapper für DB + ChromaDB Export/Import | ~2h |
| 7 | Test-Abdeckung | 5/8 Tests failed bei Review | Tests an aktuelles Schema anpassen | ~3h |
| 8 | Auto-Updater Testen | `kb update` nie live getestet | Test-Release auf GitHub erstellen | ~1h |

---

## 🔵 Niedrig (Backlog)

| # | Feature | Problem | Lösung | Aufwand |
|---|---------|---------|--------|---------|
| 9 | Web-Interface | Nur CLI verfügbar | Minimales Web-UI für Suche/Status | ~8h |
| 10 | Plugin-System | Keine Erweiterbarkeit | Hook-System für Custom Indexer | ~4h |
| 11 | Mehrsprachigkeit | Nur Deutsch/Englisch | i18n für alle Output-Strings | ~3h |

---

## 🚧 In Arbeit

| # | Feature | Status | Verantwortlich |
|---|---------|--------|----------------|
| - | - | - | - |

---

## ✅ Erledigt (Letzte 7 Tage)

| # | Feature | Datum | Notizen |
|---|---------|-------|---------|
| 1 | KB Migration | 2026-04-13 | Legacy → Neue Struktur, 868 Files migriert |
| 2 | Auto-Updater Fix | 2026-04-13 | Repo auf `Minenclown/kb-framework` korrigiert |
| 3 | README Update | 2026-04-13 | Installationspfad, Struktur, Quick Start (CLI) |
| 4 | FK Constraints | 2026-04-13 | 181 orphaned records gelöscht, PRAGMA foreign_keys = ON |

---

## Priorisierungs-Logik

```
🔥 Kritisch = Blockiert Produktivnutzung
🟡 Hoch = Wichtig für UX/Performance
🟢 Mittel = Nice-to-have, stabilisiert
🔵 Niedrig = Visionär/Zukunft
```

**Entscheidungskriterien:**
- Impact auf User × Aufwand = Priorität
- Blocker vor Optimierungen
- Stabilität vor Features

---

## Nächster Schritt

**Empfohlen:** 🔥 #1 Multi-Format Indexierung

**Begründung:**
- Aktuell werden 258 PDFs im Gesundheitsbereich ignoriert
- Agenten können wichtige medizinische Daten nicht lesen
- Hoher Impact, mittlerer Aufwand

**Implementation:**
```python
# pseudo-code
class MultiFormatIndexer:
    SUPPORTED = ['.pdf', '.txt', '.docx']
    
    def index_file(self, path):
        if path.suffix == '.md':
            return self.index_markdown(path)
        elif path.suffix in self.SUPPORTED:
            md_copy = self.convert_to_md(path)
            return self.index_markdown(md_copy)
```

---

*Letzte Aktualisierung: 2026-04-13*  
*Nächste Review: 2026-04-20*
