# AUDIT Phase A — Code-Duplikate in `kb/framework/`

**Datum:** 2026-04-26  
**Prüfer:** Sir Stern 🔍  
**Scope:** Alle 6 Prüfpunkte aus dem AUDIT_PLAN

---

## Zusammenfassung

| # | Prüfpunkt | Bewertung | Schwere |
|---|-----------|-----------|---------|
| 1 | `_get_default_chroma_path()` | **3× definiert** (2× chroma_integration + 1× chroma_plugin) | 🟡 Mittel |
| 2 | `ChromaIntegration` vs `ChromaIntegrationV2` | **V2 ist tot** — nirgendwo referenziert außer in sich selbst | 🟠 Hoch |
| 3 | `get_chroma()` vs `ChromaIntegration.get_instance()` | **Kein Duplikat** — Wrapper delegiert 1:1 | 🟢 OK |
| 4 | `providers/chroma_provider.py` vs `chroma_integration.py` | **Kein Duplikat** — Provider ist dünner Adapter | 🟢 OK |
| 5 | `providers/fts5_provider.py` vs `fts5_setup.py` | **Verschiedene Verantwortungen** — aber Overlap bei `_parse_keywords` & `check_fts5_available` | 🟡 Mittel |
| 6 | `search_providers.py` vs `providers/` | **Kein Duplikat** — Interface vs. Implementierung (korrekte Trennung) | 🟢 OK |

**Bonus-Funde:**
- `SearchResult` existiert 2×: `hybrid_search.SearchResult` (reich) vs `search_providers.SearchResult` (minimal)
- `_parse_keywords()` identisch in `chroma_provider.py` + `fts5_provider.py`
- `embed_text_v2` / `embed_batch_v2` auf `ChromaIntegration` — tot, parallel zu `ChromaIntegrationV2`

---

## Detail-Analyse

### 1. `_get_default_chroma_path()` — 3× definiert

**Dateien:**
- `chroma_integration.py` Zeile 41–43 (mit KBConfig)
- `chroma_integration.py` Zeile 47–49 (Fallback bei ImportError)
- `chroma_plugin.py` Zeile 36–38 (nur KBConfig-Variante, kein Fallback)

**Was ist doppelt?**
Identische Logik: `str(KBConfig.get_instance().chroma_path)`.  
`chroma_integration.py` hat zusätzlich einen ImportError-Fallback, `chroma_plugin.py` nicht — das ist inkonsistent und ein potenzieller Bug (chroma_plugin crasht wenn KBConfig fehlt).

**Vorschlag:** **Merge** — einmalig definieren, z.B. in `utils.py` (existiert bereits) oder als Teil von `KBConfig`. Beide Module importieren dann von dort.

**Begründung:** DRY-Prinzip; Fallback-Logik sollte an genau einer Stelle gepflegt werden. Aktuell riskiert man, dass ein Fix an einer Stelle vergessen wird.

---

### 2. `ChromaIntegration` vs `ChromaIntegrationV2` — V2 ist ungenutzt

**Dateien:**
- `chroma_integration.py` Zeile 56–508: `ChromaIntegration` (Singleton, aktiv)
- `chroma_integration.py` Zeile 510–568: `ChromaIntegrationV2` (Nicht-Singleton, **0 externe Referenzen**)

**Zusätzlich auf `ChromaIntegration` selbst:**
- `embed_text_v2()` (Z. 212) — **0 externe Aufrufe**
- `embed_batch_v2()` (Z. 240) — **0 externe Aufrufe**
- `switch_to_v2_model()` (Z. 268) — **0 externe Aufrufe**
- `sections_collection_v2` (Z. 358) — **0 externe Aufrufe**
- `alternative_model_name` (Z. 207) — nur intern von v2-Methoden genutzt

**Was ist doppelt?**
V2-Infrastruktur (Klasse + 4 Methoden + 1 Property auf der Basisklasse) existiert vollständig, wird aber **von nichts verwendet**. `ChromaIntegrationV2` erbt alles von `ChromaIntegration`, überschreibt nur `__new__` (nicht-Singleton), `__init__` (anderes Modell), und `client` (Client-Sharing).

**Vorschlag:** **Deprecate** — V2-Code in einen Branch/Tag auslagern oder mit `@deprecated` markieren. Entfernen in nächstem Major-Release.

**Begründung:** Totcode belastet Verständnis, Testing und Refactoring. ~60 Zeilen Klasse + ~60 Zeilen v2-Methoden auf `ChromaIntegration` = ~120 Zeilen unnötige Komplexität. Falls V2-Modell später gebraucht wird, kann es re-implementiert werden (idealerweise als Konfigurationsparameter statt separater Klasse).

---

### 3. `get_chroma()` vs `ChromaIntegration.get_instance()` — kein echtes Duplikat

**Dateien:**
- `chroma_integration.py` Zeile 574–581: `get_chroma(**kwargs)` → delegiert an `ChromaIntegration.get_instance(**kwargs)`

**Was ist doppelt?**
Nicht wirklich — `get_chroma()` ist ein **1:1-Wrapper**, dokumentiert als "canonical entry point". Es gibt keine separate Instanz, keinen eigenen State.

**Vorschlag:** **Keep separate** — Convenience-Funktion ist idiomatisch Python.

**Begründung:** `get_chroma()` ist der öffentliche API-Einstiegspunkt; `get_instance()` ist das Klassen-Interface. Beide zu haben ist Standard (wie `logging.getLogger()` vs `Logger.getLogger()`). Kein Wartungsaufwand.

---

