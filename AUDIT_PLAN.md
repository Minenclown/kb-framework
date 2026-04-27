# AUDIT_PLAN.md — KB-Framework Deep-Code-Audit

**Projekt:** kb-framework  
**Audit-Typ:** Deep-Code-Qualitätsprüfung (Refactor-Fokus)  
**Dauer:** Phaseweise, jede Phase max. 5 Min.  
**Status:** 0/7 Phasen abgeschlossen  

---

## Kontext

Der KB-Framework Refactor (`src/library/` → `kb/framework/`) ist abgeschlossen.  
Sir Stern soll den Code jetzt auf Qualität, Redundanzen und Verbesserungspotenzial prüfen.

**Zu prüfende Dateien:**
```
kb/framework/
├── __init__.py          (164 L)
├── batching.py           (566 L)
├── chroma_integration.py (684 L)
├── chroma_plugin.py      (445 L)
├── chunker.py            (421 L)
├── embedding_pipeline.py (538 L)
├── fts5_setup.py         (274 L)
├── hybrid_search.py      (1095 L)
├── reranker.py           (281 L)
├── search_providers.py   (119 L)
├── stopwords.py          (289 L)
├── synonyms.py           (352 L)
├── utils.py              (47 L)
└── providers/
    ├── __init__.py       (45 L)
    ├── chroma_provider.py (160 L)
    └── fts5_provider.py  (286 L)
```

---

## Phase A — Code-Duplikate

**Ziel:** Doppelte Funktionalität identifizieren und konsolidieren.

**Zu prüfen:**
1. `_get_default_chroma_path()` — duplicate in `chroma_integration.py` + `chroma_plugin.py`?
2. `ChromaIntegration` vs `ChromaIntegrationV2` — Legacy-Code in `chroma_integration.py`?
3. `get_chroma()` vs `ChromaIntegration.get_instance()` — zwei Singleton-Zugänge?
4. `providers/chroma_provider.py` vs `chroma_integration.py` — overlapping logic?
5. `providers/fts5_provider.py` vs `fts5_setup.py` — duplicate FTS5 init logic?
6. `search_providers.py` vs `providers/` — existiert beides parallel?

**Deliverable:** Liste der Duplikate mit Vorschlag: merge / deprecate / keep separate.

---

## Phase B — Singleton/Factory-Muster

**Ziel:** Singleton-Pattern konsistent und sicher implementiert.

**Zu prüfen:**
1. `KBConfig.get_instance()` — thread-safe? Lazy-loading korrekt?
2. `ChromaIntegration.get_instance()` — korrekte Singleton-Enforcement?
3. `get_chroma()` — passt dieses Pattern zu `ChromaIntegration.get_instance()`?
4. Gibt es weitere `get_instance()`-Implementierungen?

**Deliverable:** Singleton-Status-Bericht mit Risikoeinschätzung (concurrency issues?).

---

## Phase C — Große Module

**Ziel:** Moduleidentifikation die zu groß / zu komplex sind.

**Zu prüfen:**
1. `hybrid_search.py` (1,095 L) — Aufteilung in Sub-Module sinnvoll? (z.B. `search/`, `ranking/`?)
2. `batching.py` (576 L) — Passt die Größe für eine Utility-Datei? Alternative: `pipeline/`, `workers/`
3. `embedding_pipeline.py` (538 L) — Trennung in `embedding/` Sub-package?
4. Allgemein: Kohäsion und Coupling der Module prüfen

**Deliverable:** Vorschlagsliste für Modularisierung mit Begründung.

---

## Phase D — Unnötige/Redundante Module

**Ziel:** Module die als separater Namespace kaum Wert bieten.

**Zu prüfen:**
1. `utils.py` (47 L) — Lohnt sich das Modul? Oder_inlined in die Konsumenten?
2. `stopwords.py` (289 L) — Statische Daten. Verschieben in Config/YAML?
3. `synonyms.py` (352 L) — Ähnlich zu `stopwords.py`. Gemeinsames Modul oder Config?
4. `chroma_plugin.py` (445 L) — Eigenständiges Plugin oder subset von `chroma_integration`?

**Deliverable:** Empfehlungen: inline / merge / keep / externalize.

---

## Phase E — API-Oberfläche

**Ziel:** Saubere, bewusste Public API statt Wildwuchs.

**Zu prüfen:**
1. `kb/framework/__init__.py` — wie viele Symbole werden exportiert? (Ziel: <50?)
2. Welche Symbole sind wirklich public vs. implementation detail?
3. Sinnvolle Hierarchie: `kb.framework.search`, `kb.framework.embeddings`, etc.?
4. Backward Compatibility bei Export-Änderungen?

**Deliverable:** Vorschlag für strukturierte `__all__` + ggf. Sub-package-Reorg.

---

## Phase F — Hardcoded Pfade

**Ziel:** Keine Magic Strings/Pfade im Code.

**Zu prüfen:**
1. `_get_default_chroma_path()` — zeigt noch auf falschen Pfad (`Path.home()/.openclaw/kb/chroma_db`)?
2. Fallback-Pfade in `chroma_integration.py`, `hybrid_search.py` — konsistent?
3. Gibt es weitere hardcoded paths (DB, logs, config)?
4. Konfiguration über Umgebungsvariablen / KBConfig?

**Deliverable:** Liste aller hardcoded Pfade + Korrekturvorschläge.

---

## Phase G — Error Handling

**Ziel:** Konsistente Exception-Hierarchie und Graceful Degradation.

**Zu prüfen:**
1. Custom Exception-Klassen definiert? (`KBException`, `ChromaConnectionError`, etc.)
2. Konsistente Verwendung von `try/except` vs. `Result`-Typen?
3. Graceful Degradation wenn ChromaDB nicht verfügbar?
4. Graceful Degradation wenn DB nicht verfügbar (SQLite fallback?)?
5. Logging bei Fehlern — informativ genug?

**Deliverable:** Exception-Hierarchie-Dokument + Fehlende graceful-paths.

---

## Checkpoints

- [ ] Phase A abgeschlossen
- [ ] Phase B abgeschlossen
- [ ] Phase C abgeschlossen
- [ ] Phase D abgeschlossen
- [ ] Phase E abgeschlossen
- [ ] Phase F abgeschlossen
- [ ] Phase G abgeschlossen

---

## Rollback-Plan

- Branch: `audit/{timestamp}` oder `audit/main`
- Backup: Vor Audit-Zustand in `ARCHIV/` oder Git stash
- Keine destruktiven Änderungen während des Audits — nur Analysen und Empfehlungen

---

## Verification

Nach jeder Phase:
- [ ] Syntax-Check: `python3 -m py_compile kb/framework/{phase_file}.py`
- [ ] Keine neuen Import-Errors
- [ ] Dokumentation in AUDIT_PLAN.md aktualisiert

---

## Output

- Dieser Plan: `AUDIT_PLAN.md` (dieser Datei)
- Phase-Ergebnisse: Als Kommentare in jeder Phase oben dokumentieren
- Finale Zusammenfassung: `AUDIT_REPORT.md` (nach Abschluss aller Phasen)