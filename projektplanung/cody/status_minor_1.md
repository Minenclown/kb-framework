# Status Minor Fix 1: sync_chroma.py TODO

**Date:** 2026-04-16
**Issue:** EmbeddingPipeline wird nicht verwendet (TODO placeholder)
**File:** `kb/scripts/sync_chroma.py`

## Fix
- Replaced TODO placeholder in `sync_execute()` with actual `EmbeddingPipeline.run_full()` call
- Added `EmbeddingPipeline` import
- Pipeline receives `db_path` and `chroma_path` from `KBConfig.get_instance()`

## Before
```python
# TODO: Use EmbeddingPipeline to embed missing sections
print(f"   (Here EmbeddingPipeline.embed_sections() would be called)")
```

## After
```python
pipeline = EmbeddingPipeline(
    db_path=str(config.db_path),
    chroma_path=str(config.chroma_path)
)
result = pipeline.run_full(limit=len(missing))
print(f"   ✅ {result.get('processed', 0)} sections embedded")
if result.get('failed', 0) > 0:
    print(f"   ⚠️  {result['failed']} sections failed")
```

## Verification
- ✅ Syntax valid (py_compile)
- ✅ AST parse OK
- ✅ No TODO remaining
- ✅ EmbeddingPipeline imported