### 4. `providers/chroma_provider.py` vs `chroma_integration.py` — Adapter, kein Duplikat

**Dateien:**
- `providers/chroma_provider.py` (160 Zeilen): Dünner Adapter, implementiert `SemanticSearchProvider`-Protocol
- `chroma_integration.py` (680 Zeilen): Core-Singleton mit Client, Embedding, Collections

**Was ist doppelt?**
`ChromaSemanticProvider._ensure_chroma()` importiert und nutzt `get_chroma()` — es baut auf `ChromaIntegration` auf, dupliziert nichts. Die `search()`-Methode konvertiert ChromaDB-Rohdaten in `SearchResult`-Objekte — das ist Adapter-Logik, keine Duplikation.

**Vorschlag:** **Keep separate** — korrekte Schichtenarchitektur.

**Begründung:** Provider-Schicht entkoppelt `HybridSearch` von ChromaDB-Internas. Das ist genau das, was man will.

---

### 5. `providers/fts5_provider.py` vs `fts5_setup.py` — verschiedene Jobs, aber Overlap

**Dateien:**
- `fts5_setup.py` (228 Zeilen): DDL-Setup — `CREATE VIRTUAL TABLE`, Trigger, Rebuild, Stats
- `providers/fts5_provider.py` (283 Zeilen): DML-Query — BM25/LIKE-Suche, implementiert `KeywordSearchProvider`

**Was ist doppelt?**
1. **`_parse_keywords()`** — identisch in `chroma_provider.py:151` und `fts5_provider.py:268`. Dasselbe JSON/CSV-Parsing.
2. **`check_fts5_available()`** in `fts5_setup.py` (Z. 84–99) vs `is_available()` in `fts5_provider.py` (Z. 50–91) — prüfen beide FTS5-Verfügbarkeit, aber mit unterschiedlicher Granularität (Setup: kann FTS5 erstellen? / Provider: existiert die Tabelle für Queries?).

**Vorschlag:**
- `_parse_keywords()` → **Merge** in `utils.py` (existiert bereits mit `build_embedding_text`)
- `check_fts5_available()` vs `is_available()` → **Keep separate** (verschiedene Fragen, verschiedene Antworten)

**Begründung:** `_parse_keywords` ist reine Utility-Logik, gehört nicht in Provider. Die Availability-Checks sind konzeptionell verschieden (Kann-Frage vs. Ist-Frage).

---

### 6. `search_providers.py` vs `providers/` — Interface vs. Implementierung

**Dateien:**
- `search_providers.py` (128 Zeilen): Protocols (`SemanticSearchProvider`, `KeywordSearchProvider`) + `SearchResult`-Dataclass
- `providers/` (2 Dateien): `ChromaSemanticProvider`, `FTS5KeywordProvider` + Factory-Funktionen

**Was ist doppelt?**
Nichts — das ist eine **korrekte Schichtenarchitektur**: abstrakte Interfaces + konkrete Implementierungen. `providers/__init__.py` exportiert sauber.

**Vorschlag:** **Keep separate** — Architektur ist stimmig.

**Begründung:** Protocol-basierte Entkopplung ermöglicht zukünftige Provider (z.B. TF-IDF, Weaviate) ohne HybridSearch-Änderung.

---

## Bonus-Funde

### B1. `SearchResult` — zwei Dataclasses

| Attribut | `hybrid_search.SearchResult` | `search_providers.SearchResult` |
|----------|------------------------------|--------------------------------|
| section_id | ✅ | ✅ |
| content | ❌ | ✅ |
| score | ❌ (combined_score) | ✅ |
| source | ❌ | ✅ |
| file_id, file_path | ✅ | ✅ |
| semantic_score, keyword_score | ✅ | ❌ |
| combined_score | ✅ | ❌ (→ score) |
| section_level, content_full | ✅ | ❌ |

**Vorschlag:** **Keep separate** (vorerst) — verschiedene Abstraktionsebenen. `hybrid_search.SearchResult` ist ein "reiches" kombiniertes Ergebnis; `search_providers.SearchResult` ist ein einfaches Provider-Output. Falls `hybrid_search` auf Provider-Interface migriert wird, könnte man vereinheitlichen.

### B2. `_parse_keywords()` — identisch in beiden Providern

**Dateien:** `providers/chroma_provider.py:151`, `providers/fts5_provider.py:268`

**Vorschlag:** **Merge** nach `utils.py`.

**Begründung:** Copy-Paste-Code. Gleiche Logik, gleiche Edge-Cases. Zentral pflegen.

### B3. V2-Methoden auf `ChromaIntegration` selbst

`embed_text_v2`, `embed_batch_v2`, `switch_to_v2_model`, `sections_collection_v2`, `alternative_model_name` — **5 Member auf der Basisklasse** die nur V2-Funktionalität bereitstellen, aber **0 externe Aufrufer** haben.

**Vorschlag:** Zusammen mit `ChromaIntegrationV2` **deprecate**.

---

## Empfohlene Aktionen (Priorität)

| Prio | Aktion | Aufwand |
|------|--------|---------|
| 1 | `ChromaIntegrationV2` + v2-Methoden deprecaten/entfernen | Klein (~120 Zeilen) |
| 2 | `_get_default_chroma_path()` zentralisieren (→ utils.py) | Klein (~10 Zeilen) |
| 3 | `_parse_keywords()` zentralisieren (→ utils.py) | Klein (~10 Zeilen) |
| 4 | Fallback-Logik in `chroma_plugin.py` konsolidieren | Trivial |

**Keine Handlung nötig:** Punkte 3, 4, 6 (korrekte Architektur)