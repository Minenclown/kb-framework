# Status Minor Fix 3: Redundanter embed_texts() Wrapper

**Date:** 2026-04-16
**Issue:** `embed_texts()` in sync.py is a redundant wrapper that just calls `embed_batch()`
**File:** `kb/commands/sync.py`

## Fix
- Removed `embed_texts()` function definition (lines 26-39)
- Replaced 2 call sites (`_cmd_file` and `_embed_missing_sections`) with direct `embed_batch()` calls
- `embed_batch` was already imported from `src.library.chroma_integration`

## Before
```python
def embed_texts(texts: list, model_name: str = "all-MiniLM-L6-v2") -> List[List[float]]:
    """Embed texts using EmbeddingPipeline from src.library."""
    return embed_batch(texts)

# Call sites:
embeddings = embed_texts(texts)  # 2x
```

## After
```python
# No wrapper function

# Call sites:
embeddings = embed_batch(texts)  # 2x
```

## Verification
- ✅ Syntax valid (py_compile)
- ✅ AST parse OK
- ✅ No `def embed_texts` remaining
- ✅ `embed_batch(texts)` used 2 times