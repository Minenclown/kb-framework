# Phase 1 Fix: kb/knowledge_base/ Redirect erstellen

**Problem:** Imports like `from kb.knowledge_base.hybrid_search import ...` fail because `kb/knowledge_base/` does not exist. The actual code is in `src/library/`.

**Lösung:** Create redirect modules in `kb/knowledge_base/` that import and re-export from `src/library/`.

## Schritte

### 1. Create directory and __init__.py
```bash
mkdir -p ~/projects/kb-framework/kb/knowledge_base
```

### 2. kb/knowledge_base/__init__.py
```python
"""kb.knowledge_base redirect to src.library"""
import sys
from pathlib import Path

# Ensure src.library is importable
_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# Re-export all from src.library
from src.library import ChromaManager, EmbeddingPipeline, HybridSearcher

__all__ = ["ChromaManager", "EmbeddingPipeline", "HybridSearcher"]
```

### 3. kb/knowledge_base/chroma_integration.py
```python
"""Redirect to src.library.chroma_integration"""
import sys
from pathlib import Path

_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.library.chroma_integration import ChromaManager, ChromaCollectionConfig

__all__ = ["ChromaManager", "ChromaCollectionConfig"]
```

### 4. kb/knowledge_base/hybrid_search.py
```python
"""Redirect to src.library.hybrid_search"""
import sys
from pathlib import Path

_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.library.hybrid_search import HybridSearch, SearchResult

__all__ = ["HybridSearch", "SearchResult"]
```

### 5. kb/knowledge_base/embedding_pipeline.py
```python
"""Redirect to src.library.embedding_pipeline"""
import sys
from pathlib import Path

_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.library.embedding_pipeline import EmbeddingPipeline

__all__ = ["EmbeddingPipeline"]
```

### 6. kb/knowledge_base/fts5_setup.py
```python
"""Redirect to src.library.fts5_setup"""
import sys
from pathlib import Path

_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.library.fts5_setup import FTS5Setup, ensure_fts5_enabled

__all__ = ["FTS5Setup", "ensure_fts5_enabled"]
```

## Verification

```bash
cd ~/projects/kb-framework

python3 -c "
from kb.knowledge_base.hybrid_search import HybridSearch, SearchResult
from kb.knowledge_base.chroma_integration import ChromaManager
from kb.knowledge_base.embedding_pipeline import EmbeddingPipeline
from kb.knowledge_base.fts5_setup import FTS5Setup
print('✓ All kb.knowledge_base imports work')
"
```

## Rollback

```bash
rm -rf ~/projects/kb-framework/kb/knowledge_base/
```

## Checkliste

- [ ] `kb/knowledge_base/` Verzeichnis erstellt
- [ ] `__init__.py` erstellt
- [ ] `chroma_integration.py` erstellt
- [ ] `hybrid_search.py` erstellt
- [ ] `embedding_pipeline.py` erstellt
- [ ] `fts5_setup.py` erstellt
- [ ] Alle Imports verifiziert