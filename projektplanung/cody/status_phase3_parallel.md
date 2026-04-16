# Cody Phase 3 Status: Generator Parallel Support

**Datum:** 2026-04-16
**Status:** ✅ Abgeschlossen

## Übersicht

Implementierung von `parallel_mode` Support in den Generatoren für LLM Model Source Switch. Die Engine-Infrastruktur (Registry, Factory, Config) war bereits vorhanden - die Generatoren mussten aktualisiert werden, um sie zu nutzen.

## Implementierte Dateien

### 1. `kb/biblio/generator/parallel_mixin.py` (NEU)
- **ParallelStrategy** Enum: `PRIMARY_FIRST`, `AGGREGATE`, `COMPARE`
- **DiffType** Enum: `ADDED`, `REMOVED`, `CHANGED`, `UNCHANGED`
- **DiffEntry** / **DiffResult** Dataclasses für strukturierte Vergleiche
- **ParallelResult** Dataclass für Ergebnis-Metadaten
- **ParallelMixin** Klasse mit:
  - `diff_essences(a, b)` - Vergleicht zwei Essenz-Dicts feldweise
  - `merge_essences(a, b, diff_result)` - Vereinigt komplementäre Essenzen
  - `diff_reports(a, b)` - Unified-Diff für Report-Strings
  - `merge_reports(a, b, diff_result)` - Sektionsbasierte Report-Zusammenführung
  - `_generate_with_strategy()` - Dispatch basierend auf Strategie
  - `_generate_primary_only()` / `_generate_primary_first()` / `_generate_aggregate()` / `_generate_compare()`
  - `_should_use_parallel()` / `_get_parallel_engines()` / `__init_parallel__()`

### 2. `kb/biblio/generator/essence_generator.py` (AKTUALISIERT)
- **EssenzGenerator erbt nun ParallelMixin**
- `__init__` akzeptiert `registry: Optional[EngineRegistry]` und ruft `__init_parallel__` auf
- **Neue Methode `generate_essence_parallel()`**:
  - `primary_first`: Primärer Engine, Fallback auf Sekundär
  - `aggregate`: Beide generieren, Ergebnisse werden gemergt (union)
  - `compare`: Beide generieren, Diff-View + Merge wenn komplementär
- **Neue Hilfsmethoden**:
  - `_process_primary_first_result()` - Verarbeitet primary_first Ergebnisse
  - `_process_aggregate_result()` - Verarbeitet aggregate Ergebnisse
  - `_process_compare_result()` - Verarbeitet compare Ergebnisse mit Diff + Merge
- **`generate_essences_batch()` aktualisiert**:
  - Neuer Parameter `parallel_strategy`
  - Nutzt `generate_essence_parallel()` wenn parallel mode aktiv
- Importiert `EngineRegistry`, `ParallelMixin`, `ParallelStrategy`, etc.

### 3. `kb/biblio/generator/report_generator.py` (AKTUALISIERT)
- **ReportGenerator erbt nun ParallelMixin**
- `__init__` akzeptiert `registry: Optional[EngineRegistry]` und ruft `__init_parallel__` auf
- **Neue Methode `generate_report_parallel()`**:
  - `primary_first`: Primärer Engine, Fallback auf Sekundär
  - `aggregate`: Beide generieren, Reports werden kombiniert
  - `compare`: Beide generieren, Diff + Merge wenn komplementär
  - Speichert `diff.json` bei compare-Strategie
- **Neue Hilfsmethoden**:
  - `_aggregate_report_responses()` - Kombiniert zwei Report-Strings
  - `_compare_report_responses()` - Diff + Merge für Reports

### 4. `kb/biblio/generator/__init__.py` (AKTUALISIERT)
- Exportiert neue Klassen: `ParallelMixin`, `ParallelStrategy`, `ParallelResult`, `DiffResult`, `DiffEntry`, `DiffType`

### 5. `kb/biblio/generator/test_parallel.py` (NEU)
- 13 standalone Tests für Diff/Merge-Logik
- Keine Engine-Imports (isoliert testbar)
- Alle Tests bestanden ✅

## Strategien im Detail

### primary_first
- Primärer Engine wird zuerst aufgerufen
- Bei Fehler (Exception oder erfolglose Response) → Sekundärer Engine
- Kein Merge nötig - nur ein Ergebnis wird verwendet

### aggregate
- Beide Engines parallel (asyncio.gather)
- Beide Ergebnisse werden geparst und gemergt
- Listenfelder: Union (Deduplizierung)
- String-Felder: Längere/beide Antworten bevorzugt
- Relationships: Union

### compare
- Beide Engines parallel
- Diff-Vergleich der Ergebnisse
- Wenn komplementär (keine Konflikte) → Merge
- Wenn Konflikte → Primäres Ergebnis verwenden
- Diff-Metadaten werden als `diff.json` gespeichert

## Diff-View + Merge Logik

### Essenz-Diff
- **String-Felder** (summary): Direkter Vergleich, CHANGED = Konflikt
- **Listen-Felder** (key_points, connections, etc.): Item-Level Vergleich
  - only_a → REMOVED (komplementär)
  - only_b → ADDED (komplementär)
  - common → UNCHANGED
- **Relationships**: Strukturiertes Set-basiertes Comparison

### Report-Diff
- Unified-Diff (difflib) für line-by-line Vergleich
- Zeilen-basiert: +N/-M Zeilen geändert

### Merge-Regeln
- **can_merge**: Wahr wenn `!has_conflicts && complement_count > 0`
- **Essenz-Merge**: Union für Listen, längeren Summary bevorzugen (>1.2x)
- **Report-Merge**: Sektionsbasiert, gemeinsame Sektionen bekommen "Ergänzungen" Label

## Bekannte Einschränkungen

- Engine-Imports hängen beim Testen (Ollama-Abhängigkeit blockiert) - Logik-Tests laufen isoliert
- `generate_essence_parallel()` und `generate_report_parallel()` konnten nicht mit echten Mock-Engines getestet werden (Import-Problem)
- Die `__init_parallel__` / `_should_use_parallel()` Logik nutzt die existierende `EngineRegistry` und `LLMConfig`

## Nächste Schritte

- Integrationstests mit laufendem Ollama-Server
- CLI-Integration für `--parallel` Flag
- Performance-Tests: Latenz-Overhead bei parallel_mode