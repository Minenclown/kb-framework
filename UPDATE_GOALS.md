# KB Framework - Fix Plan & Roadmap

**Version:** 1.0  
**Created:** 2026-04-13  
**Status:** Active

---

## 🔥 Critical (Immediate)

| # | Feature | Problem | Solution | Effort |
|---|---------|---------|----------|--------|
| 1 | **Multi-Format Indexing** | PDFs, TXTs, DOCs are ignored – only .md is searchable | Auto-conversion: Non-MD → MD copy with metadata header | ~4h |
| 2 | Hybrid Search Module | `kb.library.knowledge_base.hybrid_search` is missing in current state | Re-integrate module from Phase 3 Recovery | ~2h |

### 🔥 Multi-Format Indexing (Detail)

**Requirements:**
- PDFs, TXT, DOCX → Automatically as `.md` copy in `library/content/[category]/`
- Header with metadata:
  ```markdown
  ---
  source: original.pdf
  type: pdf
  indexed_at: 2026-04-13
  extracted_by: [pymupdf/easyocr]
  ---
  
  [Extracted Text...]
  ```

**Benefits:**
- Agents can read PDF content directly (native MD)
- Full-text Search across all formats
- No duplicates (hash check)

---

## 🟡 High (Next Week)

| # | Feature | Problem | Solution | Effort |
|---|---------|---------|----------|--------|
| 3 | OCR Config | Tesseract is default (CPU), EasyOCR optional (GPU) | Config flag for OCR engine (`tesseract` vs `easyocr`) | ~1h |
| 4 | ChromaDB Warmup Script | Cold Start 3.2s on first embedding | Automatic model preloading on boot | ~30min |
| 5 | Delta Indexing | Re-indexing of all files on any change | Timestamp check: only modified files | ~2h |

---

## 🟢 Medium (Sprint)

| # | Feature | Problem | Solution | Effort |
|---|---------|---------|----------|--------|
| 6 | Backup/Restore CLI | `kb backup` and `kb restore` are missing | Wrapper for DB + ChromaDB export/import | ~2h |
| 7 | Test Coverage | 5/8 tests failed on review | Adjust tests to current schema | ~3h |
| 8 | Auto-Updater Testing | `kb update` never tested live | Create test release on GitHub | ~1h |
| 9 | **Gemma LLM Integration** | No local LLM for query enhancement / summarization | Optional `kb llm` command using Google Gemma 4B (multimodal, local) | ~4h |

---

## 🔵 Low (Backlog)

| # | Feature | Problem | Solution | Effort |
|---|---------|---------|----------|--------|
| 9 | Web Interface | Only CLI available | Minimal web UI for search/status | ~8h |
| 10 | Plugin System | No extensibility | Hook system for custom indexers | ~4h |
| 11 | Internationalization | Only German/English | i18n for all output strings | ~3h |

---

## 🚧 In Progress

| # | Feature | Status | Owner |
|---|---------|--------|-------|
| - | - | - | - |

---

## ✅ Done (Last 7 Days)

| # | Feature | Date | Notes |
|---|---------|------|-------|
| 1 | KB Migration | 2026-04-13 | Legacy → New structure, 868 files migrated |
| 2 | Auto-Updater Fix | 2026-04-13 | Repo corrected to `Minenclown/kb-framework` |
| 3 | README Update | 2026-04-13 | Installation path, structure, quick start (CLI) |
| 4 | FK Constraints | 2026-04-13 | 181 orphaned records deleted, PRAGMA foreign_keys = ON |

---

## 🔴 Design Principles

**Offline-First:** The KB runs exclusively locally – no cloud dependencies, no API keys, no internet required.

---

## Priority Logic

```
🔥 Critical = Blocks production usage
🟡 High = Important for UX/Performance
🟢 Medium = Nice-to-have, stabilizes
🔵 Low = Visionary/Future
```

**Decision criteria:**
- Impact on users × Effort = Priority
- Blockers before optimizations
- Stability before features

---

## Next Step

**Recommended:** 🔥 #1 Multi-Format Indexing

**Reasoning:**
- Currently 258 PDFs in the healthcare sector are ignored
- Agents cannot read important medical data
- High impact, medium effort

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

*Last Updated: 2026-04-13*  
*Next Review: 2026-04-20*
