# Obsidian Integration - Test Plan Phase 5

**Status:** bereit für Sir Stern
**Bestehende Tests:** 119 Unit Tests ✓ (alle grün)

---

## 1. Test-Kategorien

### 1.1 Unit Tests (bestehend)
- **Stand:** 119 Tests, alle PASSED
- **Covered:** `parser.py`, `resolver.py`, `indexer.py`, `vault.py`
- **Location:** `tests/test_obsidian_*.py`
- **Status:** ✅ REFACTOR if needed — keine Änderungen an APIs

### 1.2 Integration Tests (neu)
**Ziel:** Vault als Ganzes testen, Komponenten-Interaktion

| Test-ID | Name | Beschreibung |
|---------|------|-------------|
| INT-001 | `test_vault_lifecycle` | create → index → search → find_backlinks |
| INT-002 | `test_vault_index_invalidation` | index → modify → invalidate → reindex |
| INT-003 | `test_vault_search_with_real_files` | Real-World Markdown-Dateien parsen |
| INT-004 | `test_backlinks_across_folders` | Links zwischen verschachtelten Ordnern |
| INT-005 | `test_graph_completeness` | Graph enthält alle Dateien und Links |

### 1.3 End-to-End Tests (neu)
**Ziel:** Vollständiger User-Workflow

| Test-ID | Name | Beschreibung |
|---------|------|-------------|
| E2E-001 | `test_full_vault_workflow` | 10 Dateien, komplexe Links → alle Features |
| E2E-002 | `test_search_relevance_ranking` | Suchergebnisse korrekt sortiert |
| E2E-003 | `test_backlinks_accuracy` | 100% der erkannten Links korrekt |
| E2E-004 | `test_graph_structure` | nodes + edges korrekt für komplexen Vault |

---

## 2. Test-Szenarien

### Szenario A: Vault mit Beispiel-Dateien erstellen

```
test_vault/
├── README.md
├── knowledge/
│   ├── AI.md
│   └── ml/
│       ├── neural-networks.md
│       └── transformers.md
└── projects/
    └── agent.md
```

**Test-Files erstellen:**
```python
def create_test_vault():
    vault_dir = tempfile.mkdtemp()
    # ... create structure above
    return vault_dir
```

**Success-Kriterien:**
- [ ] 6 Dateien werden erkannt
- [ ] Alle Dateien lesbar
- [ ] Pfade korrekt aufgelöst

### Szenario B: Backlinks zwischen Dateien testen

**Verbindungen:**
```
AI.md → neural-networks.md (via [[neural networks]])
AI.md → transformers.md (via [[Transformers]])
neural-networks.md → AI.md (via [[AI]])
transformers.md → AI.md (via [[AI]])
agent.md → AI.md (via [[AI]])
```

**Success-Kriterien:**
- [ ] `find_backlinks("AI.md")` → 3 Quellen
- [ ] `find_backlinks("neural-networks.md")` → 1 Quelle
- [ ] Context zeigt Link-Umgebung (≥20 Zeichen)
- [ ] `link_text` und `link_target` korrekt

### Szenario C: Suchfunktion testen

**Queries:**
| Query | Erwartet | Match-Type |
|-------|----------|------------|
| "AI" | AI.md, neural-networks.md, transformers.md | name |
| "neural" | neural-networks.md | content |
| "machine learning" | ml/*.md | content |
| "title:AI" | AI.md (frontmatter) | frontmatter |

**Success-Kriterien:**
- [ ] Ergebnisse sortiert nach Score (absteigend)
- [ ] `match_type` korrekt gesetzt
- [ ] Context zeigt Treffer (≥50 Zeichen)
- [ ] Limit wird respektiert

### Szenario D: Graph-Generierung testen

**Erwartete Struktur:**
```python
graph = vault.get_graph()

# nodes: 6 Dateien
assert len(graph['nodes']) == 6

# edges: 5 Links (双向 = 2 edges)
assert len(graph['edges']) == 5

# Jeder Node hat: path, name, links (outgoing count)
for node in graph['nodes']:
    assert 'path' in node
    assert 'name' in node
    assert 'links' in node  # int
```

---

## 3. Erwartete Ergebnisse

### Success-Kriterien

| Kategorie | Kriterium | Metrik |
|-----------|-----------|--------|
| **Unit Tests** | Alle bestehen | 119/119 ✓ |
| **Integration Tests** | Alle bestehen | 5/5 ✓ |
| **E2E Tests** | Alle bestehen | 4/4 ✓ |
| **Backlinks** | Precision | 100% |
| **Backlinks** | Recall | ≥95% |
| **Search** | Relevance | Top-3 relevant |
| **Graph** | Vollständigkeit | 100% |

### Definition "Bestanden"

```
✅ ALLES GRÜN
├── 119 Unit Tests (bestehend)
├── 5 Integration Tests (neu)
└── 4 E2E Tests (neu)

✅ KEINE REGRESSIONEN
├── Suchergebnisse bleiben konsistent
├── Backlink-Qualität bleibt gleich
└── Performance: <2s für Vault mit 100 Dateien

✅ DOKUMENTATION
├── tests/test_obsidian_integration.py (neu)
├── tests/test_obsidian_e2e.py (neu)
└── TEST_RESULTS.md (Output)
```

---

## 4. Implementierungs-Reihenfolge

1. **INT-001 bis INT-005** — Integration Tests (Sir Stern)
2. **E2E-001 bis E2E-004** — E2E Tests (Sir Stern)
3. **Test-Report erstellen** — `TEST_RESULTS.md`

**Zeit-Schätzung:** 15-25 Minuten

---

## 5. Test-Location

```
kb-framework/
├── tests/
│   ├── test_obsidian_integration.py  # NEU
│   └── test_obsidian_e2e.py          # NEU
└── OBSIDIAN_TEST_PLAN.md             # dieses Dokument
```

---

## 6. Beispiel-Test-Template

```python
class TestObsidianIntegration(unittest.TestCase):
    """Integration Tests für ObsidianVault."""

    def setUp(self):
        self.vault_dir = create_test_vault()

    def test_vault_lifecycle(self):
        """Full lifecycle: create → index → search → find_backlinks."""
        vault = ObsidianVault(self.vault_dir)

        # 1. Index
        vault.index()

        # 2. Search
        results = vault.search("AI")
        assert len(results) > 0

        # 3. Find backlinks
        backlinks = vault.find_backlinks("knowledge/AI.md")
        assert len(backlinks) >= 2

    # ... more tests
```